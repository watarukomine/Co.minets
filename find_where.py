# -*- coding: utf-8 -*-
import os
from datetime import datetime

def scan_folders():
    paths = [
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Downloads"),
        os.path.join(os.path.expanduser("~"), "OneDrive - トヨタモビリティパーツ株式会社", "Downloads"),
        os.path.join(os.path.expanduser("~"), "Desktop")
    ]
    
    print("--- Searching for recently created files without extensions ---")
    now = datetime.now()
    
    for p in paths:
        if not os.path.exists(p): continue
        print(f"\nChecking: {p}")
        try:
            files = os.listdir(p)
            for f in files:
                full = os.path.join(p, f)
                if os.path.isfile(full):
                    mtime = datetime.fromtimestamp(os.path.getmtime(full))
                    # Focus on files created in the last 2 hours
                    if (now - mtime).total_seconds() < 7200:
                        name, ext = os.path.splitext(f)
                        print(f"  [{mtime.strftime('%H:%M:%S')}] {f} (Ext: '{ext}', Size: {os.path.getsize(full)})")
        except Exception as e:
            print(f"  Error checking {p}: {e}")

if __name__ == "__main__":
    scan_folders()
