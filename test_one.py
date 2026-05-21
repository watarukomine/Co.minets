# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
from rpa_extractor import get_driver, ensure_dashboard, set_params, export_csv, DOWNLOAD_DIR, log
import glob
import shutil
import re

def test_single_extraction_v470():
    log("--- RPA SINGLE TEST (v4.7.0 / UUID-Robust) ---")
    driver = get_driver()
    if not driver:
        log("FAIL: Could not connect to browser.")
        return

    try:
        if not ensure_dashboard(driver):
            log("FAIL: Dashboard not ready.")
            return

        # TARGET: 売上 / a-00 総販 / 100_総売上
        m, r, c = "売上", "a-00 総販", "100_総売上"
        filename = f"【TEST_v470】{r}_{c}.csv"
        dest = os.path.join(DOWNLOAD_DIR, filename)

        log(f"TARGETING: {filename}")
        
        # Cleanup pre-existing test files in BOTH possible folders
        search_paths = [DOWNLOAD_DIR, os.path.join(os.path.expanduser("~"), "Downloads")]
        
        def get_latest_file_info(paths):
            all_files = []
            for d in paths:
                if not os.path.exists(d): continue
                all_files.extend([os.path.join(d, f) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])
            if not all_files: return None, 0
            latest = max(all_files, key=os.path.getmtime)
            return latest, os.path.getmtime(latest)

        _, last_mtime = get_latest_file_info(search_paths)

        if set_params(driver, m, r, c):
            log("SUCCESS: Parameters set. Waiting 12s for dashboard...")
            time.sleep(12)
            
            res = export_csv(driver)
            if res and res.get("ok"):
                log("Export triggered. Monitoring for ANY new file...")
                found = False
                for i in range(50):
                    current_latest, current_mtime = get_latest_file_info(search_paths)
                    if current_mtime > last_mtime + 0.1: # Something was created!
                        if os.path.getsize(current_latest) > 100:
                            log(f"FOUND NEW FILE: {os.path.basename(current_latest)}")
                            
                            # Conversion and Move
                            try:
                                try:
                                    with open(current_latest, 'r', encoding='utf-8', errors='replace') as f_in:
                                        data = f_in.read()
                                except:
                                    with open(current_latest, 'r', encoding='shift_jis', errors='replace') as f_in:
                                        data = f_in.read()

                                with open(dest, 'w', encoding='shift_jis', errors='replace', newline='') as f_out:
                                    f_out.write(data)
                                
                                if os.path.exists(current_latest): os.remove(current_latest)
                                log(f"⭐ SUCCESS!! Saved as: {dest}")
                                found = True
                                break
                            except Exception as ee:
                                log(f"File process error: {ee}")
                    time.sleep(2)
                if not found: log("FAIL: No new file detected after export.")
            else: log(f"FAIL: Export trigger error: {res}")
        else: log("FAIL: Param setting error.")

    finally:
        log("Test completed. Closing driver...")
        driver.quit()

if __name__ == "__main__":
    test_single_extraction_v470()
