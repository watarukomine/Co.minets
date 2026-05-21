
import os
import json
import firebase_admin
from firebase_admin import credentials, storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")

def diagnose():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("Error: service-account.json not found")
        return

    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        
        # Load project ID from service account
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            sa_info = json.load(f)
            project_id = sa_info.get('project_id')
            print(f"--- 診断開始 ---")
            print(f"サービスアカウントのプロジェクトID: {project_id}")

        from google.cloud import storage as gcs
        client = gcs.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
        
        print("\n1. このサービスアカウントで見える全バケットをリストアップします...")
        try:
            buckets = list(client.list_buckets())
            if not buckets:
                print(" -> バケットが1つも見つかりませんでした。")
            else:
                for b in buckets:
                    print(f" -> 見つかったバケット: {b.name}")
        except Exception as e:
            print(f" -> バケットリストの取得に失敗しました: {e}")
                
        print("\n2. よくあるバケット名のパターンを確認します...")
        patterns = [
            f"{project_id}.appspot.com",
            f"{project_id}.firebasestorage.app",
            project_id,
            f"{project_id}-storage"
        ]
        
        for p in patterns:
            try:
                b = client.get_bucket(p)
                print(f" [OK] '{p}' は有効なバケット名です。")
            except Exception as e:
                # 404なら「存在しない」、403なら「権限なし」
                status = "不明なエラー"
                if "404" in str(e): status = "存在しません (404)"
                elif "403" in str(e): status = "権限がありません (403)"
                print(f" [NG] '{p}' -> {status}")

        print(f"\n--- 診断終了 ---")

    except Exception as e:
        print(f"致命的なエラー: {e}")

if __name__ == "__main__":
    diagnose()
