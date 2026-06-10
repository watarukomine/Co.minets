# -*- coding: utf-8 -*-
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import zipfile
import json
import io
import csv

# プロキシ自動バイパス
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import sys as _sys
        _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
        _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8')

def safe_x_drive_op(op_func, *args, retries=5, delay=3, **kwargs):
    for i in range(retries):
        try:
            return op_func(*args, **kwargs)
        except OSError as e:
            print(f"    [WARNING] Xドライブ操作失敗 (試行 {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

# ==========================================
# 抽出パターンの定義
# ==========================================
AMOUNT_TYPES = ["売上", "粗利"]
BRANCH = "すべて"

ROUTES_CORE = ["a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス", "c-01 卸売", "c-02 直売", "d-01 部品商"]
ROUTES_DETAIL = ["d-02 その他再販業者", "d-03 修理業者", "d-04 GSS", "d-05 用品小売り店", "d-06 その他", "e-01 修理工場", "e-02 特定修理業者", "e-03 大口ユーザー"]
ROUTES_ALL = ROUTES_CORE + ROUTES_DETAIL

SALES_CLASSES_CORE = [
    "100_総売上", "110_総売上（除通信事業）", "200_重点商品", "210_特販部品", "212_競争品", "213_クリーンエアフィルター", 
    "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", 
    "244_ケミカル", "300_一般部品", "310_外装部品", "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"
]
SALES_CLASSES_DETAIL = [
    "211_特販6品目", "214_特販部品その他", "223_レクサスセット", "224_タイヤその他", "231_ACデルコ", "232_パナソニック", 
    "233_GSユアサ", "234_レクサスバッテリー", "235_地場バッテリー", "236_地場パナソニック", "237_地場GSユアサ", 
    "238_パナソニック（本部＋地場）", "239_GSユアサ（本部＋地場）", "241_エンジンオイル", "242_シャシオイル", 
    "243_フルード", "245_礦油その他", "320_機能部品", "410_ナビ", "411_T-Connect対応ナビ", "412_ベーシックナビ", 
    "413_エントリーナビ", "414_ナビキット", "415_T-Connectナビキット", "416_エントリーナビキット", "417_本部扱いナビ", 
    "418_ナビその他", "420_ナビ関連オプション", "421_後席ディスプレイ", "422_モニターカメラ類", "423_地図ソフト", 
    "424_ドライブレコーダー", "425_純正ドライブレコーダー", "426_本部調達ドライブレコーダー", "427_その他ドライブレコーダー", 
    "428_ナビ関連オプションその他", "430_オーディオ", "440_ITS関連商品", "450_ベーシック推奨用品", "460_オプション推販用品", 
    "461_後付け安全4商品", "462_TRD", "463_モデリスタ", "464_オプション推販用品その他", "470_レクサス用品", "480_用品その他", 
    "500_その他", "510_通信事業", "521_本部調達工具", "522_地場工具", "530_C＋WALK（本体）", "540_本部商品その他", 
    "550_新車カタログ", "560_その他（その他）", "901_プレミアムCAF", "902_パナソニックバッテリー（本部＋地場）", 
    "903_GSユアサバッテリー（本部＋地場）", "904_ブレーキフルード", "905_LLC", "907_純正ETC2.0", "907_純正ETC", 
    "909_TCD用品", "910_トヨタ車TRD", "911_レクサス車TRD", "912_トヨタ車モデリスタ", "913_レクサス車モデリスタ", 
    "914_TMP用品", "915_TZ用品", "916_TMP車種専用品", "917_夏タイヤ", "918_冬タイヤ"
]
SALES_CLASSES_ALL = SALES_CLASSES_CORE + SALES_CLASSES_DETAIL

EXCLUDE_COMBINATIONS = []
exclude_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "always_zero_combinations.json")
if os.path.exists(exclude_json_path):
    try:
        with open(exclude_json_path, 'r', encoding='utf-8') as f:
            exclude_data = json.load(f)
            EXCLUDE_COMBINATIONS = [(item['route'], item['sales_class']) for item in exclude_data]
            print(f"  [情報] always_zero_combinations.json から {len(EXCLUDE_COMBINATIONS)} 件の除外組み合わせをロードしました。")
    except Exception as e:
        print(f"  [警告] always_zero_combinations.json のロードに失敗しました: {e}")

