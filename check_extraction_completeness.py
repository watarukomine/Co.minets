import os
import sys

# Set stdout to handle utf-8 even on windows console if possible, 
# but we will just avoid emojis to be safe.
try:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except:
    pass

# ターゲット設定
METRICS = ["売上", "粗利"]
ROUTES = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商"
]
CATEGORIES = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "211_特販6品目", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "241_エンジンオイル", "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

DOWNLOAD_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

def check_missing():
    print("Checking data extraction status in extracted_data...")
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"Error: Directory not found: {DOWNLOAD_DIR}")
        return

    present = os.listdir(DOWNLOAD_DIR)
    
    missing = []
    success_count = 0
    zero_data_count = 0
    total_count = len(METRICS) * len(ROUTES) * len(CATEGORIES)
    
    for m in METRICS:
        for r in ROUTES:
            for c in CATEGORIES:
                filename_csv = f"【{m}】{r}_{c}.csv"
                filename_zip = f"【{m}】{r}_{c}.zip"
                filename_zero = f"[ZERO_DATA]【{m}】{r}_{c}.csv"
                
                if filename_csv in present or filename_zip in present:
                    success_count += 1
                elif filename_zero in present:
                    success_count += 1
                    zero_data_count += 1
                else:
                    missing.append(filename_csv)
                
    print(f"\nSummary:")
    print(f"  - Total expected: {total_count}")
    print(f"  - Files found: {success_count} (including {zero_data_count} zero-data markers)")
    print(f"  - Missing: {len(missing)}")
    
    if missing:
        print("\nMissing files (Retry needed):")
        for m_file in missing:
            print(f"  - {m_file}")
            # Check for error screenshot (format: error_CATEGORY.png)
            # Find the category part from the filename
            # Filename: 【売上】a-00 総販_100_総売上.csv
            try:
                cat_only = m_file.split("_", 1)[1].replace(".csv", "")
                err_img = f"error_{cat_only}.png"
                if err_img in present:
                    print(f"    (Note: {err_img} exists in downloads)")
            except:
                pass
    else:
        print("\nAll data acquired successfully!")

if __name__ == "__main__":
    check_missing()
