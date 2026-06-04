import os
import zipfile
import json

# Setup lists matching rpa_extractor_monthly.py
AMOUNT_TYPES = ["売上", "粗利"]
ROUTES_ALL = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商",
    "d-02 その他再販業者", "d-03 修理業者", "d-04 GSS", 
    "d-05 用品小売り店", "d-06 その他", "e-01 修理工場", 
    "e-02 特定修理業者", "e-03 大口ユーザー"
]
SALES_CLASSES_ALL = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）",
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

EXCLUDE_COMBINATIONS = []
exclude_json_path = "always_zero_combinations.json"
if os.path.exists(exclude_json_path):
    try:
        with open(exclude_json_path, 'r', encoding='utf-8') as f:
            exclude_data = json.load(f)
            EXCLUDE_COMBINATIONS = [(item['route'], item['sales_class']) for item in exclude_data]
    except Exception as e:
        print(f"Error loading always_zero_combinations.json: {e}")

DEST_DIR = "extracted_data"
target_year = 2026
target_month = 5

target_prefix = f"{target_year:04d}-{target_month:02d}-"
target_prefix_slash = f"{target_year:04d}/{target_month:02d}/"

def check_already_extracted(zip_path):
    if not os.path.exists(zip_path):
        return False
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                content = f.read().decode('utf-8-sig')
                if target_prefix in content or target_prefix_slash in content:
                    return True
    except Exception as e:
        pass
    return False

missing_patterns = []
excluded_count = 0
already_extracted_count = 0
zero_data_markers = 0

for amount in AMOUNT_TYPES:
    for route in ROUTES_ALL:
        for sc in SALES_CLASSES_ALL:
            if (route, sc) in EXCLUDE_COMBINATIONS:
                excluded_count += 1
                continue
            
            sc_fname = sc.replace("(", "（").replace(")", "）")
            target_filename = f"【{amount}】{route}_{sc_fname}.csv"
            dest_zip_path = os.path.join(DEST_DIR, target_filename.replace(".csv", ".zip"))
            dest_zero_path = os.path.join(DEST_DIR, f"[ZERO_DATA]{target_filename}")
            
            if os.path.exists(dest_zero_path):
                zero_data_markers += 1
                continue
                
            if check_already_extracted(dest_zip_path):
                already_extracted_count += 1
                continue
            
            # If not in always zero, not zero data marked, and doesn't contain May 2026 data:
            missing_patterns.append((amount, route, sc, target_filename))

print(f"Total combinations checked (excluding static zeros): {2700 - excluded_count}")
print(f"Static zeros: {excluded_count}")
print(f"Zero data markers found for target month: {zero_data_markers}")
print(f"Already extracted / contains May data: {already_extracted_count}")
print(f"Missing May data patterns: {len(missing_patterns)}")

if missing_patterns:
    print("\nMissing patterns details:")
    for amount, route, sc, fname in missing_patterns[:50]:
        print(f"  - Amount: {amount}, Route: {route}, Class: {sc} (File: {fname})")
    if len(missing_patterns) > 50:
        print(f"  ... and {len(missing_patterns) - 50} more.")
else:
    print("\nAll non-excluded patterns have May 2026 data successfully merged/extracted!")
