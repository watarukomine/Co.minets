import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "data", "売上_a-00総販_100_総売上.json")

def main():
    if not os.path.exists(JSON_FILE):
        print(f"File not found: {JSON_FILE}")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # We need to find index 2172
    # Let's also check the timeline from sync_progress.json
    progress_file = os.path.join(BASE_DIR, "sync_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
            timeline = progress.get("timeline", [])
            try:
                idx = timeline.index("2025-04-01")
                print(f"Index of 2025-04-01: {idx}")
            except ValueError:
                print("2025-04-01 not in timeline")
                idx = -1
    else:
        idx = 2172

    kanagawa = data.get("85371 神奈川支社")
    if kanagawa:
        current_list = kanagawa.get("current", [])
        previous_list = kanagawa.get("previous", [])
        if 0 <= idx < len(current_list):
            print(f"2025-04-01 Current: {current_list[idx]}")
            print(f"2025-04-01 Previous: {previous_list[idx]}")
        else:
            print(f"Index {idx} out of range (length: {len(current_list)})")
    else:
        print("Kanagawa branch not found in JSON keys:")
        print(list(data.keys()))

if __name__ == "__main__":
    main()
