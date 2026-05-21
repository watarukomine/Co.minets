import os
import re
import sys
import subprocess
from datetime import datetime

LOG_FILE = "extraction.log"

def get_rpa_status():
    # Check if python is running with the script name via tasklist
    is_running = False
    try:
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq python.exe" /V /FO CSV', shell=True).decode('cp932', errors='ignore')
        if "rpa_extractor.py" in output:
            is_running = True
    except: pass
    
    if not os.path.exists(LOG_FILE):
        return "Log file not found.", is_running

    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except:
        return "Could not read log file.", is_running

    last_attempt = "N/A"
    success_count = 0
    fail_count = 0
    downloads = {} # key: filename, value: status
    last_log_time = "N/A"

    for line in lines:
        if not line.strip(): continue
        last_log_time = line[:19] # Capture timestamp
        if "Navigation Attempt" in line:
            m = re.search(r"Navigation Attempt (\d+)", line)
            if m: last_attempt = m.group(1)
        if "DOWNLOAD START:" in line:
            m = re.search(r"DOWNLOAD START: (.*)", line)
            if m: downloads[m.group(1).strip()] = "Running"
        if "SUCCESS:" in line and "Dashboard" not in line:
            for fn in downloads:
                if fn in line:
                    downloads[fn] = "Success"
                    success_count += 1
        if "FAILED:" in line:
            m = re.search(r"FAILED: (.*)", line)
            if m:
                fn = m.group(1).strip()
                downloads[fn] = "Failed"
                fail_count += 1

    # Get current state
    current = "Idle"
    duration = "N/A"
    health = "Good"
    if is_running:
        if lines:
            start_time_str = lines[0][:19]
            try:
                start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                duration = str(datetime.now() - start_dt).split('.')[0]
            except: pass

        # Check health (consecutive failures)
        consecutive_fails = 0
        for line in reversed(lines):
            if "SUCCESS:" in line: break
            if "FAILED:" in line: consecutive_fails += 1
        
        if consecutive_fails >= 5: health = f"Warning ({consecutive_fails} consecutive fails)"
        if consecutive_fails >= 10: health = f"CRITICAL ({consecutive_fails} consecutive fails)"

        for line in reversed(lines):
            if "SELECTING:" in line:
                current = line.split("SELECTING:")[1].strip()
                break
            if "DOWNLOAD START:" in line:
                current = "Downloading: " + line.split("DOWNLOAD START:")[1].strip()
                break
    else:
        current = "Not Running"

    print("="*60)
    print(f"RPA MONITORING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"Status:      {'[RUNNING]' if is_running else '[STOPPED]'}")
    print(f"Duration:    {duration}")
    print(f"Health:      {health}")
    print(f"Last Log:    {last_log_time}")
    print(f"Navigation:  Attempt {last_attempt} (Dashboard Found)")
    print(f"Current Activity: {current}")
    print(f"Stats:       Success: {success_count} | Failures: {fail_count}")
    print("-" * 60)
    print("Recent Extraction Results (Last 10):")
    for fn, status in list(downloads.items())[-10:]:
        print(f"  [{status:7}] {fn}")
    print("="*60)

if __name__ == "__main__":
    get_rpa_status()
