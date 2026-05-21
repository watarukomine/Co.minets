import os
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 設定
PROJECT_ROOT = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI"
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")
PROFILE_DIR = os.path.join(PROJECT_ROOT, "playwright_profile")

edge_options = Options()
edge_options.add_argument(f"user-data-dir={PROFILE_DIR}")
edge_options.add_argument("--start-maximized")
edge_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver = webdriver.Edge(options=edge_options)
wait = WebDriverWait(driver, 30)

def find_dropdown_btn(label):
    print(f"  └ 🔍 「{label}」ラベルに紐づくドロップダウンボタンを探索中...")
    
    # 複数の方法でドロップダウンを特定
    try:
        # 1. 汎用的なラベル+兄弟要素XPath
        xpath = f"//label[contains(text(), '{label}')]/following-sibling::div"
        if label == "売上/粗利":
            xpath = "//label[contains(text(), '売上') or contains(text(), '粗利')]/following-sibling::div"
        
        btns = driver.find_elements(By.XPATH, xpath)
        for b in btns:
            if b.is_displayed() and b.get_attribute("role") in ["button", "combobox"]:
                return b
        
        # 2. 親要素を辿って別の兄弟を探す
        xpath2 = f"//label[contains(text(), '{label}')]/..//div[@role='button' or @role='combobox']"
        btns = driver.find_elements(By.XPATH, xpath2)
        for b in btns:
            if b.is_displayed():
                return b

        # 3. JavaScriptで直接探索（一番確実）
        btn_via_js = driver.execute_script(f"""
            var labels = Array.from(document.querySelectorAll('label'));
            var targetLabel = labels.find(l => l.innerText.includes('{label}'));
            if (!targetLabel && '{label}' == '売上/粗利') {{
                targetLabel = labels.find(l => l.innerText.includes('売上') || l.innerText.includes('粗利'));
            }}
            if (!targetLabel) return null;
            
            var parent = targetLabel.parentElement;
            while (parent && parent.tagName !== 'BODY') {{
                var btn = parent.querySelector('[role="button"], [role="combobox"], select');
                if (btn) return btn;
                parent = parent.parentElement;
            }}
            return null;
        """)
        if btn_via_js:
            return btn_via_js
            
    except Exception as e:
        print(f"  └ ⚠️ 探索中にエラー: {e}")
    
    return None

def click_dropdown_and_select(label, value):
    print(f"\n🚀 ドロップダウン「{label}」で「{value}」を選択します")
    btn = find_dropdown_btn(label)
    if not btn:
        raise Exception(f"「{label}」のドロップダウンが見つかりません。")
        
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
    time.sleep(1)
    btn.click()
    print(f"  ✅ ドロップダウンを開きました。")
    time.sleep(2)
    
    # 検索と選択
    try:
        search_box = driver.find_element(By.XPATH, "//input[@placeholder='検索' or @placeholder='Search']")
        print(f"  └ ⌨️ 「{value}」を入力中...")
        search_box.clear()
        search_box.send_keys(value)
        time.sleep(3) # 候補が出るまで長めに待つ
        
        search_box.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        search_box.send_keys(Keys.ENTER)
        print(f"  ✅ 選択完了。")
        
        time.sleep(1)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1.5)
    except Exception as e:
        print(f"  ❌ 選択エラー: {e}")
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        raise

try:
    print("🌐 クイックサイトを開いています...")
    driver.get("https://ap-northeast-1.quicksight.aws.amazon.com/sn/dashboards/5e1732e7-577e-40d6-848e-67010487440e#p.EGZ010_日別実績")
    time.sleep(15)
    
    # Iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        driver.switch_to.frame(iframes[0])
        print("✅ Iframeに移行しました。")

    # 手順実行
    click_dropdown_and_select("売上/粗利", "売上")
    click_dropdown_and_select("ルート", "a-00 総販")
    # ここで一度現在の「販売区分」の値をログに出したいが、一旦そのまま進める
    click_dropdown_and_select("販売区分", "225_ダンロップタイヤ")
    
    print("\n⏳ データの描画を待っています（15秒）...")
    time.sleep(15) # 今回は最大15秒待機
    
    # 3点リーダー (Export)
    print("🔍 CSV出力メニューを探索中...")
    menu_btn_js = driver.execute_script("""
        var allDivs = document.querySelectorAll('div');
        var targetVisual = null;
        var maxArea = 0;
        for(var i=0; i<allDivs.length; i++) {
            var div = allDivs[i];
            var rect = div.getBoundingClientRect();
            var area = rect.width * rect.height;
            if (rect.width > 200 && rect.height > 200 && area > maxArea && rect.width < window.innerWidth && rect.height < window.innerHeight) {
                var zIndex = window.getComputedStyle(div).zIndex;
                if (zIndex !== 'auto' && parseInt(zIndex) > 100) continue;
                maxArea = area;
                targetVisual = div;
            }
        }
        if(!targetVisual) return null;
        targetVisual.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
        
        var btns = document.querySelectorAll('button');
        var visualRect = targetVisual.getBoundingClientRect();
        var targetBtn = null;
        var minDistance = 999999;
        for(var j=0; j<btns.length; j++){
            var btn = btns[j];
            var rect = btn.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0 || rect.width > 60) continue;
            var dist = Math.sqrt(Math.pow((rect.left+rect.width/2) - visualRect.right, 2) + Math.pow((rect.top+rect.height/2) - visualRect.top, 2));
            if (dist < minDistance) { minDistance = dist; targetBtn = btn; }
        }
        return targetBtn;
    """)
    
    if menu_btn_js:
        print("✅ メニューボタン発見。")
        ActionChains(driver).move_to_element(menu_btn_js).click().perform()
        time.sleep(2)
        
        # エクスポート
        export_xpath = "//li[contains(text(), 'CSVへエクスポート') or contains(text(), 'Export to CSV')]"
        export_btn = wait.until(EC.element_to_be_clickable((By.XPATH, export_xpath)))
        export_btn.click()
        print("📥 ダウンロードを開始しました。15秒待ちます...")
        time.sleep(15)
        
        # ファイル名の確認とリネームは今回は手動または後で。
        # 単純にダウンロードされたはず。
    else:
        print("❌ メニューボタンが見つかりませんでした。")
        driver.save_screenshot(os.path.join(DOWNLOAD_DIR, "debug_final_fail.png"))

finally:
    driver.quit()
    print("\n🔚 プロセス終了。")