# 保存先設定
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "rpa_downloads_temp")
X_DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data_temp"
X_FINAL_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
if not os.path.exists(X_DEST_DIR):
    os.makedirs(X_DEST_DIR)
if not os.path.exists(X_FINAL_DIR):
    os.makedirs(X_FINAL_DIR)

def get_free_space_gb(drive_name="C:"):
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(f"{drive_name}\\"), None, None, ctypes.byref(free_bytes))
    return free_bytes.value / (1024**3)

def wait_for_disk_space(threshold_gb=3.5):
    while True:
        free_gb = get_free_space_gb("C:")
        if free_gb >= threshold_gb:
            break
        print(f"\n[！警告！] Cドライブの空き容量が不足しています ({free_gb:.2f} GB)")
        print("空きができるまで待機中...")
        time.sleep(30)

def wait_for_data_load(driver, old_table=None, timeout=15):
    start_time = time.time()
    if old_table:
        try:
            WebDriverWait(driver, 5).until(EC.staleness_of(old_table))
        except:
            pass

    check_zero_data_js = """
    function hasZeroDataText(root) {
        const targets = [
            '表示するデータはありません', '表示するデータがありません', '表示データはありません', '表示データがありません',
            'データがありません', 'データはありません', 'データ無し', 'データなし', 'ビジュアルのデータが見つかりません',
            'データが見つかりません', 'No data'
        ];
        let found = false;
        const walk = n => {
            if(!n || found) return;
            let t = '';
            try {
                t = (n.nodeType === 3 ? n.textContent : (n.nodeType === 1 ? (n.innerText || '') : '')).trim();
                if (t) {
                    for (let target of targets) {
                        if (t.includes(target)) {
                            if (n.nodeType === 3 || n.children.length === 0) {
                                found = true;
                                return;
                            }
                        }
                    }
                }
            } catch(e) {}
            if(n.shadowRoot) walk(n.shadowRoot);
            let c = n.firstChild;
            while(c) { walk(c); c = c.nextSibling; }
        };
        walk(root);
        return found;
    }
    return hasZeroDataText(document.body);
    """

    while time.time() - start_time < timeout:
        try:
            if driver.execute_script(check_zero_data_js):
                # 一時的なプレースホルダー表示（ロード中）かを確認するため、2.5秒待って再検知を試みる
                time.sleep(2.5)
                if driver.execute_script(check_zero_data_js):
                    return "ZERO_DATA"
            menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
            for btn in menu_btns:
                if btn.is_displayed():
                    return "DATA_PRESENT"
        except:
            pass
        time.sleep(0.5)
    return "TIMEOUT"

def filter_recovery_decorator(func):
    def wrapper(driver, filter_name, target_value):
        try:
            return func(driver, filter_name, target_value)
        except Exception as e:
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                from selenium.webdriver.common.keys import Keys
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            time.sleep(1.0)
            raise e
    return wrapper

