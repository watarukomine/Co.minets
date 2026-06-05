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

# プロキシ自動バイパス
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for python versions that don't support reconfigure
        import sys as _sys
        _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
        _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8')

def safe_x_drive_op(op_func, *args, retries=5, delay=3, **kwargs):
    """Xドライブ（共有ネットワークドライブ）の接続一時切断(WinError 1237等)に対応するリトライラッパー"""
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

# --- 常に実績0件（データなし）となる除外パターンのロード ---
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

if not EXCLUDE_COMBINATIONS:
    # フォールバック用ハードコードリスト
    EXCLUDE_COMBINATIONS = [
        ("b-03 ジェームス", "245_礦油その他"),
        ("b-03 ジェームス", "321_S部品"),
        ("b-03 ジェームス", "415_T-Connectナビキット"),
        ("b-03 ジェームス", "427_その他ドライブレコーダー"),
        ("c-01 卸売", "550_新車カタログ"),
        ("c-02 直売", "480_用品その他"),
        ("d-02 その他再販業者", "233_GSユアサ"),
        ("d-02 その他再販業者", "415_T-Connectナビキット"),
        ("d-03 修理業者", "550_新車カタログ"),
        ("d-04 GSS", "415_T-Connectナビキット"),
        ("d-05 用品小売り店", "321_S部品"),
        ("d-05 用品小売り店", "480_用品その他"),
        ("d-06 その他", "480_用品その他"),
        ("e-01 修理工場", "480_用品その他"),
        ("e-01 修理工場", "530_C＋WALK（本体）"),
        ("e-02 特定修理業者", "417_本部扱いナビ"),
        ("e-02 特定修理業者", "911_レクサス車TRD"),
        ("e-02 特定修理業者", "913_レクサス車モデリスタ"),
        ("e-03 大口ユーザー", "415_T-Connectナビキット"),
        ("e-03 大口ユーザー", "550_新車カタログ"),
    ]


# --- 保存先（月次一時用） ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "rpa_downloads_temp")
X_DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data_temp"
X_FINAL_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
if not os.path.exists(X_DEST_DIR):
    os.makedirs(X_DEST_DIR)
if not os.path.exists(X_FINAL_DIR):
    os.makedirs(X_FINAL_DIR)

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

def check_already_extracted_in_dest(dest_zip_path, target_year, target_month):
    """
    最終保存先のZIPファイル内のCSVを読み込み、指定された対象年月(YYYY-MM)のデータが既に存在するかチェックする
    """
    if not os.path.exists(dest_zip_path):
        return False
        
    target_prefix = f"{target_year:04d}-{target_month:02d}-"
    target_prefix_slash = f"{target_year:04d}/{target_month:02d}/"
    
    try:
        with zipfile.ZipFile(dest_zip_path, 'r') as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                content = f.read().decode('utf-8-sig')
                if target_prefix in content or target_prefix_slash in content:
                    return True
    except Exception as e:
        print(f"    [警告] ZIPファイル {os.path.basename(dest_zip_path)} の中身チェック中にエラーが発生しました: {e}")
        
    return False

