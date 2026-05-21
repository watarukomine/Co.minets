import os
import ctypes
import platform
import time
import glob
import shutil
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import zipfile

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
SALES_CLASSES_CORE = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", 
    "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", 
    "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", 
    "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]

# --- 詳細販売区分定義 (残り71件) ---
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
SALES_CLASSES_ALL = SALES_CLASSES_CORE + SALES_CLASSES_DETAIL

# --- 変更点：保存先をローカルCドライブにする ---
DOWNLOAD_DIR = r"C:\Users\00137012\Desktop\rpa_downloads"
# --- 追加：最終保存先をXドライブにする ---
X_DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
if not os.path.exists(X_DEST_DIR):
    os.makedirs(X_DEST_DIR)

# ==========================================
# ユーティリティ
# ==========================================

def get_free_space_gb(drive_name="C:"):
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        ctypes.c_wchar_p(f"{drive_name}\\"), None, None, ctypes.byref(free_bytes)
    )
    return free_bytes.value / (1024**3)

def wait_for_disk_space(threshold_gb=3.5):
    while True:
        free_gb = get_free_space_gb("C:")
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
        # ユーザーのアドバイス：矢印下キーを1回押すと選択肢がハイライト（グレー）になり、クリック可能になる
        search_box.send_keys(Keys.ARROW_DOWN)
        time.sleep(1.0)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2.0)
        return # キーボード操作で選択完了
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
        # 最後にESCAPEキーで閉じておく
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        raise Exception(f"選択肢「{target_value}」が見つかりません")

    ActionChains(driver).move_to_element(option).click().perform()
    time.sleep(1.5) # 選択後の反映待ち
    # もしメニューが残っていたら閉じる
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
    except:
        pass

def export_csv(driver):
    try:
        # 表（ビジュアル）を探してスクロール
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
        time.sleep(1)
        
        # ホバーを試行（メニューボタンが出るまで最大3回）
        menu_btn = None
        for i in range(3):
            # 表を一度クリックしてフォーカスを当てる（1回目のみ）
            if i == 0:
                try:
                    ActionChains(driver).move_to_element(table).click().perform()
                except:
                    pass
            
            # 表の右上にマウスを移動（メニューが出やすい場所）
            ActionChains(driver).move_to_element(table).perform()
            time.sleep(2)
            
            try:
                # メニューボタンを検索
                menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
                for btn in menu_btns:
                    if btn.is_displayed():
                        menu_btn = btn
                        break
                if menu_btn:
                    break
            except:
                pass
            
            # ダメなら一度別の場所（画面左上など）にマウスを逃がしてリトライ
            ActionChains(driver).move_by_offset(-100, -100).perform()
            time.sleep(1)
        
        if not menu_btn:
             print("    [情報] メインメニューボタンが表示されませんでした。実績0件の可能性があります。")
             return "ZERO_DATA"

        ActionChains(driver).move_to_element(menu_btn).click().perform()
        time.sleep(2)

        # CSVエクスポートボタンを探す
        csv_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'MuiMenuItem') and (contains(text(), 'CSV') or contains(text(), 'エクスポート'))]"))
        )
        ActionChains(driver).move_to_element(csv_btn).click().perform()
        
        print("    通知待ち: 「CSV の準備ができました。」を待機中...")
        try:
            toast = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'CSV の準備ができました')]"))
            )
            print("    ✓ 通知確認: QuickSight側の準備完了")
            
            try:
                close_btn = toast.find_element(By.XPATH, "./ancestor::div[contains(@class, 'notification')]//button")
                ActionChains(driver).move_to_element(close_btn).click().perform()
                time.sleep(1) 
            except:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                pass
                
            return True
        except TimeoutException:
            print("    [警告] 通知がタイムアウトしました。")
            return False

    except Exception as e:
        print(f"    [警告] エクスポート操作失敗: {e}")
        return False

# ==========================================
# メイン
# ==========================================

