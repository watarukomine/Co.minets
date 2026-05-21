import urllib.request
import json

project_id = "cominet-8799b"
db_id = "cominets"

def check():
    print("--- 調査開始 ---")
    meta_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_metadata/current"
    req = urllib.request.Request(meta_url)
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            fields = data.get("fields", {})
            print("[Metadata] Keys:", list(fields.keys()))
            if "classes" in fields:
                print("[Metadata] classes length:", len(fields["classes"].get("arrayValue", {}).get("values", [])))
            else:
                print("[Metadata] classes MISSING!")
    except Exception as e:
        print("[Metadata] error:", e)

    doc_id = "売上_a-00総販_100_総売上"
    from urllib.parse import quote
    branch = quote("85371 神奈川支社")
    doc_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_data/{quote(doc_id)}/branches/{branch}"
    print("\n[Data] Fetching URL:", doc_url)
    req = urllib.request.Request(doc_url)
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            c_vals = data.get("fields", {}).get("c", {}).get("arrayValue", {}).get("values", [])
            print(f"[Data] Found data! c length = {len(c_vals)}")
            # Show a few items
            print("[Data] First 5 c items:", [v for v in c_vals[:5]])
    except urllib.error.HTTPError as e:
        print(f"[Data] HTTP Error: {e.code} {e.reason}")
    except Exception as e:
        print(f"[Data] Error: {e}")

check()