def wait_for_data_load(driver, old_table=None, timeout=15):
    """
    フィルター適用後、データがロードされるのを待機する。
    データなしメッセージが検出された場合は 'ZERO_DATA' を返し、
    テーブルデータが正常に表示された場合は 'DATA_PRESENT' を返す。
    タイムアウトした場合は 'TIMEOUT' を返す。
    """
    start_time = time.time()
    
    # 1. 旧テーブルが指定されている場合、それがStale（DOMから離脱）するのを待つ
    if old_table:
        try:
            # ページ遷移・ロードが始まるまでに少しラグがあるため、
            # 最大5秒間、旧テーブルが無効（stale）になるのを待機する
            WebDriverWait(driver, 5).until(EC.staleness_of(old_table))
            print("    [情報] 旧テーブル要素の消失（リロード開始）を確認しました。")
        except TimeoutException:
            # タイムアウトした場合は、すでにロード完了しているか、データ変更がなく更新が発生しなかったとみなす
            print("    [情報] 旧テーブル要素の消失が確認できませんでした（更新なし、またはすでに完了）。")
        except Exception as e:
            print(f"    [情報] 旧テーブル要素の監視中に例外が発生しました（無視して進みます）: {e}")

    # Shadow DOMも含めてページ全体から「データなし」系の文言を検索するJS
    check_zero_data_js = """
    function hasZeroDataText(root) {
        const targets = [
            '表示するデータはありません',
            '表示するデータがありません',
            '表示データはありません',
            '表示データがありません',
            'データがありません',
            'データはありません',
            'データ無し',
            'データなし',
            'ビジュアルのデータが見つかりません',
            'データが見つかりません',
            'No data'
        ];
        let found = false;
        const walk = n => {
            if(!n || found) return;
            let t = '';
            try {
                t = (n.nodeType === 3 ? n.textContent : (n.nodeType === 1 ? (n.innerText || '') : ''));
                if (t) {
                    t = t.trim();
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
            while(c) {
                walk(c);
                c = c.nextSibling;
            }
        };
        walk(root);
        return found;
    }
    return hasZeroDataText(document.body);
    """

    while time.time() - start_time < timeout:
        try:
            # 1. 「データなし」メッセージの検出 (Shadow DOM対応)
            is_zero = driver.execute_script(check_zero_data_js)
            if is_zero:
                return "ZERO_DATA"
                
            # 2. メニューオプションボタンがすでに見える状態かチェック
            menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
            for btn in menu_btns:
                if btn.is_displayed():
                    return "DATA_PRESENT"
        except Exception:
            pass
        time.sleep(0.5)
    return "TIMEOUT"


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
    
    # 1. Find the combobox dynamically using JS to penetrate Shadow DOMs
    find_combobox_js = """
    const findComboboxByLabel = (labelText) => {
        const walk = (n) => {
            if (!n) return null;
            if (n.classList && n.classList.contains('quicksight-parameter-control')) {
                const findLabel = (node) => {
                    if (!node) return false;
                    let txt = '';
                    try {
                        txt = (node.nodeType === 3 ? node.textContent : (node.nodeType === 1 ? (node.innerText || '') : '')).trim();
                    } catch(e) {}
                    if (txt === labelText || txt.includes(labelText)) return true;
                    if (node.shadowRoot) {
                        if (findLabel(node.shadowRoot)) return true;
                    }
                    let c = node.firstChild;
                    while (c) {
                        if (findLabel(c)) return true;
                        c = c.nextSibling;
                    }
                    return false;
                };
                if (findLabel(n)) {
                    const findCombo = (node) => {
                        if (!node) return null;
                        if (node.getAttribute && node.getAttribute('data-automation-id') === 'sheet_control_value') return node;
                        if (node.shadowRoot) {
                            const r = findCombo(node.shadowRoot);
                            if (r) return r;
                        }
                        let c = node.firstChild;
                        while (c) {
                            const r = findCombo(c);
                            if (r) return r;
                            c = c.nextSibling;
                        }
                        return null;
                    };
                    return findCombo(n);
                }
            }
            if (n.shadowRoot) {
                const r = walk(n.shadowRoot);
                if (r) return r;
            }
            let c = n.firstChild;
            while (c) {
                const r = walk(c);
                if (r) return r;
                c = c.nextSibling;
            }
            return null;
        };
        return walk(document.body);
    };
    return findComboboxByLabel(arguments[0]);
    """
    
    combobox = None
    try:
        combobox = driver.execute_script(find_combobox_js, filter_name)
    except Exception as e:
        print(f"    [警告] JSによるコンボボックス検索エラー: {e}")

    if not combobox:
        # Fallback to corrected hardcoded index from our diagnostics
        # Index 0: 売上/粗利
        # Index 1: 支社
        # Index 2: 販売区分
        # Index 3: ルート
        CORRECTED_INDEX = {
            "売上/粗利": 0,
            "支社": 1,
            "販売区分": 2,
            "ルート": 3,
        }
        idx = CORRECTED_INDEX.get(filter_name)
        comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
        if len(comboboxes) <= idx:
            raise Exception(f"combobox for {filter_name} not found by JS or index")
        combobox = comboboxes[idx]

    # 2. Click the combobox to open the dropdown menu
    find_arrow_js = """
    const findArrowInsideCombobox = (combobox) => {
        if (!combobox) return null;
        
        const isMenuOption = (el) => {
            let curr = el;
            while (curr && curr !== document.body) {
                const label = curr.getAttribute ? curr.getAttribute('aria-label') : '';
                if (label && (label.includes('メニュー') || label.includes('menu') || label.includes('Menu') || label.includes('Options'))) {
                    return true;
                }
                const className = curr.className && typeof curr.className === 'string' ? curr.className : '';
                if (className.includes('menu') || className.includes('options') || className.includes('context-menu') || className.includes('visual-menu')) {
                    return true;
                }
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
            
            if (className.includes('MuiSelect-icon') || 
                className.includes('arrow') || 
                className.includes('Indicator') ||
                className.includes('caret') ||
                (role === 'button' && className.includes('icon'))) {
                return n;
            }
            if (tagName === 'svg') {
                return n;
            }
            if (n.shadowRoot) {
                const r = walk(n.shadowRoot);
                if (r) return r;
            }
            let c = n.firstChild;
            while (c) {
                const r = walk(c);
                if (r) return r;
                c = c.nextSibling;
            }
            return null;
        };
        
        let arrow = walk(combobox);
        if (arrow) return arrow;
        
        if (combobox.parentNode) {
            arrow = walk(combobox.parentNode);
            if (arrow) return arrow;
            
            if (combobox.parentNode.parentNode) {
                arrow = walk(combobox.parentNode.parentNode);
                if (arrow) return arrow;
            }
        }
        return null;
    };
    return findArrowInsideCombobox(arguments[0]);
    """
    
    arrow = None
    try:
        arrow = driver.execute_script(find_arrow_js, combobox)
    except Exception as e:
        print(f"    [警告] JSによる矢印アイコン検索エラー: {e}")
        
    click_target = arrow if arrow else combobox
    if arrow:
        print("    [情報] ▼矢印アイコンを検出しました。これをクリックします。")
    else:
        print("    [情報] ▼矢印アイコンが検出できなかったため、コンボボックス本体をクリックします。")

    # Dispatch mousedown and click events using JS to open the dropdown popover reliably
    open_dropdown_js = """
    const combobox = arguments[0];
    const arrow = arguments[1];
    const triggerEvents = (el) => {
        if (!el) return;
        const mousedown = new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window });
        const click = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
        el.dispatchEvent(mousedown);
        el.dispatchEvent(click);
    };
    if (arrow) {
        triggerEvents(arrow);
        if (arrow.parentNode) {
            triggerEvents(arrow.parentNode);
        }
    }
    triggerEvents(combobox);
    return true;
    """

    for attempt in range(3):
        try:
            # Trigger mousedown/click events via JS
            driver.execute_script(open_dropdown_js, combobox, arrow)
            time.sleep(2.5)
            break
        except Exception as e:
            # Fallback to ActionChains physical click if JS event dispatch fails
            try:
                ActionChains(driver).move_to_element(click_target).click().perform()
                time.sleep(2.5)
                break
            except StaleElementReferenceException:
                if attempt == 2:
                    raise
                try:
                    combobox = driver.execute_script(find_combobox_js, filter_name)
                    if combobox:
                        arrow = driver.execute_script(find_arrow_js, combobox)
                        click_target = arrow if arrow else combobox
                except:
                    pass
                time.sleep(1)

    # 3. Check if search box is present and type search term if so (skip if selecting "All" to avoid filter-out)
    search_box = None
    try:
        search_box = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='値を検索']"))
        )
    except TimeoutException:
        pass

    if search_box and target_value not in ["すべて", "すべての支社"]:
        try:
            search_box.send_keys(Keys.CONTROL, "a")
            search_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            search_term = target_value.split("_")[0] + "_" if "_" in target_value else target_value
            search_box.send_keys(search_term)
            time.sleep(3.5)  # Wait for filtering to complete
        except Exception as e:
            print(f"    [警告] 検索ボックス入力失敗: {e}")

    # 4. Find the target option, check its checkbox state, click if not checked, and click Apply if needed
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
        const text = item.innerText || '';
        const ariaLabel = item.getAttribute('aria-label') || '';
        if (isMatch(text, ariaLabel, targetText)) {
            targetOption = item;
            break;
        }
    }

    if (!targetOption) {
        return { success: false, reason: 'Option not found' };
    }

    const isSelected = (el) => {
        if (el.getAttribute('aria-selected') === 'true') return true;
        if (el.getAttribute('aria-checked') === 'true') return true;
        if (el.classList.contains('Mui-selected') || el.className.includes('selected')) return true;
        
        const checkbox = el.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) return true;

        const checkedInner = el.querySelector('[aria-checked="true"]');
        if (checkedInner) return true;

        // Traverse all descendants for check state classes and attributes
        const descendants = Array.from(el.querySelectorAll('*'));
        for (const desc of descendants) {
            const className = desc.className || '';
            const ariaChecked = desc.getAttribute ? desc.getAttribute('aria-checked') : '';
            if (ariaChecked === 'true') return true;
            if (typeof className === 'string' && (className.includes('Mui-checked') || className.includes('checked'))) {
                return true;
            }
        }
        return false;
    };

    const alreadyChecked = isSelected(targetOption);

    if (!alreadyChecked) {
        const mousedown = new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window });
        const click = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
        targetOption.dispatchEvent(mousedown);
        targetOption.dispatchEvent(click);
    }

    let applyClicked = false;
    const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
    for (const btn of buttons) {
        const text = (btn.innerText || '').trim();
        if (text === '適用' || text === 'Apply') {
            const mousedown = new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window });
            const click = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
            btn.dispatchEvent(mousedown);
            btn.dispatchEvent(click);
            applyClicked = true;
            break;
        }
    }

    return { 
        success: true, 
        clicked: !alreadyChecked, 
        alreadyChecked: alreadyChecked,
        applyClicked: applyClicked 
    };
    """

    res = {"success": False, "reason": "Not executed"}
    try:
        res = driver.execute_script(select_option_js, target_value)
    except Exception as e:
        print(f"    [警告] JSによるオプション選択エラー: {e}")

    if res.get("success"):
        print(f"    [選択結果] すでに選択済み: {res.get('alreadyChecked')}, クリック実行: {res.get('clicked')}, 適用ボタンクリック: {res.get('applyClicked')}")
        time.sleep(2.0)
    else:
        # Fallback to standard Selenium/Python clicks if JS failed
        print(f"    [情報] JS選択に失敗したため（理由: {res.get('reason') if res else 'エラー'}）、Seleniumによるフォールバックを実行します。")
        
        find_option_js = """
        const findDropdownOption = (targetText) => {
            const items = Array.from(document.querySelectorAll('[role="option"], .MuiMenuItem-root, [class*="MenuItem"]'));
            for (const item of items) {
                const text = (item.innerText || '').trim();
                const ariaLabel = item.getAttribute('aria-label') || '';
                if (text === targetText || text.includes(targetText) || ariaLabel.includes(targetText)) {
                    return item;
                }
            }
            return null;
        };
        return findDropdownOption(arguments[0]);
        """
        
        option = None
        try:
            option = driver.execute_script(find_option_js, target_value)
        except:
            pass

        if not option:
            try:
                option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[@role='option' and (contains(@aria-label, '{target_value}') or contains(text(), '{target_value}'))]"))
                )
            except TimeoutException:
                try:
                    option = driver.find_element(By.XPATH, f"//*[contains(@class, 'MenuItem') and contains(text(), '{target_value}')]")
                except NoSuchElementException:
                    pass

        if option is None:
            # Keyboard fallback (ARROW_DOWN + ENTER) if option is still not found
            if search_box:
                print("    [情報] 選択肢がDOMに見つかりません。キーボード操作(ARROW_DOWN + ENTER)を試みます。")
                try:
                    search_box.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1.0)
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2.0)
                    return
                except Exception as e:
                    print(f"    [警告] キーボード操作失敗: {e}")
            
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            time.sleep(1)
            raise Exception(f"選択肢「{target_value}」が見つかりません")

        # 5. Click the option
        for attempt in range(3):
            try:
                ActionChains(driver).move_to_element(option).click().perform()
                time.sleep(1.5)
                break
            except StaleElementReferenceException:
                if attempt == 2:
                    raise
                try:
                    option = driver.execute_script(find_option_js, target_value)
                except:
                    pass
                time.sleep(1)

        # Fallback click apply button if visible
        try:
            apply_btn = driver.find_element(By.XPATH, "//button[text()='適用' or text()='Apply']")
            if apply_btn.is_displayed():
                apply_btn.click()
                print("    [情報] Seleniumで適用ボタンをクリックしました")
                time.sleep(1.5)
        except:
            pass

    # Ensure dropdown is closed
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except:
        pass

def export_csv(driver):
    try:
        table = None
        for attempt in range(3):
            try:
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
                time.sleep(1)
                break
            except StaleElementReferenceException:
                print(f"    [情報] テーブル取得中に要素の差し替えが発生しました。リトライします。 (試行 {attempt + 1}/3)")
                time.sleep(1)
        
        if not table:
            raise Exception("テーブル要素の取得に失敗しました。")

        menu_btn = None
        for i in range(3):
            try:
                # table が stale になっていないか確認し、stale なら再取得する
                try:
                    _ = table.is_displayed()
                except StaleElementReferenceException:
                    print("    [情報] ホバー前にテーブル要素が古くなったため、再取得します。")
                    table = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", table)
                    time.sleep(1)

                if i == 0:
                    try:
                        ActionChains(driver).move_to_element_with_offset(table, 10, 10).click().perform()
                    except:
                        pass
                
                ActionChains(driver).move_to_element_with_offset(table, 10, 10).perform()
                time.sleep(2)
                
                try:
                    menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
                    for btn in menu_btns:
                        if btn.is_displayed():
                            menu_btn = btn
                            break
                    if menu_btn:
                        break
                except StaleElementReferenceException:
                    print("    [情報] ボタン検索中に要素の差し替えが発生しました。リトライします。")
            except StaleElementReferenceException:
                print("    [情報] ホバーループ中に要素の差し替えが発生しました。リトライします。")
                time.sleep(1)
            except Exception as e:
                print(f"    [情報] ホバーループ内エラー: {e}")
            
            try:
                ActionChains(driver).move_by_offset(-100, -100).perform()
            except:
                pass
            time.sleep(1)
        
        if not menu_btn:
             print("    [情報] メインメニューボタンが表示されませんでした。実績0件の可能性があります。")
             return "ZERO_DATA"

        # メニューボタンをクリック
        for attempt in range(3):
            try:
                ActionChains(driver).move_to_element(menu_btn).click().perform()
                break
            except StaleElementReferenceException:
                print(f"    [情報] メニューボタンのクリック中に要素が古くなりました。再取得します。(試行 {attempt + 1}/3)")
                menu_btns = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'メニューオプション') or contains(@aria-label, 'Visual menu')]")
                menu_btn = None
                for btn in menu_btns:
                    if btn.is_displayed():
                        menu_btn = btn
                        break
                if not menu_btn:
                    raise Exception("再取得したメニューボタンが見つかりません。")
                time.sleep(1)
        
        time.sleep(2)

        # CSVボタンをクリック
        csv_btn = None
        for attempt in range(3):
            try:
                csv_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'MuiMenuItem') and (contains(text(), 'CSV') or contains(text(), 'エクスポート'))]"))
                )
                ActionChains(driver).move_to_element(csv_btn).click().perform()
                break
            except StaleElementReferenceException:
                print(f"    [情報] CSVボタンのクリック中に要素が古くなりました。リトライします。(試行 {attempt + 1}/3)")
                time.sleep(1)
        
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

import csv
def validate_downloaded_csv(filepath, target_year, target_month):
    """ダウンロードされたCSV内に対象年月のデータが1行以上含まれているか確認する"""
    target_prefix = f"{target_year:04d}-{target_month:02d}"
    target_prefix_slash = f"{target_year:04d}/{target_month:02d}"
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                row_count += 1
                date_str = row.get('日付', '')
                if not date_str:
                    continue
                # 年月が含まれているか
                if date_str.startswith(target_prefix) or date_str.startswith(target_prefix_slash):
                    return True
            # 行が無い場合は不整合
            if row_count == 0:
                print("    [警告] CSVの中身が空です（ヘッダーのみ）。")
                return False
    except Exception as e:
        print(f"    [警告] CSVバリデーション実行エラー: {e}")
        return False
    
    print(f"    [警告] CSV内に対象年月 {target_year}/{target_month:02d} のデータが1件も見つかりませんでした。")
    return False

def main():
    print("【TMP-ONE 月次差分データ抽出ループシステム (一時フォルダ保存版)】")

    # 対象年月の読み込み
    target_year = None
    target_month = None
    target_month_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target_month.json")
    if os.path.exists(target_month_json):
        try:
            with open(target_month_json, "r", encoding="utf-8") as f:
                target_info = json.load(f)
                target_year = target_info.get("year")
                target_month = target_info.get("month")
                print(f"  [設定] 対象年月をロードしました: {target_year}/{target_month:02d}")
        except Exception as e:
            print(f"  [警告] target_month.json のロードに失敗しました: {e}")

    if not target_year or not target_month:
        # フォールバック: 現在の日付から1ヶ月前を計算
        now = datetime.now()
        if now.month == 1:
            target_year = now.year - 1
            target_month = 12
        else:
            target_year = now.year
            target_month = now.month - 1
        print(f"  [設定] 対象年月を自動決定しました (前月): {target_year}/{target_month:02d}")

    # 不足リスト (missing_patterns.json) の読み込み
    missing_set = None
    missing_patterns_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "missing_patterns.json")
    if os.path.exists(missing_patterns_json):
        try:
            with open(missing_patterns_json, "r", encoding="utf-8") as f:
                missing_data = json.load(f)
                missing_set = set((item["amount"], item["route"], item["sales_class"]) for item in missing_data)
                print(f"  [設定] 不足データリストから {len(missing_set)} 件の抽出指示をロードしました。ピンポイント抽出を実行します。")
        except Exception as e:
            print(f"  [警告] missing_patterns.json のロードに失敗しました: {e}")

    edge_options = Options()
    edge_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = webdriver.Edge(options=edge_options)
    
    try:
        driver.maximize_window()
        print("  [設定] ウィンドウを最大化しました。")
        time.sleep(1)
    except Exception as e:
        print(f"  [警告] ウィンドウの最大化に失敗しました: {e}")
    
    # CDPコマンドを使用してダウンロード先ディレクトリを動的に設定する
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": DOWNLOAD_DIR
    })

    print("Edge (デバッグモード) に接続しました。QuickSightダッシュボードを検索中...")

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
        if found:
            break
            
    if not found:
        print("[エラー] QuickSightダッシュボードを開いているタブが見つかりませんでした。")
        sys.exit(1)
        
    print("★ iframe接続成功")
        
    # 支社フィルターを自動的に「すべて」に設定する
    print("  [初期設定] 支社フィルターを「すべて」に設定します...")
    try:
        set_quicksight_filter(driver, "支社", "すべて")
        print("  ✓ 支社フィルターを「すべて」に設定完了")
    except Exception as e:
        print(f"  [警告] 支社フィルターの設定に失敗しました: {e} (手動で「すべて」になっているか確認してください)")

    total_expected = len(AMOUNT_TYPES) * len(ROUTES_ALL) * len(SALES_CLASSES_ALL)
    pattern_count = 0
    success_count = 0
    skip_count = 0
    fail_count = 0
    failed_patterns = []

    for amount in AMOUNT_TYPES:
        amount_changed = False
        try:
            # もしこの金額タイプに属する不足データが1つもないなら、フィルター切り替え自体をスキップ
            if missing_set is not None:
                has_missing_in_amount = any(m[0] == amount for m in missing_set)
                if not has_missing_in_amount:
                    print(f"  [スキップ] 金額種別 {amount} に不足パターンがないためスキップします。")
                    continue

            set_quicksight_filter(driver, "売上/粗利", amount)
            amount_changed = True
        except Exception as e:
            print(f"  [エラー] 金額種別切替失敗: {e}")

        for route in ROUTES_ALL:
            route_changed = False
            if amount_changed:
                try:
                    # もしこの金額＋ルートに属する不足データが1つもないなら、フィルター切り替え自体をスキップ
                    if missing_set is not None:
                        has_missing_in_route = any(m[0] == amount and m[1] == route for m in missing_set)
                        if not has_missing_in_route:
                            # 2700パターンの期待総数カウントを進めるためのダミー処理
                            for sc in SALES_CLASSES_ALL:
                                pattern_count += 1
                                skip_count += 1
                            continue

                    set_quicksight_filter(driver, "ルート", route)
                    route_changed = True
                except Exception as e:
                    print(f"  [エラー] ルート切替失敗: {e}")
            else:
                print(f"  [警告] 金額種別切替に失敗しているため、ルート {route} の切替をスキップします。")

            for sc in SALES_CLASSES_ALL:
                # 不足リストがロードされている場合、リストに含まれないパターンは無条件スキップ
                if missing_set is not None and (amount, route, sc) not in missing_set:
                    pattern_count += 1
                    skip_count += 1
                    continue

                wait_for_disk_space(threshold_gb=3.5)
                pattern_count += 1
                
                sc_fname = sc.replace("(", "（").replace(")", "）")
                target_filename = f"【{amount}】{route}_{sc_fname}.csv"
                target_path = os.path.join(DOWNLOAD_DIR, target_filename)

                # 一時フォルダおよび最終フォルダに既に存在するかチェック (Xドライブアクセスはsafe_x_drive_opで)
                final_path_csv = os.path.join(X_DEST_DIR, target_filename)
                final_path_zip = final_path_csv.replace(".csv", ".zip")
                final_path_zero = os.path.join(X_DEST_DIR, f"[ZERO_DATA]{target_filename}")
                
                dest_zip_name = target_filename.replace(".csv", ".zip")
                dest_zip_path = os.path.join(X_FINAL_DIR, dest_zip_name)
                dest_zero_path = os.path.join(X_FINAL_DIR, f"[ZERO_DATA]{target_filename}")
                
                # 常にデータなしとなる除外パターンのチェック
                if (route, sc) in EXCLUDE_COMBINATIONS:
                    print(f"  [除外スキップ] 常にデータなしとなる組み合わせのためスキップ: {route} - {sc}")
                    if not safe_x_drive_op(os.path.exists, final_path_zero) and not safe_x_drive_op(os.path.exists, dest_zero_path):
                        try:
                            def _write_zero():
                                with open(final_path_zero, 'w', encoding='utf-8') as f:
                                    f.write(f"Zero data (statically excluded) at {datetime.now().isoformat()}")
                            safe_x_drive_op(_write_zero)
                            print(f"  ✓ マーカーファイルを作成しました: [ZERO_DATA]{target_filename}")
                        except Exception as e:
                            print(f"  [警告] マーカーファイルの作成に失敗しました: {e}")
                    skip_count += 1
                    success_count += 1
                    continue

                if safe_x_drive_op(os.path.exists, final_path_csv) or safe_x_drive_op(os.path.exists, final_path_zip) or safe_x_drive_op(os.path.exists, final_path_zero):
                    status = "CSV" if safe_x_drive_op(os.path.exists, final_path_csv) else ("ZIP" if safe_x_drive_op(os.path.exists, final_path_zip) else "ZERO_DATA")
                    print(f"  [スキップ] 既に一時フォルダに存在します({status}): {target_filename}")
                    skip_count += 1
                    success_count += 1
                    continue

                if safe_x_drive_op(os.path.exists, dest_zero_path):
                    print(f"  [スキップ] 既に最終フォルダにゼロデータマーカーが存在します: {target_filename}")
                    skip_count += 1
                    success_count += 1
                    continue

                if safe_x_drive_op(check_already_extracted_in_dest, dest_zip_path, target_year, target_month):
                    print(f"  [スキップ] 既に最終フォルダのZIPに当月データが含まれています ({target_year}/{target_month:02d}): {target_filename}")
                    skip_count += 1
                    success_count += 1
                    continue

                if not (amount_changed and route_changed):
                    print(f"  [エラースキップ] フィルター切り替えに失敗しているため、抽出をスキップします: {target_filename}")
                    fail_count += 1
                    failed_patterns.append({
                        "pattern": target_filename,
                        "reason": "売上/粗利またはルートのフィルター切り替え失敗のため安全にスキップされました。"
                    })
                    continue

                print(f"\n{'='*60}")
                print(f"[{pattern_count}/{total_expected}] 処理中: {target_filename}")
                print(f"{'='*60}")

                try:
                    old_table = None
                    try:
                        old_table = driver.find_element(By.XPATH, "//*[contains(@data-automation-id, 'table') or contains(@class, 'quicksight-viz')]")
                    except:
                        pass

                    set_quicksight_filter(driver, "販売区分", sc)
                    print("  データロード待機中...")
                    load_status = wait_for_data_load(driver, old_table=old_table, timeout=15)
                    
                    if load_status == "ZERO_DATA":
                        print("  [情報] 画面に「データなし」を検出しました。実績0件として処理します。")
                        try:
                            def _write_ui_zero():
                                with open(final_path_zero, 'w', encoding='utf-8') as f:
                                    f.write(f"Zero data (detected on UI) at {datetime.now().isoformat()}")
                            safe_x_drive_op(_write_ui_zero)
                            print(f"  ✓ マーカーファイルを作成しました: [ZERO_DATA]{target_filename}")
                        except Exception as e:
                            print(f"  [警告] マーカーファイルの作成に失敗しました: {e}")
                        success_count += 1
                        continue

                    res = export_csv(driver)
                    if res == True:
                        print(f"  ダウンロード完了を待機中 (保存先: {DOWNLOAD_DIR})...")
                        timeout = 120 
                        start_time = time.time()
                        downloaded = False
                        
                        while time.time() - start_time < timeout:
                            all_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
                            new_csvs = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))
                            crdownloads = glob.glob(os.path.join(DOWNLOAD_DIR, "*.crdownload"))
                            
                            if crdownloads:
                                print(f"    [待機] ダウンロード進行中... ({len(crdownloads)}個の未完了ファイル)")
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
                                    # --- 年月データバリデーションの実行 ---
                                    if not validate_downloaded_csv(latest_file, target_year, target_month):
                                        print("    [ERROR] ダウンロードされたCSVのデータ内容が不正です。ファイルを破棄します。")
                                        if os.path.exists(latest_file):
                                            os.remove(latest_file)
                                        break  # 待機ループを抜けてタイムアウト失敗とする
                                    
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    os.rename(latest_file, target_path)
                                    
                                    # ZIP圧縮して一時保存先へ移動
                                    zip_path = target_path.replace(".csv", ".zip")
                                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                                        zf.write(target_path, arcname=target_filename)
                                    
                                    os.remove(target_path)
                                    
                                    # Xドライブへの書き込み・移動はリトライ対応
                                    safe_x_drive_op(shutil.move, zip_path, final_path_zip)
                                    print(f"  ✓ ZIP圧縮して一時保存先へ移動完了: {os.path.basename(final_path_zip)}")
                                    
                                    downloaded = True
                                    break
                                except Exception as e:
                                    print(f"    [警告] リネーム/圧縮/移動失敗: {e}")
                                    break
                            else:
                                if int(time.time() - start_time) % 10 == 0:
                                    print(f"    ...待機中 ({int(time.time() - start_time)}s経過 / フォルダ内総数: {len(all_files)}個)")
                            
                            time.sleep(2)
                        
                        if not downloaded:
                            print("  [警告] ファイルの書き出しまたはデータバリデーションに失敗しました。")
                            fail_count += 1
                            failed_patterns.append({
                                "pattern": target_filename,
                                "reason": "CSVエクスポート後のダウンロード完了が確認できないか、データ年月のバリデーションに失敗しました。"
                            })
                        else:
                            success_count += 1
                    elif res == "ZERO_DATA":
                        print(f"  [情報] 実績0件と判定しました。マーカーファイルを作成します。")
                        def _write_ui_zero_alt():
                            with open(final_path_zero, 'w', encoding='utf-8') as f:
                                f.write(f"Zero data detected at {datetime.now().isoformat()}")
                        safe_x_drive_op(_write_ui_zero_alt)
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_patterns.append({
                            "pattern": target_filename,
                            "reason": "エクスポートボタンやメニューオプションが表示されない等の操作失敗です。"
                        })
                except Exception as e:
                    print(f"  エラー: {e}")
                    fail_count += 1
                    failed_patterns.append({
                        "pattern": target_filename,
                        "reason": f"予期せぬ例外エラーが発生しました: {e}"
                    })
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)

    print(f"\n{'='*60}")
    print(f"完了！ 成功(込スキップ): {success_count} / 失敗: {fail_count} / 合計: {total_expected}")
    
    report_data = {
        "target_year": target_year,
        "target_month": target_month,
        "timestamp": datetime.now().isoformat(),
        "total_expected": total_expected,
        "success_count": success_count,
        "skip_count": skip_count,
        "fail_count": fail_count,
        "failed_patterns": failed_patterns
    }
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extraction_report.json")
    try:
        # ローカルファイルなので通常保存
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 抽出レポートを保存しました: {report_path}")
    except Exception as e:
        print(f"  [警告] 抽出レポートの保存に失敗しました: {e}")
        
    driver.quit()

if __name__ == '__main__':
    main()
