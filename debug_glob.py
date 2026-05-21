import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

print(f"BASE_DIR: {BASE_DIR}")
print(f"DOWNLOAD_DIR: {DOWNLOAD_DIR}")

pattern = os.path.join(DOWNLOAD_DIR, "【*】*.csv")
print(f"Pattern: {pattern}")

files = glob.glob(pattern)
print(f"Found {len(files)} files.")

if len(files) == 0:
    # Try just listing the directory
    print("Listing directory content:")
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith(".csv"):
                print(f" - {f}")
    except Exception as e:
        print(f"Error listing dir: {e}")

    # Try a simpler glob
    print("Trying simpler glob (*.csv):")
    simpler_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.csv"))
    print(f"Found {len(simpler_files)} files.")
