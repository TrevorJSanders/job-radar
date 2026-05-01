import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """
    Returns an authenticated Gmail API service object.
    Handles token loading, refreshing, and initial OAuth flow.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # Looking for token.json in the /backend folder as requested
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_path = os.path.join(backend_dir, 'token.json')
    credentials_path = os.path.join(backend_dir, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            try:
                # Try to run a local server which automatically opens the browser
                creds = flow.run_local_server(port=0)
            except Exception:
                # Fallback for WSL/headless where a browser can't be opened automatically
                print("\nNo browser detected or could not open one.")
                print("Please copy and paste the following URL into your browser to authorize:")
                creds = flow.run_local_server(port=0, open_browser=False)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

if __name__ == '__main__':
    try:
        service = get_gmail_service()
        # Call the Gmail API to verify it works
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
        else:
            print('Gmail authentication successful')
            print('Labels:')
            for label in labels:
                print(f"- {label['name']}")
    except Exception as e:
        print(f"An error occurred: {e}")
