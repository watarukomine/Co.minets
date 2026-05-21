import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_PROGRESS_FILE = os.path.join(BASE_DIR, "sync_progress.json")

def main():
    if os.path.exists(SYNC_PROGRESS_FILE):
        with open(SYNC_PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        target = "売上_a-00総販_100_総売上"
        completed = data.get("completed", [])
        
        if target in completed:
            completed.remove(target)
            print(f"✓ '{target}' を同期済リストから削除しました。")
            data["completed"] = completed
            
            with open(SYNC_PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✓ sync_progress.json の更新に成功しました。")
        else:
            print(f"ℹ '{target}' は既に未同期状態、もしくはリストに存在しません。")
    else:
        print("✗ sync_progress.json が見つかりません。")

if __name__ == "__main__":
    main()