def main():
    print("【TMP-ONE データ抽出ループシステム (3日前の安定版復元・Cドライブ保存版)】")

    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--start-maximized")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR, 
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
                wait_for_disk_space(threshold_gb=3.5)
                pattern_count += 1
                
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_filename = f"【{amount}】{route}_{sc_fname}.csv"
                target_path = os.path.join(DOWNLOAD_DIR, target_filename)

                # Xドライブに既に存在するかチェック（CSVまたはZIP）
                final_path_csv = os.path.join(X_DEST_DIR, target_filename)
                final_path_zip = final_path_csv.replace(".csv", ".zip")
                
                final_path_zero = os.path.join(X_DEST_DIR, f"[ZERO_DATA]{target_filename}")
                
                if os.path.exists(final_path_csv) or os.path.exists(final_path_zip) or os.path.exists(final_path_zero):
                    status = "CSV" if os.path.exists(final_path_csv) else ("ZIP" if os.path.exists(final_path_zip) else "ZERO_DATA")
                    print(f"  [スキップ] 既にXドライブに存在します({status}): {target_filename}")
                    skip_count += 1
                    success_count += 1
                    continue

                print(f"\n{'='*60}")
                print(f"[{pattern_count}/{total_expected}] 処理中: {target_filename}")
                print(f"{'='*60}")

                try:
                    set_quicksight_filter(driver, "販売区分", sc)
                    print("  データ計算待機 (8s)...")
                    time.sleep(8)

                    res = export_csv(driver)
                    if res == True:
                        print(f"  ダウンロード完了を待機中 (保存先: {DOWNLOAD_DIR})...")
                        timeout = 120 
                        start_time = time.time()
                        downloaded = False
                        
                        while time.time() - start_time < timeout:
                            # 「日別実績_*.csv」または「*.crdownload」を探す
                            all_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
                            new_csvs = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))
                            crdownloads = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
                            
                            if crdownloads:
                                print(f"    [待機] ダウンロード進行中... ({len(crdownloads)}個の未完了ファイル)")
                            elif new_csvs:
                                # 最新のCSVを取得
                                latest_file = max(new_csvs, key=os.path.getctime)
                                print(f"    [発見] ターゲット候補: {os.path.basename(latest_file)}")
                                
                                # ダウンロード完了（ファイルサイズが安定）を待つ
                                size_before = -1
                                retry_stable = 0
                                while retry_stable < 10:
                                    size_now = os.path.getsize(latest_file)
                                    if size_now == size_before and size_now > 0:
                                        break
                                    size_before = size_now
                                    time.sleep(1)
                                    retry_stable += 1
                                
                                # 正式な名前にリネームして移動
                                try:
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    os.rename(latest_file, target_path)
                                    
                                    # --- 修正：ZIP圧縮してXドライブへ移動 ---
                                    zip_path = target_path.replace(".csv", ".zip")
                                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                                        zf.write(target_path, arcname=target_filename)
                                    
                                    # 元のCSVは削除してCドライブを空ける
                                    os.remove(target_path)
                                    
                                    # ZIPをXドライブへ移動
                                    shutil.move(zip_path, final_path_zip)
                                    print(f"  ✓ ZIP圧縮してXドライブへ移動完了: {os.path.basename(final_path_zip)}")
                                    
                                    downloaded = True
                                    break
                                except Exception as e:
                                    print(f"    [警告] リネーム/圧縮/移動失敗: {e}")
                                    break
                            else:
                                if int(time.time() - start_time) % 10 == 0:
                                    print(f"    ...待機中 ({int(time.time() - start_time)}s経過 / フォルダ内総数: {len(all_files)}個)")
                            
                            time.sleep(2)
                        
                        else:
                            print("  [警告] ファイルの書き出しが確認できませんでした。")
                            fail_count += 1
                    elif res == "ZERO_DATA":
                        print(f"  [情報] 実績0件と判定しました。マーカーファイルを作成します。")
                        with open(final_path_zero, 'w', encoding='utf-8') as f:
                            f.write(f"Zero data detected at {datetime.now().isoformat()}")
                        success_count += 1
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
