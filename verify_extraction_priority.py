import os
import sys

# ターゲット設定 (ユーザー要望の19区分 x 7ルート x 2種)
METRICS = ["売上", "粗利"]
ROUTES = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商"
]
CATEGORIES = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_鉱油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

def verify():
    print(f"--- 優先取得対象(266件)の精査を開始 ---")
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"エラー: {DOWNLOAD_DIR} が見つかりません。")
        return

    present_files = os.listdir(DOWNLOAD_DIR)
    
    missing = []
    found_count = 0
    total_count = len(METRICS) * len(ROUTES) * len(CATEGORIES)
    
    for m in METRICS:
        for r in ROUTES:
            for c in CATEGORIES:
                # ファイル名のカッコの揺れ（半角・全角）を柔軟に探す
                filename_full = f"【{m}】{r}_{c}.csv"
                filename_half = filename_full.replace("（", "(").replace("）", ")")
                
                if filename_full in present_files or filename_half in present_files:
                    found_count += 1
                else:
                    missing.append(filename_full)
                    
    print(f"\n集計結果:")
    print(f"  - 期待合計: {total_count}")
    print(f"  - 発見済み: {found_count}")
    print(f"  - 未取得(漏れ): {len(missing)}")
    
    if missing:
        print(f"\n未取得リスト (最初の10件):")
        for m_file in missing[:10]:
            print(f"  - {m_file}")
        if len(missing) > 10:
            print(f"  ...他 {len(missing) - 10} 件")
    else:
        print("\nおめでとうございます！全ての優先データが「漏れなく」揃っています。")

if __name__ == "__main__":
    verify()
