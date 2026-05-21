import firebase_admin
from firebase_admin import credentials, firestore
import os

def check_firestore():
    try:
        # Resolve absolute path for service account
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
        
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"Error: {SERVICE_ACCOUNT_FILE} not found.")
            return

        # Initialize
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            firebase_admin.initialize_app(cred)
        
        # Test connection to "cominets" database
        print("Connecting to database: cominets...")
        try:
            db = firestore.client(database_id="cominets")
            # List collections
            collections = db.collections()
            col_names = [c.id for c in collections]
            print(f"Collections found in 'cominets': {col_names}")
            
            for col_name in col_names:
                docs = db.collection(col_name).limit(5).get()
                doc_ids = [d.id for d in docs]
                print(f"  - Collection '{col_name}' Sample Docs: {doc_ids}")
        except Exception as e:
            print(f"Error accessing 'cominets': {e}")

        # Also check default to compare
        try:
            print("\nComparing with '(default)' database...")
            db_def = firestore.client() # default
            col_def = [c.id for c in db_def.collections()]
            print(f"Collections in '(default)': {col_def}")
            for col_name in col_def:
                docs = db_def.collection(col_name).limit(5).get()
                doc_ids = [d.id for d in docs]
                print(f"  - Collection '{col_name}' Sample Docs: {doc_ids}")
        except Exception as e:
            print(f"Error accessing '(default)': {e}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    check_firestore()
