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

# Proxy configuration
PROXIES = {
    "http": "http://proxy03.tns.ne.jp:8080",
    "https": "http://proxy03.tns.ne.jp:8080"
}

# Input directory
INPUT_DIR = "サービス入庫"
SERVICE_ACCOUNT_FILE = "service-account.json"

# Branch Code Mapping
BRANCH_MAP = {
    "85371": "神奈川支社",
    "85341": "埼玉支社",
    "85351": "千葉支社",
    "85311": "東京統括支社",
    "85321": "茨城支社",
    "85331": "栃木支社",
    "85361": "群馬支社",
    "85381": "山梨支社",
    "85391": "長野支社",
    "85211": "宮城支社",
    "85121": "北海道統括支社",
    "85221": "岩手支社",
    "85231": "宮城支社",
    "85261": "福島支社",
}

def get_access_token():
    """サービスアカウントからアクセストークンを取得"""
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=['https://www.googleapis.com/auth/datastore']
        )
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"[ERROR] トークン取得失敗: {e}")
        return None

def to_firestore_value(val):
    if isinstance(val, (int, float)):
        return {"doubleValue": float(val)}
    if isinstance(val, str):
        return {"stringValue": val}
    if isinstance(val, list):
        return {"arrayValue": {"values": [to_firestore_value(v) for v in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(v) for k, v in val.items()}}}
    return {"nullValue": None}

def upload_to_firestore(collection, doc_id, data, token):
    url = f"{BASE_URL}/{collection}/{doc_id}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    fields = {k: to_firestore_value(v) for k, v in data.items()}
    body = {"fields": fields}
    
    try:
        res = requests.patch(url, json=body, headers=headers, proxies=PROXIES, timeout=30)
        if res.status_code not in [200, 201]:
            print(f"  [ERROR] Failed to upload {doc_id}: {res.status_code} {res.text}")
            return False
        return True
    except Exception as e:
        print(f"  [ERROR] Exception during upload: {e}")
        return False

def process_service_files():
    token = get_access_token()
    if not token:
        print("[CRITICAL] Could not get access token. Check service-account.json")
        return

    files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    print(f"[START] Found {len(files)} files in {INPUT_DIR}")
    
    all_factor_types = set()
    
    for file_path in files:
        filename = os.path.basename(file_path)
        match = re.search(r"\((\d{6})\)", filename)
        if not match: continue
        
        month_str = match.group(1)
        month_label = f"{month_str[:4]}-{month_str[4:]}"
        
        print(f"[PROCESS] {filename} (Month: {month_label})")
        
        try:
            try:
                df = pd.read_csv(file_path, encoding="shift-jis")
            except:
                df = pd.read_csv(file_path, encoding="utf-8")
                
            df.columns = [c.strip().replace('"', '') for c in df.columns]
            branches = df["管轄支社コード"].unique()
            
            for b_code in branches:
                b_code_str = str(int(b_code))
                b_name = BRANCH_MAP.get(b_code_str, f"Code_{b_code_str}")
                branch_data = df[df["管轄支社コード"] == b_code]
                
                doc_id = f"{b_name}_{month_label}".replace("/", "-")
                
                summary = {}
                dealers = {}
                
                for _, row in branch_data.iterrows():
                    d_code = str(row["販売店コード"])
                    d_name = str(row["販売店名"])
                    cat = str(row["台数区分"])
                    val = float(row["当年"]) if pd.notnull(row["当年"]) else 0
                    all_factor_types.add(cat)
                    
                    summary[cat] = summary.get(cat, 0) + val
                    if d_code not in dealers:
                        dealers[d_code] = {"n": d_name}
                    dealers[d_code][cat] = val
                
                payload = {
                    "m": month_label,
                    "b": b_name,
                    "s": summary,
                    "d": dealers,
                    "updatedAt": datetime.now().isoformat()
                }
                
                success = upload_to_firestore("dashboard_factors", doc_id, payload, token)
                if success:
                    print(f"  [OK] Uploaded {b_name} for {month_label}")

        except Exception as e:
            print(f"  [ERROR] Failed to process {filename}: {e}")

if __name__ == "__main__":
    process_service_files()
