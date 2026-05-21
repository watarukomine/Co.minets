import os
import ctypes
import platform
import time
import glob
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ==========================================
# 抽出パターンのマスターデータ (2,700全件・優先順位付き)
# ==========================================
AMOUNT_TYPES = ["売上", "粗利"]
BRANCH = "すべて"

# --- ルート定義 (優先7ルート) ---
ROUTES_CORE = [
    "a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス",
    "c-01 卸売", "c-02 直売", "d-01 部品商"
]
# --- 詳細ルート定義 (残り8ルート) ---
ROUTES_DETAIL = [
    "d-02 その他再販業者", "d-03 修理業者", "d-04 GSS", 
    "d-05 用品小売り店", "d-06 その他", "e-01 修理工場", 
    "e-02 特定修理業者", "e-03 大口ユーザー"
]
ROUTES_ALL = ROUTES_CORE + ROUTES_DETAIL

# --- 販売区分定義 ---
# ※優先件数と正確性の向上のため、ユーザーの表記修正（全角カッコ等）を反映
SALES_CLASSES_CORE = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_鉱油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

# --- 詳細販売区分定義 (残り71件) ---
SALES_CLASSES_DETAIL = [
    "211_特販6品目", "214_特販部品その他", "223_レクサスセット", "224_タイヤその他", 
    "231_ACデルコ", "232_パナソニック", "233_GSユアサ", "234_レクサスバッテリー", 
    "235_地場バッテリー", "236_地場パナソニック", "237_地場GSユアサ", 
    "238_パナソニック（本部＋地場）", "239_GSユアサ（本部＋地場）", "241_エンジンオイル",
    "242_シャシオイル", "243_フルード", "245_鉱油その他", "320_機能部品", "410_ナビ", 
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
SALES_CLASSES_ALL = SALES_CLASSES_CORE + SALES_CLASSES_DETAIL

# ------------------------------------------


DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ==========================================
# ユーティリティ
# ==========================================

def get_free_space_gb(drive_name="C:"):
    """
    指定したドライブの空き容量をGB単位で取得（ctypes版: Windows対応）
    """
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        ctypes.c_wchar_p(f"{drive_name}\\"), None, None, ctypes.byref(free_bytes)
    )
    return free_bytes.value / (1024**3)

def wait_for_disk_space(threshold_gb=3.5):
    """
    Cドライブの空き容量が回復するまで待機する
    """
    while True:
        free_gb = get_free_space_gb("C")
        if free_gb >= threshold_gb:
            break
        print(f"\n[！警告！] Cドライブの空き容量が不足しています ({free_gb:.2f} GB)")
        print(f"Fileforceの動作には {threshold_gb} GB 以上の空きが必要です。")
        print("キャッシュをクリアするか、不要なファイルを削除してください。回復を待機中...")
        time.sleep(30)

FILTER_INDEX = {
    "売上/粗利": 0,
    "支社": 1,
    "販売区分": 2,
    "ルート": 3,
}


# ==========================================
# UI操作関数
# ==========================================

def set_quicksight_filter(driver, filter_name, target_value):
    print(f"  [{filter_name}] → 「{target_value}」")
    idx = FILTER_INDEX.get(filter_name)
    comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
    if len(comboboxes) <= idx:
        raise Exception(f"combobox {idx} not found")

    combobox = comboboxes[idx]
    ActionChains(driver).move_to_element(combobox).click().perform()
    time.sleep(2.5)

    try:
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='値を検索']"))
        )
        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
        search_term = target_value.split("_")[0] + "_" if "_" in target_value else target_value
        search_box.send_keys(search_term)
        time.sleep(3.5)
    except TimeoutException:
        pass

    option = None
    try:
        option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@role='option' and (contains(@aria-label, '{target_value}') or contains(text(), '{target_value}'))]"))
        )
    except TimeoutException:
        try:
            option = driver.find_element(By.XPATH, f"//li[contains(@class, 'MuiMenuItem') and contains(text(), '{target_value}')]")
        except NoSuchElementException:
            pass

    if option is None:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        raise Exception(f"選択肢「{target_value}」が見つかりません")

    ActionChains(driver).move_to_element(option).click().perform()
    time.sleep(1)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1.5)


