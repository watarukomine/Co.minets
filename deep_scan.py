# -*- coding: utf-8 -*-
import os
import re

def deep_scan():
    paths = [
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "OneDrive - トヨタモビリティパーツ株式会社", "Downloads"),
    ]
    
    print("--- DEEP SCAN: List all files in Downloads (Last 50) ---")
    
    for p in paths:
        if not os.path.exists(p): continue
        print(f"\nLocation: {p}")
        try:
            files = []
            for f in os.listdir(p):
                full = os.path.join(p, f)
                if os.path.isfile(full):
                    files.append((os.path.getmtime(full), f, os.path.getsize(full)))
            
            # Sort by time descend
            files.sort(key=lambda x: x[0], reverse=True)
            
            for mtime, name, size in files[:50]:
                from datetime import datetime
                ts = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  [{ts}] {name} ({size} bytes)")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    deep_scan()
