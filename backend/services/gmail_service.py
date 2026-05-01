import os
import sys
import json
from pathlib import Path

# Add the backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

import re
import email.utils
from datetime import datetime
from services.gmail_auth import get_gmail_service
from services.ai_service import process_email
from database import get_db

def parse_sender(from_header: str):
    """Parses 'Name <email@example.com>' into ('Name', 'email@example.com')"""
    if not from_header:
        return "", ""
    
    match = re.match(r'(.*)<(.*)>', from_header)
    if match:
        name = match.group(1).strip().strip('"')
        email = match.group(2).strip()
        return name, email
    
    return "", from_header.strip()

def fetch_recent_emails(days_back=7):
    """Fetches emails from the last N days and parses them."""
    service = get_gmail_service()
    query = f"newer_than:{days_back}d"
    
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    emails = []
    
    for msg_meta in messages:
        msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute()
        
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        header_data = {h['name'].lower(): h['value'] for h in headers}
        
        from_header = header_data.get('from', '')
        sender_name, sender_email = parse_sender(from_header)
        
        date_str = header_data.get('date', '')
        received_at = ""
        if date_str:
            try:
                dt = email.utils.parsedate_to_datetime(date_str)
                received_at = dt.isoformat()
            except Exception:
                received_at = date_str
        
        email_item = {
            "gmail_message_id": msg['id'],
            "thread_id": msg['threadId'],
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": header_data.get('subject', ''),
            "body_snippet": msg.get('snippet', ''),
            "received_at": received_at
        }
        emails.append(email_item)
        
    return emails

def map_status(classification_type):
    """Maps AI classification to application status and priority."""
    # Higher number = higher priority/later stage
    mapping = {
        "confirmation": ("applied", 1),
        "recruiter": ("screening", 2),
        "interview": ("interviewing", 3),
        "offer": ("offered", 4),
        "rejection": ("rejected", 10), # Rejection always wins
        "followup": (None, 0)
    }
    return mapping.get(classification_type, (None, 0))

def fetch_and_store_emails(days_back=7):
    """
    Fetches recent emails, stores them, and processes them with AI.
    """
    raw_emails = fetch_recent_emails(days_back)
    db = get_db()
    cursor = db.cursor()
    
    stats = {
        "fetched": len(raw_emails),
        "new": 0,
        "skipped": 0,
        "auto_classified": 0,
        "queued_for_review": 0
    }
    
    for email_data in raw_emails:
        # Check for deduplication
        cursor.execute("SELECT 1 FROM emails WHERE gmail_message_id = ?", (email_data['gmail_message_id'],))
        if cursor.fetchone():
            stats["skipped"] += 1
            continue
            
        # 1. Insert new email
        cursor.execute("""
            INSERT INTO emails (
                gmail_message_id, thread_id, sender_name, sender_email, 
                subject, body_snippet, received_at, processed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            email_data['gmail_message_id'], email_data['thread_id'],
            email_data['sender_name'], email_data['sender_email'],
            email_data['subject'], email_data['body_snippet'],
            email_data['received_at']
        ))
        email_id = cursor.lastrowid
        stats["new"] += 1
        
        # 2. Process with AI
        ai_result = process_email(
            email_data['sender_name'], email_data['sender_email'],
            email_data['subject'], email_data['body_snippet']
        )
        
        status = ai_result["status"]
        classification = ai_result["classification"]
        raw_json_str = json.dumps(ai_result)

        if status == "skip":
            cursor.execute("""
                UPDATE emails SET processed = 1, classification_type = 'unrelated'
                WHERE id = ?
            """, (email_id,))
            
        elif status == "auto":
            details = ai_result["details"]
            cursor.execute("""
                UPDATE emails SET 
                    classification_type = ?, confidence_score = ?, 
                    raw_json = ?, processed = 1
                WHERE id = ?
            """, (
                classification["type"], classification["confidence"],
                raw_json_str, email_id
            ))
            
            # Application Logic
            company = details.get("company", "").strip()
            role = details.get("role", "").strip()
            
            if company and role:
                # Check for existing application (case-insensitive)
                cursor.execute("""
                    SELECT id, status FROM applications 
                    WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?)
                """, (company, role))
                existing_app = cursor.fetchone()
                
                new_status, new_priority = map_status(classification["type"])
                
                if not existing_app:
                    # INSERT new application
                    cursor.execute("""
                        INSERT INTO applications (
                            company, role, status, date_applied, source, 
                            last_activity, next_action
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        company, role, new_status or "applied",
                        details.get("application_date"), details.get("ats_platform"),
                        email_data['received_at'], details.get("next_action")
                    ))
                    app_id = cursor.lastrowid
                else:
                    # UPDATE existing application
                    app_id = existing_app["id"]
                    current_status = existing_app["status"]
                    
                    # Logic: only update status if new status is higher priority
                    _, current_priority = map_status(current_status) if current_status else (None, 0)
                    
                    if new_status and new_priority > current_priority:
                        cursor.execute("""
                            UPDATE applications SET 
                                status = ?, last_activity = ?, next_action = ?
                            WHERE id = ?
                        """, (new_status, email_data['received_at'], details.get("next_action"), app_id))
                    else:
                        cursor.execute("""
                            UPDATE applications SET last_activity = ?
                            WHERE id = ?
                        """, (email_data['received_at'], app_id))

                # Link email to application
                cursor.execute("UPDATE emails SET application_id = ? WHERE id = ?", (app_id, email_id))
            
            stats["auto_classified"] += 1

        elif status == "review":
            cursor.execute("""
                UPDATE emails SET 
                    confidence_score = ?, raw_json = ?, processed = 0
                WHERE id = ?
            """, (classification["confidence"], raw_json_str, email_id))
            
            cursor.execute("""
                INSERT INTO review_queue (
                    email_id, suggested_type, suggested_company, suggested_role, 
                    confidence_score, reasoning
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email_id, classification["type"], classification["company"],
                classification["role"], classification["confidence"], classification["reasoning"]
            ))
            stats["queued_for_review"] += 1
            
    db.commit()
    db.close()
    return stats

if __name__ == '__main__':
    try:
        print("Starting fetch and store process...")
        results = fetch_and_store_emails(days_back=1)
        print(f"Results: {json.dumps(results, indent=2)}")
    except Exception as e:
        print(f"An error occurred: {e}")
