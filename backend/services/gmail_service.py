import os
import sys
from pathlib import Path

# Add the backend directory to sys.path so 'services' and 'database' can be found
# when running this file directly.
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

import base64
import re
import email.utils
from datetime import datetime
from googleapiclient.discovery import Resource
from services.gmail_auth import get_gmail_service
from database import get_db

def parse_sender(from_header: str):
    """Parses 'Name <email@example.com>' into ('Name', 'email@example.com')"""
    if not from_header:
        return "", ""
    
    # Match "Name <email@example.com>"
    match = re.match(r'(.*)<(.*)>', from_header)
    if match:
        name = match.group(1).strip().strip('"')
        email = match.group(2).strip()
        return name, email
    
    # Fallback for just "email@example.com"
    return "", from_header.strip()

def fetch_recent_emails(days_back=7):
    """
    Fetches emails from the last N days and parses them into a list of dictionaries.
    """
    service = get_gmail_service()
    query = f"newer_than:{days_back}d"
    
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    emails = []
    
    for msg_meta in messages:
        msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute()
        
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        header_data = {h['name'].lower(): h['value'] for h in headers}
        
        from_header = header_data.get('from', '')
        sender_name, sender_email = parse_sender(from_header)
        
        # Parse date header to ISO string
        date_str = header_data.get('date', '')
        received_at = ""
        if date_str:
            try:
                dt = email.utils.parsedate_to_datetime(date_str)
                received_at = dt.isoformat()
            except Exception:
                received_at = date_str # Fallback to raw string if parsing fails
        
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

def fetch_and_store_emails(days_back=7):
    """
    Fetches recent emails and stores new ones in the database.
    Deduplicates by gmail_message_id.
    """
    raw_emails = fetch_recent_emails(days_back)
    db = get_db()
    cursor = db.cursor()
    
    stats = {
        "fetched": len(raw_emails),
        "new": 0,
        "skipped": 0
    }
    
    for email in raw_emails:
        # Check for deduplication
        cursor.execute("SELECT 1 FROM emails WHERE gmail_message_id = ?", (email['gmail_message_id'],))
        if cursor.fetchone():
            stats["skipped"] += 1
            continue
            
        # Insert new email
        cursor.execute("""
            INSERT INTO emails (
                gmail_message_id, thread_id, sender_name, sender_email, 
                subject, body_snippet, received_at, processed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            email['gmail_message_id'],
            email['thread_id'],
            email['sender_name'],
            email['sender_email'],
            email['subject'],
            email['body_snippet'],
            email['received_at']
        ))
        stats["new"] += 1
        
    db.commit()
    db.close()
    return stats

if __name__ == '__main__':
    import json
    
    try:
        print(f"Fetching emails from the last 3 days...")
        recent_emails = fetch_recent_emails(days_back=3)
        print(f"Found {len(recent_emails)} emails.\n")
        
        # Pretty print first 3
        for i, email in enumerate(recent_emails[:3]):
            print(f"--- Email {i+1} ---")
            print(json.dumps(email, indent=2))
            print()
            
    except Exception as e:
        print(f"An error occurred: {e}")
