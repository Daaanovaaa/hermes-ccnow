import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests

def main():
    # Load environment variables from /root/.hermes/.env
    env_path = '/root/.hermes/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print(f"Warning: {env_path} not found")

    # Get LinkedIn access token
    linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not linkedin_token:
        raise ValueError("LINKEDIN_ACCESS_TOKEN not found in environment")

    # Get Facebook access token and page ID
    facebook_access_token = os.getenv('META_CCN_PAGE_ACCESS_TOKEN') or os.getenv('CCN_TUTIENDA_PAGE_ACCESS_TOKEN')
    facebook_page_id = os.getenv('CCN_FACEBOOK_PAGE_ID')
    
    if not facebook_access_token:
        raise ValueError("Facebook access token not found in environment (check META_CCN_PAGE_ACCESS_TOKEN or CCN_TUTIENDA_PAGE_ACCESS_TOKEN)")
    if not facebook_page_id:
        raise ValueError("Facebook page ID not found in environment (check CCN_FACEBOOK_PAGE_ID)")

    # Google Docs API setup
    # Use the pre-authenticated token for dominalo.con.cristo@gmail.com
    token_path = '/root/.hermes/google_token.json'
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"Google token file not found at {token_path}")
    
    try:
        with open(token_path) as f:
            token_data = json.load(f)
        
        # Create credentials
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/documents.readonly'])
        )
        
        # Try to refresh if needed
        if not creds.valid:
            print("Refreshing credentials...")
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            
    except Exception as e:
        print(f"Failed to load/refresh Google credentials: {e}")
        raise

    # Build the Docs service
    docs_service = build('docs', 'v1', credentials=creds)

    # Document ID
    doc_id = '193XJkhdkx0lEVPb_2oK8jK4rxUC7vtcAVBbBIVuHBQQ'

    # Fetch the document
    print("Fetching document...")
    doc = docs_service.documents().get(documentId=doc_id).execute()

    # Extract text content
    def extract_text_from_structural_elements(elements):
        text = ''
        for element in elements:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text += elem['textRun'].get('content', '')
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        text += extract_text_from_structural_elements(cell.get('content', []))
            elif 'tableOfContents' in element:
                text += extract_text_from_structural_elements(element['tableOfContents'].get('content', []))
        return text

    doc_content = doc.get('body', {}).get('content', [])
    text = extract_text_from_structural_elements(doc_content)
    print(f"Extracted text length: {len(text)}")
    print(f"Extracted text: {text[:100]}..." if len(text) > 100 else f"Extracted text: {text}")

    # Post to LinkedIn
    print("\n--- Posting to LinkedIn ---")
    linkedin_url = 'https://api.linkedin.com/v2/ugcPosts'
    headers = {
        'Authorization': f'Bearer {linkedin_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    linkedin_payload = {
        "author": "urn:li:person:41q6-gkeGG",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    linkedin_response = requests.post(linkedin_url, headers=headers, data=json.dumps(linkedin_payload))
    if linkedin_response.status_code == 201:
        print("Successfully posted to LinkedIn")
        print(f"Post ID: {linkedin_response.json().get('id')}")
    else:
        print(f"Failed to post to LinkedIn: {linkedin_response.status_code}")
        print(linkedin_response.text)

    # Post to Facebook
    print("\n--- Posting to Facebook ---")
    facebook_url = f'https://graph.facebook.com/v19.0/{facebook_page_id}/feed'
    facebook_payload = {
        'message': text,
        'access_token': facebook_access_token
    }
    
    facebook_response = requests.post(facebook_url, data=facebook_payload)
    if facebook_response.status_code == 200:
        print("Successfully posted to Facebook")
        print(f"Post ID: {facebook_response.json().get('id')}")
    else:
        print(f"Failed to post to Facebook: {facebook_response.status_code}")
        print(facebook_response.text)

if __name__ == '__main__':
    main()