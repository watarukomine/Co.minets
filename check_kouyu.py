import os
import glob

DOWNLOAD_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"
kouyu_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*鉱油*.csv"))
print(f"鉱油ファイル数: {len(kouyu_files)}")
for f in kouyu_files[:5]:
    print(os.path.basename(f))