def export_csv(driver):
    """
    通知メッセージを検知し、かつ検知後に通知を閉じて画面をクリーンにする。
    """
    try:
        # 1. 表にホバー (より確実に可視化させる)
        table = driver.find_element(By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
        ActionChains(driver).move_to_element(table).perform()
        time.sleep(2)

        # 2. 「⋮」ボタンをクリック
        menu_btn = driver.find_element(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
        ActionChains(driver).move_to_element(menu_btn).click().perform()
        time.sleep(2)

        # 3. 「CSV へエクスポート」をクリック
        csv_btn = driver.find_element(By.XPATH, "//li[contains(@class, 'MuiMenuItem') and (contains(text(), 'CSV') or contains(text(), 'エクスポート'))]")
        ActionChains(driver).move_to_element(csv_btn).click().perform()
        
        # ★ 4. 「CSV の準備ができました。」トースト通知を待機
        print("    通知待ち: 「CSV の準備ができました。」を待機中...")
        try:
            toast = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'CSV の準備ができました')]"))
            )
            print("    ✓ 通知確認: QuickSight側の準備完了")
            
            # ★ 5. 通知を閉じて画面をクリーンにする（次に備える）
            try:
                # 親要素を遡ってクローズボタンを探す
                close_btn = toast.find_element(By.XPATH, "./ancestor::div[contains(@class, 'notification')]//button")
                ActionChains(driver).move_to_element(close_btn).click().perform()
                print("    ✓ 通知を閉じました")
                time.sleep(1) 
            except:
                # XPATHが合わない場合、単純な Esc キーで代用を試みる
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                pass
                
            return True
        except TimeoutException:
            print("    [警告] 通知がタイムアウトしました。データ量が多すぎるか、セッションが不安定です。")
            return False

    except Exception as e:
        print(f"    [警告] エクスポート操作失敗: {e}")
        return False


# ==========================================
# メイン
# ==========================================

def main():
    print("【TMP-ONE データ抽出ループシステム v10 (2,700件・表記修正版)】")

    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--start-maximized")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR, # 直接ネットワークドライブ(X:)に落とす (C:の二重消費を避ける)
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Edge(options=edge_options)
    driver.get("https://report.tmp-one.com/portal")

    print("\nダッシュボードが表示されたら、Enterキーを押してください。")
    input("準備完了Enter: ")

    try:
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'quicksight')]")))
        print("★ iframe接続成功")
    except:
        print("iframe接続に失敗しました。")

    total_expected = len(AMOUNT_TYPES) * len(ROUTES_ALL) * len(SALES_CLASSES_ALL)
    pattern_count = 0
    success_count = 0
    skip_count = 0
    fail_count = 0

    for amount in AMOUNT_TYPES:
        try:
            set_quicksight_filter(driver, "売上/粗利", amount)
        except Exception as e:
            print(f"  [エラー] 金額種別切替失敗: {e}")

        for route in ROUTES_ALL:
            try:
                set_quicksight_filter(driver, "ルート", route)
            except Exception as e:
                print(f"  [エラー] ルート切替失敗: {e}")

            for sc in SALES_CLASSES_ALL:
                # --- Disk Guard: 空き容量を毎ループチェック ---
                wait_for_disk_space(threshold_gb=3.5)
                
                pattern_count += 1
                
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_filename = f"【{amount}】{route}_{sc_fname}.csv"
                target_path = os.path.join(DOWNLOAD_DIR, target_filename)

                # 再開機能
                if os.path.exists(target_path):
                    skip_count += 1
                    success_count += 1
                    continue

                print(f"\n{'='*60}")
                print(f"[{pattern_count}/{total_expected}] 処理中: {target_filename}")
                print(f"{'='*60}")

                try:
                    set_quicksight_filter(driver, "販売区分", sc)
                    
                    # 計算・描画待ち
                    print("  データ計算待機 (8s)...")
                    time.sleep(8)

                    if export_csv(driver):
                        print(f"  ダウンロード完了を待機中 (保存先: {DOWNLOAD_DIR})...")
                        # ネットワークドライブ直書きの場合、ブラウザ完了 = ファイル存在確認となる
                        # タイムアウトを少し長めに設定(ネットワーク遅延対策)
                        timeout = 120 
                        start_time = time.time()
                        downloaded = False
                        
                        while time.time() - start_time < timeout:
                            if os.path.exists(target_path):
                                size_kb = os.path.getsize(target_path) / 1024
                                if size_kb > 10.0: # 最低限のサイズチェック
                                    downloaded = True
                                    break
                            time.sleep(2)
                        
                        if downloaded:
                            print(f"  ✓ 抽出成功: {target_filename} ({os.path.getsize(target_path)/1024:.1f} KB)")
                            success_count += 1
                        else:
                            print("  [警告] ファイルの書き出しが確認できませんでした。")
                            fail_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"  エラー: {e}")
                    fail_count += 1
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)

    print(f"\n{'='*60}")
    print(f"完了！ 成功(込スキップ): {success_count} / 失敗: {fail_count} / 合計: {total_expected}")
    driver.quit()

if __name__ == '__main__':
    main()