@filter_recovery_decorator
def set_quicksight_filter(driver, filter_name, target_value):
    print(f"  [{filter_name}] → 「{target_value}」")
    try:
        if driver.find_elements(By.XPATH, "//*[@role='option']"):
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1.0)
    except:
        pass
    find_combobox_js = """
    const findComboboxByLabel = (labelText) => {
        const walk = (n) => {
            if (!n) return null;
            if (n.classList && n.classList.contains('quicksight-parameter-control')) {
                const findLabel = (node) => {
                    if (!node) return false;
                    let txt = '';
                    try { txt = (node.nodeType === 3 ? node.textContent : (node.nodeType === 1 ? (node.innerText || '') : '')).trim(); } catch(e) {}
                    if (txt === labelText || txt.includes(labelText)) return true;
                    if (node.shadowRoot) { if (findLabel(node.shadowRoot)) return true; }
                    let c = node.firstChild;
                    while (c) { if (findLabel(c)) return true; c = c.nextSibling; }
                    return false;
                };
                if (findLabel(n)) {
                    const findCombo = (node) => {
                        if (!node) return null;
                        if (node.getAttribute && node.getAttribute('data-automation-id') === 'sheet_control_value') return node;
                        if (node.shadowRoot) { const r = findCombo(node.shadowRoot); if (r) return r; }
                        let c = node.firstChild;
                        while (c) { const r = findCombo(c); if (r) return r; c = c.nextSibling; }
                        return null;
                    };
                    return findCombo(n);
                }
            }
            if (n.shadowRoot) { const r = walk(n.shadowRoot); if (r) return r; }
            let c = n.firstChild;
            while (c) { const r = walk(c); if (r) return r; c = c.nextSibling; }
            return null;
        };
        return walk(document.body);
    };
    return findComboboxByLabel(arguments[0]);
    """
    combobox = None
    try:
        combobox = driver.execute_script(find_combobox_js, filter_name)
    except:
        pass

    if not combobox:
        CORRECTED_INDEX = {"売上/粗利": 0, "支社": 1, "販売区分": 2, "ルート": 3}
        idx = CORRECTED_INDEX.get(filter_name)
        comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
        if len(comboboxes) <= idx:
            raise Exception(f"combobox for {filter_name} not found")
        combobox = comboboxes[idx]

    find_arrow_js = """
    const findArrowInsideCombobox = (combobox) => {
        if (!combobox) return null;
        const isMenuOption = (el) => {
            let curr = el;
            while (curr && curr !== document.body) {
                const label = curr.getAttribute ? curr.getAttribute('aria-label') : '';
                if (label && (label.includes('メニュー') || label.includes('menu') || label.includes('Menu'))) return true;
                curr = curr.parentNode;
            }
            return false;
        };
        const walk = (n) => {
            if (!n) return null;
            if (isMenuOption(n)) return null;
            const tagName = (n.tagName || '').toLowerCase();
            const className = (n.className && typeof n.className === 'string') ? n.className : '';
            const role = n.getAttribute ? n.getAttribute('role') : '';
            if (className.includes('MuiSelect-icon') || className.includes('arrow') || className.includes('Indicator') || className.includes('caret') || (role === 'button' && className.includes('icon'))) {
                return n;
            }
            if (tagName === 'svg') return n;
            if (n.shadowRoot) { const r = walk(n.shadowRoot); if (r) return r; }
            let c = n.firstChild;
            while (c) { const r = walk(c); if (r) return r; c = c.nextSibling; }
            return null;
        };
        let arrow = walk(combobox);
        if (arrow) return arrow;
        if (combobox.parentNode) {
            arrow = walk(combobox.parentNode);
            if (arrow) return arrow;
        }
        return null;
    };
    return findArrowInsideCombobox(arguments[0]);
    """
    arrow = None
    try:
        arrow = driver.execute_script(find_arrow_js, combobox)
    except:
        pass
        
    click_target = arrow if arrow else combobox

    open_dropdown_js = """
    const combobox = arguments[0];
    const arrow = arguments[1];
    const triggerEvents = (el) => {
        if (!el) return;
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
        el.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
    };
    if (arrow) { triggerEvents(arrow); if (arrow.parentNode) triggerEvents(arrow.parentNode); }
    triggerEvents(combobox);
    return true;
    """

    for attempt in range(3):
        try:
            driver.execute_script(open_dropdown_js, combobox, arrow)
            time.sleep(2.5)
            break
        except Exception:
            try:
                ActionChains(driver).move_to_element(click_target).click().perform()
                time.sleep(2.5)
                break
            except StaleElementReferenceException:
                if attempt == 2: raise
                time.sleep(1)

    search_box = None
    try:
        search_box = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='値を検索']")))
    except:
        pass

    if search_box and target_value not in ["すべて", "すべての支社"]:
        try:
            search_box.send_keys(Keys.CONTROL, "a")
            search_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            search_term = target_value.split("_")[0] + "_" if "_" in target_value else target_value
            print(f"    検索ワード入力: 「{search_term}」")
            search_box.send_keys(search_term)
            time.sleep(5.0)
            # 選択肢が表示されるまでポーリング（最大15秒追加）
            poll_start = time.time()
            while time.time() - poll_start < 15:
                try:
                    options = driver.find_elements(By.XPATH, "//*[@role='option']")
                    matching = [o for o in options if target_value in (o.text or '') or target_value in (o.get_attribute('aria-label') or '')]
                    if matching:
                        print(f"    ✓ 検索結果に「{target_value}」の選択肢を検出")
                        break
                    # 選択肢は表示されているが一致するものがない場合、もう少し待つ
                    if len(options) > 0:
                        time.sleep(1.0)
                    else:
                        time.sleep(1.5)
                except:
                    time.sleep(1.0)
            else:
                print(f"    [警告] 検索結果のポーリングがタイムアウト。選択肢が見つかりませんでした。再入力を試行します...")
                # 再入力を試行
                try:
                    search_box.send_keys(Keys.CONTROL, "a")
                    search_box.send_keys(Keys.BACKSPACE)
                    time.sleep(1.0)
                    search_box.send_keys(search_term)
                    time.sleep(8.0)
                except:
                    pass
        except Exception as e:
            print(f"    [警告] 検索ボックス入力失敗: {e}")

    select_option_js = """
    const targetText = arguments[0];
    const isMatch = (text, ariaLabel, target) => {
        text = (text || '').trim();
        ariaLabel = (ariaLabel || '').trim();
        if (target === 'すべて' || target === 'すべての支社') {
            const allTerms = ['すべて', 'すべての支社', 'すべてを選択', '(すべて選択)', '(すべて)', 'All', 'Select all'];
            return allTerms.some(term => text.includes(term) || ariaLabel.includes(term));
        }
        return text === target || text.includes(target) || ariaLabel.includes(target);
    };

    const items = Array.from(document.querySelectorAll('[role="option"], .MuiMenuItem-root, [class*="MenuItem"]'));
    let targetOption = null;
    for (const item of items) {
        if (isMatch(item.innerText, item.getAttribute('aria-label'), targetText)) {
            targetOption = item;
            break;
        }
    }
    if (!targetOption) return { success: false, reason: 'Option not found' };

    const isSelected = (el) => {
        if (el.getAttribute('aria-selected') === 'true') return true;
        if (el.getAttribute('aria-checked') === 'true') return true;
        if (el.classList.contains('Mui-selected')) return true;
        const checkbox = el.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) return true;
        return false;
    };

    const alreadyChecked = isSelected(targetOption);
    if (!alreadyChecked) {
        targetOption.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
        targetOption.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
    }

    let applyClicked = false;
    const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
    for (const btn of buttons) {
        const text = (btn.innerText || '').trim();
        if (text === '適用' || text === 'Apply') {
            btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window }));
            btn.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
            applyClicked = true;
            break;
        }
    }
    return { success: true, clicked: !alreadyChecked, alreadyChecked: alreadyChecked, applyClicked: applyClicked };
    """

    res = {"success": False}
    try:
        res = driver.execute_script(select_option_js, target_value)
    except:
        pass

    if res.get("success"):
        time.sleep(2.0)
    else:
        # Fallback to standard click
        option = None
        try:
            option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[@role='option' and (contains(@aria-label, '{target_value}') or contains(text(), '{target_value}'))]"))
            )
        except:
            pass

        if option is None:
            if search_box:
                try:
                    search_box.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1.0)
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2.0)
                    return
                except:
                    pass
            try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except: pass
            raise Exception(f"選択肢「{target_value}」が見つかりません")

        ActionChains(driver).move_to_element(option).click().perform()
        time.sleep(1.5)
        try:
            apply_btn = driver.find_element(By.XPATH, "//button[text()='適用' or text()='Apply']")
            if apply_btn.is_displayed():
                apply_btn.click()
                time.sleep(1.5)
        except:
            pass

    try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

