import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from database import get_db
from services.ai_service import process_email
from services.gmail_service import map_status

def reprocess_all(clear_data=False):
    db = get_db()
    cursor = db.cursor()

    if clear_data:
        print("Clearing applications, review queue, and resetting emails...")
        cursor.execute("DELETE FROM review_queue")
        cursor.execute("DELETE FROM applications")
        cursor.execute("UPDATE emails SET application_id = NULL, classification_type = NULL, confidence_score = NULL, raw_json = NULL, processed = 0")
        db.commit()

    # Fetch all unprocessed emails
    cursor.execute("SELECT * FROM emails WHERE processed = 0")
    emails = cursor.fetchall()
    
    print(f"Reprocessing {len(emails)} emails...")
    
    stats = {
        "processed": 0,
        "auto_classified": 0,
        "queued_for_review": 0,
        "skipped": 0
    }

    for email in emails:
        print(f"  [{stats['processed']+1}/{len(emails)}] Processing: {email['subject'][:50]}...")
        
        ai_result = process_email(
            email['sender_name'], email['sender_email'],
            email['subject'], email['body_snippet']
        )
        
        # Add a delay to stay within 5 RPM (60s / 5 = 12s)
        import time
        time.sleep(12)
        
        status = ai_result["status"]
        classification = ai_result["classification"]
        raw_json_str = json.dumps(ai_result)
        email_id = email['id']

        if status == "skip":
            cursor.execute("UPDATE emails SET processed = 1, classification_type = 'unrelated' WHERE id = ?", (email_id,))
            stats["skipped"] += 1
            
        elif status == "auto":
            details = ai_result["details"]
            cursor.execute("""
                UPDATE emails SET 
                    classification_type = ?, confidence_score = ?, 
                    raw_json = ?, processed = 1
                WHERE id = ?
            """, (classification["type"], classification["confidence"], raw_json_str, email_id))
            
            company = details.get("company", "").strip()
            role = details.get("role", "").strip()
            
            if company and role:
                cursor.execute("""
                    SELECT id, status FROM applications 
                    WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?)
                """, (company, role))
                existing_app = cursor.fetchone()
                
                new_status, new_priority = map_status(classification["type"])
                
                if not existing_app:
                    cursor.execute("""
                        INSERT INTO applications (
                            company, role, status, date_applied, source, 
                            last_activity, next_action
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        company, role, new_status or "applied",
                        details.get("application_date"), details.get("ats_platform"),
                        email['received_at'], details.get("next_action")
                    ))
                    app_id = cursor.lastrowid
                else:
                    app_id = existing_app["id"]
                    current_status = existing_app["status"]
                    _, current_priority = map_status(current_status) if current_status else (None, 0)
                    
                    if new_status and new_priority > current_priority:
                        cursor.execute("""
                            UPDATE applications SET status = ?, last_activity = ?, next_action = ?
                            WHERE id = ?
                        """, (new_status, email['received_at'], details.get("next_action"), app_id))
                    else:
                        cursor.execute("UPDATE applications SET last_activity = ? WHERE id = ?", (email['received_at'], app_id))

                cursor.execute("UPDATE emails SET application_id = ? WHERE id = ?", (app_id, email_id))
            stats["auto_classified"] += 1

        elif status == "review":
            cursor.execute("UPDATE emails SET confidence_score = ?, raw_json = ?, processed = 0 WHERE id = ?", 
                          (classification["confidence"], raw_json_str, email_id))
            cursor.execute("""
                INSERT INTO review_queue (
                    email_id, suggested_type, suggested_company, suggested_role, 
                    confidence_score, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (email_id, classification["type"], classification["company"], 
                  classification["role"], classification["confidence"], classification["reasoning"]))
            stats["queued_for_review"] += 1
        
        stats["processed"] += 1
        db.commit() # Commit after each to see progress

    db.close()
    return stats

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reprocess emails through the AI pipeline.")
    parser.add_argument("--clear", action="store_true", help="Clear all applications and reset all emails before processing.")
    args = parser.parse_args()

    print("--- AI Reprocessing Utility ---")
    results = reprocess_all(clear_data=args.clear)
    print(f"\nFinished!\n{json.dumps(results, indent=2)}")
