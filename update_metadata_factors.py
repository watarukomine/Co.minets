import requests
import json
import os
from datetime import datetime

# --- Configuration ---
PROJECT_ID = "cominet-8799b"
DATABASE_ID = "cominets"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DATABASE_ID}/documents"
PROXIES = {"http": "http://proxy03.tns.ne.jp:8080", "https": "http://proxy03.tns.ne.jp:8080"}
SERVICE_ACCOUNT_FILE = "service-account.json"

def get_access_token():
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/datastore'])
        creds.refresh(Request())
        return creds.token
    except: return None

def update_metadata():
    token = get_access_token()
    if not token: return
    
    url = f"{BASE_URL}/dashboard_metadata/current"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Define factor types we just uploaded
    factor_types = ["総整備台数", "車検台数", "法点台数", "一般整備台数", "板金塗装台数", "新商品台数"]
    
    # We use updateMask to only update/add factorTypes field
    body = {
        "fields": {
            "factorTypes": {"arrayValue": {"values": [{"stringValue": t} for t in factor_types]}}
        }
    }
    
    try:
        res = requests.patch(f"{url}?updateMask.fieldPaths=factorTypes", json=body, headers=headers, proxies=PROXIES, timeout=30)
        if res.status_code == 200:
            print("[OK] Metadata updated with factor types.")
        else:
            print(f"[ERROR] {res.status_code} {res.text}")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    update_metadata()
