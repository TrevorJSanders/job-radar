from fastapi import APIRouter
from services.gmail_service import fetch_and_store_emails

router = APIRouter(prefix="/emails", tags=["emails"])

@router.get("/raw")
async def get_raw_emails():
    """
    Diagnostic endpoint to manually trigger Gmail fetch and storage.
    """
    summary = fetch_and_store_emails(days_back=7)
    return summary
