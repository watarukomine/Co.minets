
import firebase_admin
from firebase_admin import credentials, storage
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")

def check_buckets():
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(cred)
        
        # This might not list all buckets if we don't know the project, 
        # but let's try to see what's available if we can.
        # Actually, listing buckets requires project ID if not set.
        from google.cloud import storage as gcs
        client = gcs.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
        buckets = list(client.list_buckets())
        print("Available buckets:")
        for bucket in buckets:
            print(f" - {bucket.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_buckets()
