import os
import glob

DOWNLOAD_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"
csvs = glob.glob(os.path.join(DOWNLOAD_DIR, "*.csv"))

print(f"--- DOWNLOADED FILES COUNT ---")
print(f"TOTAL CSV FILES: {len(csvs)}")

if len(csvs) == 294:
    print("\n[RESULT] ALL 294 FILES CAPTURED SUCCESSFULLY! 100% COMPLETION.")
else:
    print(f"\n[RESULT] MISSING {294 - len(csvs)} FILES.")
    # 名前を出力して特定
    all_metrics = ["売上", "粗利"]
    all_routes = ["a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス", "c-01 卸売", "c-02 直売", "d-01 部品商"]
    all_categories = ["100_総売上", "110_総売上（除通信事業）", "200_重点商品", "210_特販部品", "211_特販6品目", "212_競争品", "213_クリーンエアフィルター", "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", "241_エンジンオイル", "244_ケミカル", "300_一般部品", "310_外装部品", "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"]
    
    existing_files = {os.path.basename(f) for f in csvs}
    missing = []
    for m in all_metrics:
        for r in all_routes:
            for c in all_categories:
                fname = f"【{m}】{r}_{c}.csv".replace("/", "_")
                if fname not in existing_files:
                    missing.append(fname)
    
    if missing:
        print("\nMISSING FILES:")
        for m in missing:
            print(f" - {m}")
