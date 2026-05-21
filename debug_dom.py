"""
QuickSight ダッシュボードのフィルタードロップダウンDOM構造を徹底調査するデバッグスクリプト
JavaScript実行でShadow DOMも含めて調査します。
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://report.tmp-one.com/portal#"
TARGET_DASHBOARD = "EGZ010_日別実績"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".tmp_one_selenium_profile")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

options = Options()
options.add_argument(f"user-data-dir={USER_DATA_DIR}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)

print("🌐 Edgeブラウザを起動しています...")
driver = webdriver.Edge(options=options)

try:
    driver.maximize_window()
    driver.get(BASE_URL)
    
    # ログインチェック
    time.sleep(5)
    page_text = driver.page_source.lower()
    if "employee" in page_text or "ソーシャル" in page_text:
        print("🔑 ログインが必要です。30秒待機します...")
        time.sleep(30)
    else:
        print("✅ 既にログイン済み。")

    # iframeを探す
    print("⏳ iframeの出現を待機中...")
    WebDriverWait(driver, 30).until(lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0)
    time.sleep(5)
    
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    target_iframe = None
    for iframe in iframes:
        src = iframe.get_attribute("src") or ""
        if "quicksight" in src.lower() or "amazon" in src.lower() or "favorites" in src.lower():
            target_iframe = iframe
            break
    if not target_iframe and iframes:
        target_iframe = iframes[-1]
    
    if target_iframe:
        driver.switch_to.frame(target_iframe)
        time.sleep(5)
        
        # ダッシュボードリンクをクリック
        try:
            link = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{TARGET_DASHBOARD}')]"))
            )
            print(f"✅ ダッシュボード発見。クリックします...")
            try:
                link.click()
            except:
                driver.execute_script("arguments[0].click();", link)
            print("⏳ ダッシュボードの展開を待機中（25秒）...")
            time.sleep(25)
        except Exception as e:
            print(f"⚠️ ダッシュボードのクリックに失敗: {e}")
            time.sleep(10)
        
        # iframeを再取得
        driver.switch_to.default_content()
        time.sleep(5)
        
        new_iframes = driver.find_elements(By.TAG_NAME, "iframe")
        new_target = None
        for iframe in new_iframes:
            src = iframe.get_attribute("src") or ""
            if "quicksight" in src.lower() or "amazon" in src.lower() or "dashboard" in src.lower():
                new_target = iframe
                break
        if not new_target and new_iframes:
            new_target = new_iframes[-1]
        
        if new_target:
            driver.switch_to.frame(new_target)
            time.sleep(10)
            
            print("\n" + "="*60)
            print("📋 徹底DOM調査 開始")
            print("="*60)
            
            # --- JavaScript で body 全体の innerHTML を保存 ---
            print("\n[1] body全体のHTMLをファイルに保存中...")
            body_html = driver.execute_script("return document.body.innerHTML;")
            debug_file = os.path.join(DOWNLOAD_DIR, "debug_full_body.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(body_html)
            print(f"✅ 保存完了: {debug_file} ({len(body_html)} bytes)")
            
            # --- 「ルート」テキストを含む部分を探す ---
            print("\n[2] 'ルート'/'販売区分'テキストが含まれる位置を調査...")
            for keyword in ["ルート", "販売区分", "売上", "粗利", "a-00"]:
                idx = body_html.find(keyword)
                if idx >= 0:
                    snippet = body_html[max(0, idx-200):idx+500]
                    print(f"\n  ✅ '{keyword}' 発見（位置{idx}）。周辺200文字:")
                    print("  " + snippet[:500].replace('\n', '\n  '))
                else:
                    print(f"  ❌ '{keyword}' が見つかりません")
            
            # --- JavaScriptで詳細な要素情報を収集 ---
            print("\n[3] JavaScriptで全ボタン・インタラクティブ要素を収集...")
            js_result = driver.execute_script("""
                var results = [];
                var tags = ['button', 'select', 'input', 'a'];
                tags.forEach(function(tag) {
                    var elems = document.querySelectorAll(tag);
                    elems.forEach(function(el, i) {
                        if (i >= 50) return;
                        var rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            results.push({
                                tag: el.tagName,
                                text: el.textContent.trim().substring(0, 80),
                                aria_label: el.getAttribute('aria-label') || '',
                                role: el.getAttribute('role') || '',
                                type: el.getAttribute('type') || '',
                                class: el.className.substring(0, 80),
                                id: el.id || '',
                                visible: rect.width > 0 && rect.height > 0,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y)
                            });
                        }
                    });
                });
                return results;
            """)
            
            print(f"  発見した要素数: {len(js_result)}")
            for el in js_result:
                print(f"  [{el['tag']}] text='{el['text'][:60]}' aria-label='{el['aria_label']}' "
                      f"role='{el['role']}' class='{el['class'][:40]}' pos=({el['x']},{el['y']})")
            
            # --- role='button'やrole='combobox'の要素も含む ---
            print("\n[4] role属性を持つ全要素（JavaScriptで取得）...")
            js_roles = driver.execute_script("""
                var results = [];
                var all = document.querySelectorAll('[role]');
                all.forEach(function(el, i) {
                    if (i >= 100) return;
                    var rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            tag: el.tagName,
                            role: el.getAttribute('role'),
                            text: el.textContent.trim().substring(0, 80),
                            aria_label: el.getAttribute('aria-label') || '',
                            class: el.className.substring(0, 80),
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        });
                    }
                });
                return results;
            """)
            
            print(f"  role属性を持つ要素数: {len(js_roles)}")
            for el in js_roles:
                print(f"  [{el['tag']}] role='{el['role']}' text='{el['text'][:60]}' "
                      f"aria-label='{el['aria_label']}' class='{el['class'][:40]}'")
            
            print("\n" + "="*60)
            print("✅ DOM調査完了！")
            print(f"📁 全bodyHTMLを保存: {debug_file}")
            print("="*60)
            print("\nEnterキーを押してブラウザを閉じてください...")
            input("> ")

finally:
    driver.quit()
    print("🛑 ブラウザを終了しました。")
