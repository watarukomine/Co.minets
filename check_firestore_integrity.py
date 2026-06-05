import requests
import json
import os

# ==========================================
# サービスアカウントからトークン取得 (簡略版)
# ==========================================
def get_token():
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    creds = service_account.Credentials.from_service_account_file(
        'service-account.json', 
        scopes=['https://www.googleapis.com/auth/datastore']
    )
    creds.refresh(Request())
    return creds.token

def check_doc():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    project_id = "cominet-8799b"
    db_id = "cominets"
    # UIが取得しているドキュメントを模倣
    # 例: 売上_a-00総販_100_総売上 (神奈川支社)
    doc_id = "%E5%A3%B2%E4%B8%8A_a-00%E7%B7%8F%E8%B2%A9_100_%E7%B7%8F%E5%A3%B2%E4%B8%8A"
    branch = "%E7%A5%9E%E5%A5%88%E5%B7%9D%E6%94%AF%E7%A4%BE"
    
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_data/{doc_id}/branches/{branch}"
    
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        fields = data.get('fields', {})
        c = fields.get('c', {}).get('arrayValue', {}).get('values', [])
        c_ext = fields.get('c_ext', {}).get('arrayValue', {}).get('values', [])
        
        print(f"Document: {doc_id} ({branch})")
        print(f"c length: {len(c)}")
        print(f"c_ext length: {len(c_ext)}")
        
        # メタデータのタイムラインもチェック
        meta_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_metadata/current"
        mres = requests.get(meta_url, headers=headers)
        if mres.status_code == 200:
            mdata = mres.json()
            timeline = mdata.get('fields', {}).get('timeline', {}).get('arrayValue', {}).get('values', [])
            print(f"Timeline length: {len(timeline)}")
            if timeline:
                print(f"Timeline Start: {timeline[0].get('stringValue')}")
                print(f"Timeline End: {timeline[-1].get('stringValue')}")
    else:
        print(f"Error: {res.status_code} {res.text}")

if __name__ == "__main__":
    check_doc()
