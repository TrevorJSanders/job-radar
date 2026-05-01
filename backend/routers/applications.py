from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["applications"])

@router.get("", response_model=List[ApplicationResponse])
async def get_applications(status: Optional[str] = Query(None)):
    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT * FROM applications"
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    
    query += " ORDER BY last_activity DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    db.close()
    
    return [dict(row) for row in rows]

@router.get("/{id}")
async def get_application(id: int):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (id,))
    row = cursor.fetchone()
    
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    application = dict(row)
    
    cursor.execute("SELECT * FROM emails WHERE application_id = ?", (id,))
    emails = cursor.fetchall()
    db.close()
    
    application["emails"] = [dict(e) for e in emails]
    return application

@router.post("", response_model=ApplicationResponse)
async def create_application(app_data: ApplicationCreate):
    db = get_db()
    cursor = db.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO applications (company, role, status, date_applied, source, fit_score, notes, next_action, last_activity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_data.company,
        app_data.role,
        app_data.status,
        app_data.date_applied,
        app_data.source,
        app_data.fit_score,
        app_data.notes,
        app_data.next_action,
        now,
        now
    ))
    
    new_id = cursor.lastrowid
    db.commit()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    db.close()
    
    return dict(row)

@router.patch("/{id}", response_model=ApplicationResponse)
async def update_application(id: int, app_data: ApplicationUpdate):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = app_data.dict(exclude_unset=True)
    
    now = datetime.now().isoformat()
    update_data["last_activity"] = now
    
    fields = ", ".join([f"{k} = ?" for k in update_data.keys()])
    values = list(update_data.values())
    values.append(id)
    
    cursor.execute(f"UPDATE applications SET {fields} WHERE id = ?", values)
    db.commit()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (id,))
    row = cursor.fetchone()
    db.close()
    
    return dict(row)

@router.delete("/{id}")
async def delete_application(id: int):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM applications WHERE id = ?", (id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update linked emails
    cursor.execute("UPDATE emails SET application_id = NULL WHERE application_id = ?", (id,))
    
    # Delete application
    cursor.execute("DELETE FROM applications WHERE id = ?", (id,))
    
    db.commit()
    db.close()
    
    return {"deleted": True}
