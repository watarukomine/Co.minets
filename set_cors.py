
import os
import json
from google.cloud import storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")

def set_cors():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("Error: service-account.json not found")
        return

    try:
        client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
        # ユーザーが確認したバケット名を使用
        bucket_name = "cominet-8799b.firebasestorage.app"
        bucket = client.get_bucket(bucket_name)

        # CORS設定（全てのオリジンからのGETを許可）
        # 本来はセキュリティ上オリジンを制限すべきですが、まずは疎通を優先
        bucket.cors = [
            {
                "origin": ["*"],
                "responseHeader": ["Content-Type"],
                "method": ["GET"],
                "maxAgeSeconds": 3600
            }
        ]
        bucket.patch()

        print(f"✅ バケット {bucket_name} の CORS 設定を更新しました。")
        print("\n--- 現在の CORS 設定 ---")
        print(bucket.cors)
        print("\n設定が反映されるまで 1〜2 分ほどかかる場合があります。")
        print("ブラウザのキャッシュをクリア（Ctrl+F5）してリロードしてください。")

    except Exception as e:
        print(f"❌ CORS設定エラー: {e}")
        if "403" in str(e):
            print("権限不足です。サービスアカウントに 'Storage 管理者' 権限があるか確認してください。")
        elif "404" in str(e):
            print("バケット名が見つかりません。")

if __name__ == "__main__":
    set_cors()
