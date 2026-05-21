import os

DOWNLOAD_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"

metrics = ["売上", "粗利"]
routes = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商"
]
sales_categories = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

missing = []
found_count = 0

for metric in metrics:
    for route in routes:
        for category in sales_categories:
            safe_category = category.replace('/', '_').replace(':', '_')
            safe_route = route.replace('/', '_').replace(':', '_')
            safe_metric = metric.replace('/', '_').replace(':', '_')
            filename = f"【{safe_metric}】{safe_route}_{safe_category}.csv"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                found_count += 1
            else:
                missing.append(f"[{metric}] {route} - {category}")

total = len(metrics) * len(routes) * len(sales_categories)

with open(r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\missing_report.txt", "w", encoding="utf-8") as f:
    f.write(f"期待される全ファイル数: {total}\n")
    f.write(f"うち、ダウンロード済み（成功）: {found_count}\n")
    f.write(f"漏れファイル数: {len(missing)}\n\n")
    
    if missing:
        f.write("--- 📝 取得漏れリスト ---\n")
        # 最初の30件と最後の数件を表示
        for m in missing[:30]:
            f.write(m + "\n")
        if len(missing) > 30:
            f.write(f"... 他 {len(missing) - 30} 件\n")
