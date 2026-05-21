import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

DOWNLOAD_DIR = r"C:\Users\00137012\Desktop\rpa_downloads"
X_DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

FILTER_INDEX = {
    "売上/粗利": 0,
    "支社": 1,
    "販売区分": 2,
    "ルート": 3,
}

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
        search_box.send_keys(Keys.ARROW_DOWN)
        time.sleep(1.0)
        search_box.send_keys(Keys.ENTER)
        time.sleep(2.0)
        return
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
    time.sleep(1.5)
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
    except:
        pass

def export_csv(driver):
    try:
        # We need to make sure we export the right table. The main table has many rows.
        # Let's find all tables and pick the largest one, or simply the one matching the general class.
        tables = driver.find_elements(By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]")
        if not tables:
            print("Table not found!")
            return False
            
        # Target the first visual (usually the main one)
        table = tables[0]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
        time.sleep(1)
        
        menu_btn = None
        for i in range(3):
            if i == 0:
                try:
                    ActionChains(driver).move_to_element(table).click().perform()
                except:
                    pass
            ActionChains(driver).move_to_element(table).perform()
            time.sleep(2)
            try:
                menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
                for btn in menu_btns:
                    if btn.is_displayed():
                        menu_btn = btn
                        break
                if menu_btn:
                    break
            except:
                pass
            ActionChains(driver).move_by_offset(-100, -100).perform()
            time.sleep(1)
        
        if not menu_btn:
             print("    [情報] メインメニューボタンが表示されませんでした。")
             return False

        ActionChains(driver).move_to_element(menu_btn).click().perform()
        time.sleep(2)

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

def rescue_data():
    print("【1ファイル限定抽出スクリプト: a-00 総販_100_総売上】")
    
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
        driver.quit()
        return

    # Delete existing bad file
    target_filename = "【売上】a-00 総販_100_総売上.csv"
    bad_file = os.path.join(X_DEST_DIR, target_filename)
    if os.path.exists(bad_file):
        os.remove(bad_file)
        print(f"古い破損ファイル {target_filename} を削除しました。")

    target_path = os.path.join(DOWNLOAD_DIR, target_filename)

    try:
        print("\n--- フィルター設定 ---")
        set_quicksight_filter(driver, "売上/粗利", "売上")
        set_quicksight_filter(driver, "ルート", "a-00 総販")
        set_quicksight_filter(driver, "販売区分", "100_総売上")
        
        print("  データ計算待機 (10s)...")
        time.sleep(10)

        res = export_csv(driver)
        if res:
            print(f"  ダウンロード完了を待機中 (保存先: {DOWNLOAD_DIR})...")
            start_time = time.time()
            
            while time.time() - start_time < 120:
                new_csvs = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))
                crdownloads = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
                
                if crdownloads:
                    pass
                elif new_csvs:
                    latest_file = max(new_csvs, key=os.path.getctime)
                    size_before = -1
                    retry_stable = 0
                    while retry_stable < 10:
                        size_now = os.path.getsize(latest_file)
                        if size_now == size_before and size_now > 0:
                            break
                        size_before = size_now
                        time.sleep(1)
                        retry_stable += 1
                    
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.rename(latest_file, target_path)
                    
                    import shutil
                    shutil.move(target_path, os.path.join(X_DEST_DIR, target_filename))
                    print(f"\n★ 復旧完了: {target_filename} が Xドライブに保存されました！")
                    break
                time.sleep(2)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    rescue_data()