def export_csv(driver):
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
        time.sleep(1)

        menu_btn = None
        for i in range(3):
            try:
                ActionChains(driver).move_to_element_with_offset(table, 10, 10).perform()
                time.sleep(2)
                menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
                for btn in menu_btns:
                    if btn.is_displayed():
                        menu_btn = btn
                        break
                if menu_btn: break
            except:
                pass
            time.sleep(1)
        
        if not menu_btn:
             print("    [情報] メニューボタンが表示されません。実績0件とみなします。")
             return "ZERO_DATA"

        ActionChains(driver).move_to_element(menu_btn).click().perform()
        time.sleep(2)

        csv_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'MuiMenuItem') and (contains(text(), 'CSV') or contains(text(), 'エクスポート'))]"))
        )
        ActionChains(driver).move_to_element(csv_btn).click().perform()
        
        print("    通知待ち: 「CSV の準備ができました。」を待機中...")
        toast = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'CSV の準備ができました')]"))
        )
        print("    ✓ 通知確認: QuickSight側の準備完了")
        try:
            close_btn = toast.find_element(By.XPATH, "./ancestor::div[contains(@class, 'notification')]//button")
            ActionChains(driver).move_to_element(close_btn).click().perform()
        except:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        return True
    except Exception as e:
        print(f"    [警告] エクスポート操作失敗: {e}")
        return False

