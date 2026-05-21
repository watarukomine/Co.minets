import os
import shutil

DOWNLOAD_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"
src = os.path.join(DOWNLOAD_DIR, "日別実績_1773882222818.csv")
dst = os.path.join(DOWNLOAD_DIR, "【売上】a-00 総販_211_特販6品目.csv")

if os.path.exists(src):
    shutil.move(src, dst)
    print(f"SUCCESS: Moved {src} to {dst}")
else:
    # 別の名前の可能性も考慮して glob で探す
    import glob
    temps = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))
    if temps:
        latest = max(temps, key=os.path.getctime)
        shutil.move(latest, dst)
        print(f"SUCCESS: Moved LATEST {latest} to {dst}")
    else:
        print("FAILED: No temp files found")
