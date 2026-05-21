import os
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
PROJECT_ID = "cominet-8799b"

def get_access_token():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, 
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    creds.refresh(Request())
    return creds.token

def test():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/releases"
    res = requests.get(url, headers=headers)
    print("Releases:", json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test()