def validate_downloaded_csv(filepath):
    """過去実績データ復旧用バリデーション：過去(2026/03以前)と最新(2026/05以降)の両方のデータが含まれているか確認"""
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            row_count = 0
            has_past = False
            has_recent = False
            for row in reader:
                row_count += 1
                date_str = row.get('日付', '')
                if not date_str:
                    continue
                d = date_str.split(' ')[0].replace('/', '-')
                parts = d.split('-')
                if len(parts) >= 2 and parts[0].isdigit():
                    yr = int(parts[0])
                    mo = int(parts[1])
                    if yr < 2026 or (yr == 2026 and mo <= 3):
                        has_past = True
                    if yr == 2026 and mo >= 5:
                        has_recent = True
            if row_count == 0:
                print("    [警告] CSVの中身が空です（ヘッダーのみ）。")
                return False
            if has_past and has_recent:
                return True
    except Exception as e:
        print(f"    [警告] CSVバリデーション実行エラー: {e}")
        return False
    
    print(f"    [警告] CSV内に対象データが見つかりませんでした。過去分検出: {has_past}, 最新分検出: {has_recent}")
    return False

def main():
    print("【TMP-ONE 過去実績データ差分 復旧専用RPA抽出システム】")

    missing_set = None
    missing_patterns_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "missing_patterns.json")
    if os.path.exists(missing_patterns_json):
        try:
            with open(missing_patterns_json, "r", encoding="utf-8") as f:
                missing_data = json.load(f)
                missing_set = set((item["amount"], item["route"], item["sales_class"]) for item in missing_data)
                print(f"  [設定] 不足データリストから {len(missing_set)} 件の復旧指示をロードしました。")
        except Exception as e:
            print(f"  [警告] missing_patterns.json のロードに失敗しました: {e}")

    if missing_set is None:
        print("  [情報] missing_patterns.json が見つからないため、全 2,700 パターンの全件抽出を実行します。")

    edge_options = Options()
    edge_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=edge_options)
    
    try:
        driver.maximize_window()
        time.sleep(1)
    except:
        pass
    
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": DOWNLOAD_DIR
    })

    print("Edgeに接続しました。QuickSightダッシュボードを検索中...")
    found = False
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if "コントロール" in driver.execute_script("return document.body.innerText"):
                    found = True
                    break
                driver.switch_to.default_content()
            except:
                pass
        if found: break
            
    if not found:
        print("[エラー] QuickSightダッシュボードを開いているタブが見つかりませんでした。")
        sys.exit(1)
        
    print("★ iframe接続成功。支社フィルターを「すべて」に設定します...")
    try:
        set_quicksight_filter(driver, "支社", "すべて")
        print("  ✓ 支社フィルターを「すべて」に設定完了")
    except Exception as e:
        print(f"  [警告] 支社フィルター設定失敗: {e}")

    total_expected = len(missing_set) if missing_set is not None else len(AMOUNT_TYPES) * len(ROUTES_ALL) * len(SALES_CLASSES_ALL)
    pattern_count = 0
    success_count = 0
    skip_count = 0
    fail_count = 0
    failed_patterns = []

    for amount in AMOUNT_TYPES:
        amount_changed = False
        has_missing_in_amount = any(m[0] == amount for m in missing_set) if missing_set is not None else True
        if not has_missing_in_amount:
            continue
            
        try:
            set_quicksight_filter(driver, "売上/粗利", amount)
            amount_changed = True
        except Exception as e:
            print(f"  [エラー] 金額種別切替失敗: {e}")
            try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except: pass
            time.sleep(1.0)

        for route in ROUTES_ALL:
            route_changed = False
            has_missing_in_route = any(m[0] == amount and m[1] == route for m in missing_set) if missing_set is not None else True
            if not has_missing_in_route:
                continue

            if amount_changed:
                try:
                    set_quicksight_filter(driver, "ルート", route)
                    route_changed = True
                except Exception as e:
                    print(f"  [エラー] ルート切替失敗: {e}")
                    try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except: pass
                    time.sleep(1.0)

            for sc in SALES_CLASSES_ALL:
                if missing_set is not None and (amount, route, sc) not in missing_set:
                    continue

                wait_for_disk_space(threshold_gb=3.5)
                pattern_count += 1
                
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_filename = f"【{amount}】{route}_{sc_fname}.csv"
                target_path = os.path.join(DOWNLOAD_DIR, target_filename)

                # スキップ判定 (一時保存先フォルダに既に存在する場合のみスキップ可能にする)
                final_path_csv = os.path.join(X_DEST_DIR, target_filename)
                final_path_zip = final_path_csv.replace(".csv", ".zip")
                final_path_zero = os.path.join(X_DEST_DIR, f"[ZERO_DATA]{target_filename}")
                
                if (route, sc) in EXCLUDE_COMBINATIONS:
                    print(f"  [除外スキップ] 常にデータなしとなる組み合わせのためスキップ: {route} - {sc}")
                    if not safe_x_drive_op(os.path.exists, final_path_zero):
                        try:
                            def _write_zero():
                                with open(final_path_zero, 'w', encoding='utf-8') as f:
                                    f.write(f"Zero data (statically excluded) at {datetime.now().isoformat()}")
                            safe_x_drive_op(_write_zero)
                        except: pass
                    skip_count += 1
                    success_count += 1
                    continue

                # 注意: 最終フォルダ (X_FINAL_DIR) にある ZIP は不完全（過去データが無い）なため、
                # 最終フォルダの存在有無チェックによるスキップはすべて排除し、一時フォルダのみチェックする
                if safe_x_drive_op(os.path.exists, final_path_csv) or safe_x_drive_op(os.path.exists, final_path_zip) or safe_x_drive_op(os.path.exists, final_path_zero):
                    print(f"  [スキップ] 既に一時フォルダに存在します: {target_filename}")
                    skip_count += 1
                    success_count += 1
                    continue

                if not (amount_changed and route_changed):
                    print(f"  [エラースキップ] フィルター切り替えに失敗しているため、抽出をスキップします: {target_filename}")
                    fail_count += 1
                    failed_patterns.append({"pattern": target_filename, "reason": "フィルター切り替え失敗のため安全にスキップ"})
                    continue

                print(f"\n{'='*60}")
                print(f"[{pattern_count}/{total_expected}] 復旧中: {target_filename}")
                print(f"{'='*60}")

                try:
                    old_table = None
                    try: old_table = driver.find_element(By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]")
                    except: pass

                    max_retries = 3
                    retry_count = 0
                    load_status = "TIMEOUT"
                    
                    while retry_count <= max_retries:
                        set_quicksight_filter(driver, "販売区分", sc)
                        print("  データロード待機中...")
                        load_status = wait_for_data_load(driver, old_table=old_table, timeout=15)
                        
                        if load_status == "ZERO_DATA":
                            is_must_have_data = (route == "a-00") or ("a-00" in route) or (route == "すべて")
                            if is_must_have_data and retry_count < max_retries:
                                retry_count += 1
                                print(f"  [警告] 主要ルート「{route}」で「データなし」を誤検出した可能性があります。ロード遅延とみなして 10 秒待機後にリトライします ({retry_count}/{max_retries})...")
                                time.sleep(10)
                                try: old_table = driver.find_element(By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]")
                                except: pass
                                continue
                        break

                    if load_status == "ZERO_DATA":
                        print("  [情報] 画面に「データなし」を検出。ゼロ実績として処理します。")
                        try:
                            def _write_ui_zero():
                                with open(final_path_zero, 'w', encoding='utf-8') as f:
                                    f.write(f"Zero data (detected on UI) at {datetime.now().isoformat()}")
                            safe_x_drive_op(_write_ui_zero)
                        except: pass
                        success_count += 1
                        continue

                    res = export_csv(driver)
                    if res == True:
                        print(f"  ダウンロード完了を待機中...")
                        timeout = 120 
                        start_time = time.time()
                        downloaded = False
                        
                        while time.time() - start_time < timeout:
                            new_csvs = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))
                            crdownloads = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
                            
                            if crdownloads:
                                pass
                            elif new_csvs:
                                latest_file = max(new_csvs, key=os.path.getctime)
                                print(f"    [発見] ターゲット候補: {os.path.basename(latest_file)}")
                                
                                size_before = -1
                                retry_stable = 0
                                while retry_stable < 10:
                                    size_now = os.path.getsize(latest_file)
                                    if size_now == size_before and size_now > 0:
                                        break
                                    size_before = size_now
                                    time.sleep(1)
                                    retry_stable += 1
                                
                                try:
                                    # 過去データ有無のバリデーション
                                    if not validate_downloaded_csv(latest_file):
                                        print("    [ERROR] ダウンロードされたCSVに過去実績(2026/03以前)が含まれていません。")
                                        if os.path.exists(latest_file):
                                            os.remove(latest_file)
                                        break
                                    
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    os.rename(latest_file, target_path)
                                    
                                    # ZIP圧縮して一時保存先へ移動
                                    zip_path = target_path.replace(".csv", ".zip")
                                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                                        zf.write(target_path, arcname=target_filename)
                                    
                                    os.remove(target_path)
                                    safe_x_drive_op(shutil.move, zip_path, final_path_zip)
                                    print(f"  ✓ 一時保存先へ移動完了: {os.path.basename(final_path_zip)}")
                                    
                                    downloaded = True
                                    break
                                except Exception as e:
                                    print(f"    [警告] 移動/圧縮失敗: {e}")
                                    break
                            
                            time.sleep(2)
                        
                        if not downloaded:
                            fail_count += 1
                            failed_patterns.append({"pattern": target_filename, "reason": "ダウンロードタイムアウトまたはバリデーション失敗"})
                        else:
                            success_count += 1
                    elif res == "ZERO_DATA":
                        print(f"  [情報] 実績0件と判定しました。")
                        def _write_ui_zero_alt():
                            with open(final_path_zero, 'w', encoding='utf-8') as f:
                                f.write(f"Zero data at {datetime.now().isoformat()}")
                        safe_x_drive_op(_write_ui_zero_alt)
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_patterns.append({"pattern": target_filename, "reason": "エクスポートボタン等のクリック失敗"})
                except Exception as e:
                    print(f"  エラー: {e}")
                    fail_count += 1
                    failed_patterns.append({"pattern": target_filename, "reason": f"例外エラー: {e}"})
                    try: ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except: pass
                    time.sleep(1)

    print(f"\n{'='*60}")
    print(f"完了！ 成功(込スキップ): {success_count} / 失敗: {fail_count} / 合計: {total_expected}")
    driver.quit()

if __name__ == '__main__':
    main()
