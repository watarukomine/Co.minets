import os
import json

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
# 重複を除去（907が2回あるため）
SALES_CLASSES_ALL = list(dict.fromkeys(SALES_CLASSES_CORE + SALES_CLASSES_DETAIL))

X_DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

def check_exhaustive():
    print("--- 2,700パターン全件スキャン開始 ---")
    
    if not os.path.exists(X_DEST_DIR):
        print(f"エラー: {X_DEST_DIR} が見つかりません。")
        return

    # 実際に存在するファイルをリストアップ
    present_files = set(os.listdir(X_DEST_DIR))
    
    summary = {
        "core_route_core_class": {"total": 0, "found": 0, "missing": []},
        "core_route_detail_class": {"total": 0, "found": 0, "missing": []},
        "detail_route_core_class": {"total": 0, "found": 0, "missing": []},
        "detail_route_detail_class": {"total": 0, "found": 0, "missing": []},
    }

    total_all = 0
    found_all = 0

    for amount in AMOUNT_TYPES:
        for route in ROUTES_ALL:
            is_core_route = route in ROUTES_CORE
            for sc in SALES_CLASSES_ALL:
                is_core_class = sc in SALES_CLASSES_CORE
                
                # ファイル名の生成
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_filename_csv = f"【{amount}】{route}_{sc_fname}.csv"
                target_filename_zip = f"【{amount}】{route}_{sc_fname}.zip"
                
                # 分類
                if is_core_route and is_core_class:
                    cat = "core_route_core_class"
                elif is_core_route and not is_core_class:
                    cat = "core_route_detail_class"
                elif not is_core_route and is_core_class:
                    cat = "detail_route_core_class"
                else:
                    cat = "detail_route_detail_class"
                
                summary[cat]["total"] += 1
                total_all += 1
                
                if target_filename_csv in present_files or target_filename_zip in present_files:
                    summary[cat]["found"] += 1
                    found_all += 1
                else:
                    summary[cat]["missing"].append(target_filename_csv)

    print(f"\n全体集計:")
    print(f"  - 総計: {total_all}")
    print(f"  - 抽出済み: {found_all}")
    print(f"  - 未抽出: {total_all - found_all}")

    print(f"\n詳細内訳:")
    for cat, data in summary.items():
        print(f"  {cat}:")
        print(f"    - 期待: {data['total']}")
        print(f"    - 発見: {data['found']}")
        print(f"    - 不足: {len(data['missing'])}")

    # 結果をファイルに保存
    report_path = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\exhaustive_completeness_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== 2,700パターン全件スキャン報告書 ===\n\n")
        f.write(f"総期待数: {total_all}\n")
        f.write(f"総取得数: {found_all}\n")
        f.write(f"総不足数: {total_all - found_all}\n\n")
        
        for cat, data in summary.items():
            f.write(f"--- 分類: {cat} ---\n")
            f.write(f"期待: {data['total']} / 発見: {data['found']} / 不足: {len(data['missing'])}\n")
            if data["missing"]:
                f.write("不足リスト (一部):\n")
                for m in data["missing"][:20]:
                    f.write(f"  - {m}\n")
                if len(data["missing"]) > 20:
                    f.write(f"  ...他 {len(data['missing']) - 20} 件\n")
            f.write("\n")

    print(f"\n詳細レポートを保存しました: {report_path}")

if __name__ == "__main__":
    check_exhaustive()
