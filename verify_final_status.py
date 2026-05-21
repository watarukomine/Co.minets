import os

# ==========================================
# 抽出パターンの定義 (rpa_extractor.py よりコピー)
# ==========================================
AMOUNT_TYPES = ["売上", "粗利"]
ROUTES_CORE = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商"
]
ROUTES_DETAIL = [
    "d-02 その他再販業者", "d-03 修理業者", "d-04 GSS", 
    "d-05 用品小売り店", "d-06 その他", "e-01 修理工場", 
    "e-02 特定修理業者", "e-03 大口ユーザー"
]
ROUTES_ALL = ROUTES_CORE + ROUTES_DETAIL

SALES_CLASSES_CORE = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

SALES_CLASSES_DETAIL = [
    "211_特販6品目", "214_特販部品その他", "223_レクサスセット", "224_タイヤその他", 
    "231_ACデルコ", "232_パナソニック", "233_GSユアサ", "234_レクサスバッテリー", 
    "235_地場バッテリー", "236_地場パナソニック", "237_地場GSユアサ", 
    "238_パナソニック（本部＋地場）", "239_GSユアサ（本部＋地場）", "241_エンジンオイル",
    "242_シャシオイル", "243_フルード", "245_礦油その他", "320_機能部品", "410_ナビ", 
    "411_T-Connect対応ナビ", "412_ベーシックナビ", "413_エントリーナビ", 
    "414_ナビキット", "415_T-Connectナビキット", "416_エントリーナビキット", 
    "417_本部扱いナビ", "418_ナビその他", "420_ナビ関連オプション", 
    "421_後席ディスプレイ", "422_モニターカメラ類", "423_地図ソフト", 
    "424_ドライブレコーダー", "425_純正ドライブレコーダー", 
    "426_本部調達ドライブレコーダー", "427_その他ドライブレコーダー", 
    "428_ナビ関連オプションその他", "430_オーディオ", "440_ITS関連商品", 
    "450_ベーシック推奨用品", "460_オプション推販用品", "461_後付け安全4商品", 
    "462_TRD", "463_モデリスタ", "464_オプション推販用品その他", "470_レクサス用品", 
    "480_用品その他", "500_その他", "510_通信事業", "521_本部調達工具", 
    "522_地場工具", "530_C＋WALK（本体）", "540_本部商品その他", "550_新車カタログ", 
    "560_その他（その他）", "901_プレミアムCAF", "902_パナソニックバッテリー（本部＋地場）", 
    "903_GSユアサバッテリー（本部＋地場）", "904_ブレーキフルード", "905_LLC", 
    "907_純正ETC2.0", "907_純正ETC", "909_TCD用品", "910_トヨタ車TRD", 
    "911_レクサス車TRD", "912_トヨタ車モデリスタ", "913_レクサス車モデリスタ", 
    "914_TMP用品", "915_TZ用品", "916_TMP車種専用品", "917_夏タイヤ", "918_冬タイヤ"
]
SALES_CLASSES_ALL = list(dict.fromkeys(SALES_CLASSES_CORE + SALES_CLASSES_DETAIL))

X_DEST_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

def check():
    present_files = set(os.listdir(X_DEST_DIR))
    
    # 優先294パターンのチェック (AMOUNT_TYPES * ROUTES_CORE * SALES_CLASSES_CORE)
    priority_total = 2 * len(ROUTES_CORE) * len(SALES_CLASSES_CORE)
    priority_found = 0
    priority_missing = []
    
    total_expected = 2 * len(ROUTES_ALL) * len(SALES_CLASSES_ALL)
    total_found = 0
    
    for amount in AMOUNT_TYPES:
        for route in ROUTES_ALL:
            for sc in SALES_CLASSES_ALL:
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_csv = f"【{amount}】{route}_{sc_fname}.csv"
                target_zip = f"【{amount}】{route}_{sc_fname}.zip"
                target_zero = f"[ZERO_DATA]【{amount}】{route}_{sc_fname}.csv"
                
                found = (target_csv in present_files or target_zip in present_files or target_zero in present_files)
                
                if found:
                    total_found += 1
                    if route in ROUTES_CORE and sc in SALES_CLASSES_CORE:
                        priority_found += 1
                else:
                    if route in ROUTES_CORE and sc in SALES_CLASSES_CORE:
                        priority_missing.append(target_csv)

    with open("current_status_summary.txt", "w", encoding="utf-8") as f:
        f.write("=== 最新データ抽出状況レポート ===\n\n")
        f.write(f"1. 最優先 266パターン (コア販売区分 x コアルート):\n")
        f.write(f"   - 完了: {priority_found} / {priority_total}\n")
        f.write(f"   - 未完了: {len(priority_missing)}\n\n")
        
        f.write(f"2. 全 2,700パターン (推計):\n")
        f.write(f"   - 抽出済み: {total_found} / {total_expected}\n\n")
        
        if priority_missing:
            f.write("未完了の最優先ファイル:\n")
            for m in priority_missing:
                f.write(f"  - {m}\n")

if __name__ == "__main__":
    check()
