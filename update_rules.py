import os
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
PROJECT_ID = "cominet-8799b"

def get_access_token():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"Token error: {e}")
        return None

def update_firestore_rules():
    token = get_access_token()
    if not token:
        print("Failed to get token.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    rules_content = """rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}"""

    # 1. Create a Ruleset
    print("Creating new ruleset...")
    create_url = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/rulesets"
    ruleset_payload = {
        "source": {
            "files": [
                {
                    "name": "firestore.rules",
                    "content": rules_content
                }
            ]
        }
    }
    
    res = requests.post(create_url, headers=headers, json=ruleset_payload)
    if res.status_code != 200:
        print(f"Failed to create ruleset: {res.text}")
        return
    
    ruleset_name = res.json().get("name")
    print(f"Created ruleset: {ruleset_name}")

    # 2. Update the Release to point to the new Ruleset
    print("Applying ruleset to Firestore...")
    
    release_name = f"projects/{PROJECT_ID}/releases/cloud.firestore"
    update_url = f"https://firebaserules.googleapis.com/v1/{release_name}"
    
    # Correct REST API request format for UpdateReleaseRequest
    payload = {
        "release": {
            "name": release_name,
            "rulesetName": ruleset_name
        },
        "updateMask": "rulesetName"
    }
    
    res = requests.patch(update_url, headers=headers, json=payload)
    if res.status_code == 200:
        print("Successfully updated Firestore rules!")
        print("Please reload the dashboard page in your browser.")
        return
        
    print(f"PATCH failed: {res.text}")
    print("Attempting to recreate release...")
    create_release_url = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/releases"
    res_post = requests.post(create_release_url, headers=headers, json=payload["release"])
    if res_post.status_code == 200:
        print("Successfully created and applied Firestore rules!")
        print("Please reload the dashboard page in your browser.")
    else:
        print(f"Failed: {res_post.text}")

if __name__ == "__main__":
    update_firestore_rules()
