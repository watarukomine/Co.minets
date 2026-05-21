import requests
import json

project_id = "cominet-8799b"
db_id = "cominets"

doc_id = "売上_a-00総販_100_総売上"
branch = "85371 神奈川支社"
url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_data/{doc_id}/branches/{branch}"

res = requests.get(url)
with open("verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"Status: {res.status_code}\n")
    if res.ok:
        data = res.json()
        fields = data.get("fields", {})
        c = fields.get("c", {}).get("arrayValue", {}).get("values", [])
        f.write(f"c length: {len(c)}\n")
    else:
        f.write(res.text + "\n")
