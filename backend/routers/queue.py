from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import QueueItemResponse, QueueResolve

router = APIRouter(prefix="/queue", tags=["queue"])

@router.get("")
async def get_queue():
    db = get_db()
    cursor = db.cursor()
    
    query = """
    SELECT q.*, e.sender_name, e.sender_email, e.subject, e.body_snippet
    FROM review_queue q
    JOIN emails e ON q.email_id = e.id
    WHERE q.status = 'pending'
    ORDER BY q.created_at ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    items = [dict(row) for row in rows]
    db.close()
    
    return {"count": len(items), "items": items}

@router.get("/count")
async def get_queue_count():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM review_queue WHERE status = 'pending'")
    count = cursor.fetchone()[0]
    db.close()
    
    return {"pending": count}

@router.post("/{id}/resolve")
async def resolve_queue_item(id: int, resolve_data: QueueResolve):
    db = get_db()
    cursor = db.cursor()
    
    # Check if queue item exists
    cursor.execute("SELECT * FROM review_queue WHERE id = ?", (id,))
    queue_item = cursor.fetchone()
    if not queue_item:
        db.close()
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    queue_item = dict(queue_item)
    email_id = queue_item["email_id"]
    now = datetime.now().isoformat()
    
    if resolve_data.action == "reject":
        # Update email
        cursor.execute("""
            UPDATE emails SET processed = 1, classification_type = 'unrelated' 
            WHERE id = ?
        """, (email_id,))
        
        # Update queue
        cursor.execute("""
            UPDATE review_queue SET status = 'rejected', resolved_at = ? 
            WHERE id = ?
        """, (now, id))
        
    elif resolve_data.action in ["confirm", "correct"]:
        if resolve_data.action == "confirm":
            target_type = queue_item["suggested_type"]
            target_company = queue_item["suggested_company"]
            target_role = queue_item["suggested_role"]
            status = "confirmed"
        else:
            target_type = resolve_data.corrected_type or queue_item["suggested_type"]
            target_company = resolve_data.corrected_company or queue_item["suggested_company"]
            target_role = resolve_data.corrected_role or queue_item["suggested_role"]
            status = "corrected"
            
        # Find or create application
        cursor.execute("""
            SELECT id FROM applications 
            WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?)
        """, (target_company, target_role))
        app_row = cursor.fetchone()
        
        if app_row:
            application_id = app_row[0]
            cursor.execute("""
                UPDATE applications SET last_activity = ? WHERE id = ?
            """, (now, application_id))
        else:
            cursor.execute("""
                INSERT INTO applications (company, role, status, last_activity, created_at, source)
                VALUES (?, ?, 'applied', ?, ?, 'gmail')
            """, (target_company, target_role, now, now))
            application_id = cursor.lastrowid
            
        # Update email
        cursor.execute("""
            UPDATE emails SET processed = 1, classification_type = ?, application_id = ?
            WHERE id = ?
        """, (target_type, application_id, email_id))
        
        # Update queue
        cursor.execute("""
            UPDATE review_queue SET status = ?, resolved_at = ? 
            WHERE id = ?
        """, (status, now, id))
        
    else:
        db.close()
        raise HTTPException(status_code=400, detail="Invalid action")
        
    db.commit()
    db.close()
    
    return {"resolved": True, "action": resolve_data.action}
