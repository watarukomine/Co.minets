import os
import shutil
import glob

def clean_cache():
    print("--- RPA Cache Cleanup Utility ---")
    
    # 1. Target Directories (Browser profiles and downloads can be HUGE)
    target_dirs = [
        "edge_profile_rpa",
        "chrome_profile_rpa",
        "playwright_profile",
        "__pycache__",
        "downloads"  # New target: 12GB+ of CSV files found here
    ]
    
    total_freed = 0
    
    for d in target_dirs:
        path = os.path.abspath(d)
        if os.path.exists(path):
            print(f"Checking directory: {d}...", end=" ")
            try:
                # Calculate size before deletion
                size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            size += os.path.getsize(fp)
                        except:
                            pass
                
                if d == "downloads":
                    print(f"\n[WARNING] Found {size / (1024*1024):.2f} MB in {d} folder.")
                    confirm = input("Are you sure you want to delete ALL files in the 'downloads' folder? (y/n): ")
                    if confirm.lower() != 'y':
                        print("Skipping 'downloads' folder.")
                        continue

                shutil.rmtree(path)
                print(f"DONE (Freed {size / (1024*1024):.2f} MB)")
                total_freed += size
            except Exception as e:
                print(f"FAILED ({e})")

    # 2. Target Files (Logs, heavy CSVs in root, and debug images)
    target_files = [
        "*.log",
        "*.csv",      # Target loose CSV files too
        "debug_*.png",
        "dom_snapshot.html",
        "dump.html",
        "dom_iframe_*.html",
        "iframe_dom.txt",
        "data_matrix.json_backup" # If any backups exist
    ]
    
    for pattern in target_files:
        files = glob.glob(pattern)
        for f in files:
            try:
                size = os.path.getsize(f)
                os.remove(f)
                print(f"Removed file: {f} ({size / 1024:.1f} KB)")
                total_freed += size
            except Exception as e:
                print(f"Could not remove {f}: {e}")

    # 3. Clean Project-Specific Logs
    log_dirs = [
        "../L06代替/src/local_server/Antigravity_Logs" # Placeholder if relative path works
    ]
    # Also check %TEMP%
    temp_log_dir = os.path.join(os.environ.get('TEMP'), 'Antigravity_Logs')
    if os.path.exists(temp_log_dir):
        print(f"Cleaning logs in TEMP: {temp_log_dir}...")
        for f in os.listdir(temp_log_dir):
            fp = os.path.join(temp_log_dir, f)
            try:
                size = os.path.getsize(fp)
                os.remove(fp)
                total_freed += size
            except:
                pass

    print(f"\nCleanup Complete. Estimated space recovered: {total_freed / (1024*1024):.2f} MB")
    print("\n--- Next Steps for Fileforce ---")
    print("1. Right-click the Fileforce icon in the taskbar.")
    print("2. Go to 'Maintenance' or 'Settings'.")
    print("3. Look for 'Purge Cache' or 'Clear Local Cache'.")
    print("4. Restart the Fileforce client if the 0.00 GB warning persists.")

if __name__ == "__main__":
    clean_cache()
