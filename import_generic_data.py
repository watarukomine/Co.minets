import os
import pandas as pd
import requests
import json
import glob
import re
from datetime import datetime

# --- Configuration ---
PROJECT_ID = "cominet-8799b"
DATABASE_ID = "cominets"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DATABASE_ID}/documents"
PROXIES = {"http": "http://proxy03.tns.ne.jp:8080", "https": "http://proxy03.tns.ne.jp:8080"}
SERVICE_ACCOUNT_FILE = "service-account.json"

# Target directory for various data
INPUT_DIR = "custom_data"
if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)

# Branch Code Mapping
BRANCH_MAP = {
    "85371": "神奈川支社", "85341": "埼玉支社", "85351": "千葉支社",
    "85311": "東京統括支社", "85121": "北海道統括支社", "85231": "宮城支社",
}

def get_access_token():
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/datastore'])
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"[ERROR] Token error: {e}")
        return None

def to_firestore_value(val):
    if isinstance(val, (int, float)): return {"doubleValue": float(val)}
    if isinstance(val, str): return {"stringValue": val}
    if isinstance(val, dict): return {"mapValue": {"fields": {k: to_firestore_value(v) for k, v in val.items()}}}
    return {"nullValue": None}

def upload_doc(collection, doc_id, data, token):
    url = f"{BASE_URL}/{collection}/{doc_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    fields = {k: to_firestore_value(v) for k, v in data.items()}
    try:
        res = requests.patch(url, json={"fields": fields}, headers=headers, proxies=PROXIES, timeout=30)
        return res.status_code in [200, 201]
    except: return False

def process_generic_files():
    token = get_access_token()
    if not token: return
    
    files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    if not files:
        print(f"[INFO] No files found in {INPUT_DIR}. Please put your CSV files there.")
        return

    all_found_factors = set()
    
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"[PROCESS] {filename}")
        
        # 1. Identify Month from filename or content
        match = re.search(r"(\d{6})", filename)
        month_label = f"{match.group(1)[:4]}-{match.group(1)[4:]}" if match else "2026-04" # Fallback
        
        try:
            df = pd.read_csv(file_path, encoding="shift-jis")
        except:
            df = pd.read_csv(file_path, encoding="utf-8")
        
        # Clean column names
        df.columns = [c.strip().replace('"', '') for c in df.columns]
        
        # 2. Identify key columns automatically
        branch_col = next((c for c in df.columns if "支社コード" in c or "管轄" in c), None)
        dealer_col = next((c for c in df.columns if "販売店コード" in c), None)
        value_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64'] and c not in [branch_col, dealer_col]]
        
        if not branch_col:
            print(f"  [SKIP] Could not identify branch column in {filename}")
            continue

        # 3. Aggregate and Upload
        for b_code in df[branch_col].unique():
            b_name = BRANCH_MAP.get(str(int(b_code)), f"Code_{int(b_code)}")
            branch_df = df[df[branch_col] == b_code]
            
            summary = {}
            for col in value_cols:
                summary[col] = float(branch_df[col].sum())
                all_found_factors.add(col)
                
            doc_id = f"{b_name}_{month_label}".replace("/", "-")
            # We merge with existing data in Firestore if needed, 
            # but for simplicity we'll just PATCH the whole summary for now.
            # In a real app, we'd fetch the doc first.
            
            payload = {
                "m": month_label,
                "b": b_name,
                "s": summary,
                "updatedAt": datetime.now().isoformat()
            }
            if upload_doc("dashboard_factors", doc_id, payload, token):
                print(f"  [OK] Uploaded {b_name} - {len(value_cols)} factors found.")

    # 4. Update Metadata with new factor list
    if all_found_factors:
        # Fetch current factor types first
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/dashboard_metadata/current", headers=headers, proxies=PROXIES)
        if res.status_code == 200:
            meta = from_firestore_value(res.json()["fields"])
            current_factors = set(meta.get("factorTypes", []))
            new_factors = list(current_factors | all_found_factors)
            
            body = {"fields": {"factorTypes": {"arrayValue": {"values": [{"stringValue": f} for f in new_factors]}}}}
            requests.patch(f"{BASE_URL}/dashboard_metadata/current?updateMask.fieldPaths=factorTypes", json=body, headers=headers, proxies=PROXIES)
            print(f"[METADATA] Updated. Total factors: {len(new_factors)}")

def from_firestore_value(fields):
    # Minimal converter for metadata update
    res = {}
    for k, v in fields.items():
        if "stringValue" in v: res[k] = v["stringValue"]
        elif "arrayValue" in v: res[k] = [x.get("stringValue") for x in v["arrayValue"].get("values", [])]
    return res

if __name__ == "__main__":
    process_generic_files()
