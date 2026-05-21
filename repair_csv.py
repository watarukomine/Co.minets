# -*- coding: utf-8 -*-
import os
import glob
import shutil
import re
from datetime import datetime

def repair_and_recover():
    print("--- CSV Recovery & Repair Tool (v4.6.9) ---")
    
    # 1. Setup paths
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    project_downloads = "downloads"
    if not os.path.exists(project_downloads): os.makedirs(project_downloads)

    # 2. Find "Mystery" UUID files (files with no extension created today)
    print(f"Scanning for mystery files in: {user_downloads}")
    all_files = os.listdir(user_downloads)
    recovered_count = 0
    
    for f in all_files:
        full_path = os.path.join(user_downloads, f)
        if os.path.isfile(full_path):
            # Check if it has NO extension and looks like a UUID or hex string
            name, ext = os.path.splitext(f)
            if ext == "" and (len(name) > 20 or re.match(r'^[a-f0-9\-]+$', name)):
                # Check file size (only CSVs of reasonable size)
                size = os.path.getsize(full_path)
                if 1000 < size < 1000000: # 1KB to 1MB
                    # Try reading first line to see if it's a CSV
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as check_f:
                            first_line = check_f.readline()
                            if '"' in first_line or ',' in first_line:
                                # It's a CSV!
                                dest_name = f"recovered_{name[:8]}.csv"
                                dest_path = os.path.join(project_downloads, dest_name)
                                
                                # Convert to Shift-JIS while moving
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f_in:
                                    data = f_in.read()
                                with open(dest_path, 'w', encoding='shift_jis', errors='replace', newline='') as f_out:
                                    f_out.write(data)
                                
                                print(f"✅ RECOVERED: {f} -> {dest_name}")
                                recovered_count += 1
                    except: pass

    # 3. Repair existing files in project downloads
    print(f"Repairing existing files in: {project_downloads}")
    proj_files = glob.glob(os.path.join(project_downloads, "*.csv"))
    for f in proj_files:
        try:
            # Try to see if it needs conversion (if it's UTF-8 it might mojibake in Excel)
            with open(f, 'r', encoding='utf-8', errors='ignore') as f_in:
                data = f_in.read()
            with open(f, 'w', encoding='shift_jis', errors='replace', newline='') as f_out:
                f_out.write(data)
            print(f"🔧 Repaired: {os.path.basename(f)}")
        except: pass

    print(f"\n--- Done. Recovered {recovered_count} mystery files. ---")
    print("Check the 'downloads' folder in this project to see them in Excel.")

if __name__ == "__main__":
    repair_and_recover()
