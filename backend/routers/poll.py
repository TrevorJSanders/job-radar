from fastapi import APIRouter
from datetime import datetime
from services.gmail_service import fetch_and_store_emails

router = APIRouter(prefix="/poll", tags=["poll"])

# In-memory state for the last poll
poll_state = {
    "last_polled": None,
    "last_result": None
}

@router.post("")
async def trigger_poll():
    """
    Manually trigger a Gmail poll to fetch and process new emails.
    """
    result = fetch_and_store_emails(days_back=3) # Defaulting to 3 days for standard poll
    
    poll_state["last_polled"] = datetime.now().isoformat()
    poll_state["last_result"] = result
    
    return result

@router.get("/status")
async def get_poll_status():
    """
    Returns the last time a poll was run and its results.
    """
    return poll_state
