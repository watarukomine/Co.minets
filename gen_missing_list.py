import os

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

DOWNLOAD_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"

def generate_missing_list():
    present = os.listdir(DOWNLOAD_DIR)
    missing = []
    
    for m in METRICS:
        for r in ROUTES:
            for c in CATEGORIES:
                filename = f"【{m}】{r}_{c}.csv"
                if filename not in present:
                    missing.append(filename)
    
    with open("missing_files_list.py", "w", encoding="utf-8") as f:
        f.write("MISSING_FILES = [\n")
        for m_file in missing:
            f.write(f"    '{m_file}',\n")
        f.write("]\n")
    print(f"Generated missing_files_list.py with {len(missing)} files.")

if __name__ == "__main__":
    generate_missing_list()
