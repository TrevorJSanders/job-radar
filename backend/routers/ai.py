from fastapi import APIRouter, HTTPException
from services.ai_service import generate_cover_letter
from config import RESUME_TEXT
from models import CoverLetterRequest, CoverLetterResponse
from database import get_db

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/cover-letter", response_model=CoverLetterResponse)
async def create_cover_letter(request: CoverLetterRequest):
    """
    Generates a tailored cover letter and optionally stores it in the application notes.
    """
    result = generate_cover_letter(
        job_description=request.job_description,
        company=request.company,
        role=request.role,
        resume_text=RESUME_TEXT
    )
    
    if request.application_id:
        db = get_db()
        cursor = db.cursor()
        
        # Check if application exists
        cursor.execute("SELECT notes FROM applications WHERE id = ?", (request.application_id,))
        row = cursor.fetchone()
        
        if row:
            current_notes = row["notes"] or ""
            new_note = f"\n\n--- GENERATED COVER LETTER ({request.role} at {request.company}) ---\n\n{result['cover_letter']}"
            updated_notes = current_notes + new_note
            
            cursor.execute(
                "UPDATE applications SET notes = ? WHERE id = ?",
                (updated_notes, request.application_id)
            )
            db.commit()
            
        db.close()
        
    return result
