import os
import sys
import time
import glob
import shutil
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ログ設定
LOG_FILE = "extraction_egz100.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def log(msg):
    logging.info(msg)

import argparse
parser = argparse.ArgumentParser(description="TMP-One EGZ100 Data Extractor")
parser.add_argument("--headless", action="store_true", help="画面を出さずにバックグラウンドで実行")
args = parser.parse_args()

BASE_URL = "https://report.tmp-one.com/portal#"
TARGET_DASHBOARD = "EGZ100"
TARGET_TAB = "⑤販売台数データ"

# Point to local C: drive to bypass Fileforce sync/cache issues
DOWNLOAD_DIR = r"C:\Users\00137012\Desktop\rpa_downloads_egz100"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".tmp_one_selenium_profile_2")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
ARTIFACT_DIR = r"C:\Users\00137012\.gemini\antigravity\brain\c42f2c71-f35d-4389-9e30-17ff8c173dcb"

def generate_months(start_str, end_str):
    start_y, start_m = map(int, start_str.split('/'))
    end_y, end_m = map(int, end_str.split('/'))
    months = []
    curr_y, curr_m = start_y, start_m
    while (curr_y > end_y) or (curr_y == end_y and curr_m >= end_m):
        months.append(f"{curr_y:04d}/{curr_m:02d}")
        curr_m -= 1
        if curr_m == 0:
            curr_m = 12
            curr_y -= 1
    return months

def run_extraction():
    log("STARTING EGZ100 EXTRACTION PROCESS")
    options = Options()
    options.add_argument(f"user-data-dir={USER_DATA_DIR}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    # --- アタッチモードの試行 ---
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_debug_port_open = sock.connect_ex(('127.0.0.1', 9222)) == 0
    sock.close()
    
    if is_debug_port_open:
        log("Detected Edge on port 9222. Attaching to existing session...")
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    else:
        log("No debugging port detected. Starting a new Edge instance...")

    driver = webdriver.Edge(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(BASE_URL)
        time.sleep(10)
        log("Attempting to navigate via Keyboard Emulation (Search + Tab + Enter)...")
        time.sleep(4)
        
        try:
            # 1. Use JS to populate search box (avoids XPath character encoding errors on Windows)
            driver.execute_script("""
                const search = document.querySelector('input[placeholder*="検索"]');
                if(search){
                    search.focus();
                    search.value = 'EGZ100_新車販売・受注台数';
                    search.dispatchEvent(new Event('input', {bubbles:true}));
                    search.dispatchEvent(new Event('change', {bubbles:true}));
                }
            """)
            time.sleep(3) # Wait for filter to apply
            
            # 2. Emulate tabbing down to the first result and pressing Enter
            log("  -> Tabbing to search result...")
            actions = ActionChains(driver)
            
            # Since JS focused the search input, Tab should move to the first matching result.
            actions.send_keys(Keys.TAB).pause(0.5).send_keys(Keys.ENTER).perform()
            log("  -> Keypress Enter submitted via ActionChains.")
            time.sleep(2)
            
            # Fallback JS click on the isolated element with reinforced events
            driver.execute_script("""
                if (window.location.href.includes('login.microsoftonline.com')) return;
                
                const findAndClick = (root, text) => {
                    let res = null;
                    const walk = n => {
                        if(!n || res) return;
                        let t = '';
                        try { t = (n.nodeType===3 ? n.textContent : (n.nodeType===1 ? (n.innerText||n.getAttribute('aria-label')||'') : '')); } catch(e){}
                        if(t && t.includes(text) && (n.nodeType===3 || n.children.length === 0)) {
                            res = (n.nodeType===3 ? n.parentElement : n); return;
                        }}
                        if(n.shadowRoot) walk(n.shadowRoot);
                        let c = n.firstChild; while(c){ walk(c); c = c.nextSibling; }
                    };
                    walk(document.body);
                    if(res) {
                        const clickable = res.closest('a, button, [role="button"]') || res;
                        try { clickable.scrollIntoView({block:'center'}); } catch(e){}
                        const r = clickable.getBoundingClientRect();
                        const cx = r.left + r.width/2;
                        const cy = r.top + r.height/2;
                        clickable.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:cx, clientY:cy}));
                        clickable.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:cx, clientY:cy}));
                        clickable.click();
                    }
                };
                findAndClick(document.body, 'EGZ100');
                findAndClick(document.body, 'TMP Employee'); // Also handles login
            """)
            
        except Exception as e:
            log(f"  -> WARNING: Key Emulation failed: {e}")

        time.sleep(20) # Wait for dashboard load
        
        # Navigate to specific Tab
        log("Navigating to Tab: " + TARGET_TAB)
        driver.execute_script(f"""
            const tabs = Array.from(document.querySelectorAll('*')).filter(n => (n.innerText||'').includes('{TARGET_TAB}') && n.offsetParent !== null);
            // Click the deepest matching element that looks clickable
            if(tabs.length > 0) {{
                // sort by depth or just pick last
                tabs[tabs.length-1].click();
            }}
        """)
        time.sleep(15)

        # Ensure filters are set to 'すべて選択'
        # In QuickSight, usually a page load has default 'Select All' for lists unless overridden. 
        # The user requested 'すべて選択', so we assume it's the default or we can trust the interface state initially.

        # Generate Months
        # Assuming current month as start, down to 2023/04
        current_month = datetime.now().strftime('%Y/%m')
        target_months = generate_months(current_month, '2023/04')
        log(f"Target Months: {target_months}")
        
        for month_str in target_months:
            filename = f"EGZ100_販売台数_{month_str.replace('/', '')}.csv"
            log(f"PROCESSING: {month_str} -> {filename}")
            
            # Input Date
            try:
                # The screenshot shows YYYY/MM standard format. We find the inputs.
                inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'YYYY/MM')]")
                if len(inputs) >= 2:
                    for idx in [0, 1]:  # Both start and end get the same month
                        inputs[idx].click()
                        inputs[idx].send_keys(Keys.CONTROL, "a")
                        inputs[idx].send_keys(Keys.BACKSPACE)
                        inputs[idx].send_keys(month_str)
                        inputs[idx].send_keys(Keys.ENTER)
                        time.sleep(1)
                    log(f"  -> Applied Date Filter: {month_str}")
                else:
                    log("  -> WARNING: Could not find Date inputs, using JS fallback...")
                    # JS Fallback
                    driver.execute_script(f"""
                        const ins = document.querySelectorAll('input[placeholder*="YYYY/MM"]');
                        if (ins.length >= 2) {{
                            ins[0].value = '{month_str}'; ins[0].dispatchEvent(new Event('input', {{bubbles:true}}));
                            ins[1].value = '{month_str}'; ins[1].dispatchEvent(new Event('input', {{bubbles:true}}));
                            ins[1].dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, key:'Enter', code:'Enter', keyCode:13}}));
                        }}
                    """)
                time.sleep(15) # Wait for visual refresh
            except Exception as e:
                log(f"  -> ERROR setting date: {e}")
                continue

            # Export Visual
            success = False
            for attempt in range(3):
                try:
                    # 1. Activate Visual (Table) and Find the "More Options" button
                    click_target = driver.execute_script("""
                        function f(root, t){
                            let res = null;
                            const walk = n => { 
                                if(res) return; 
                                if(n.nodeType===1 && (
                                    (n.getAttribute('aria-label')||'').includes(t) || 
                                    (n.getAttribute('title')||'').includes(t) || 
                                    (n.innerText||'').includes(t)
                                )){
                                    res=n; return;
                                } 
                                if(n.shadowRoot) walk(n.shadowRoot); 
                                let c=n.firstChild; while(c){walk(c);c=c.nextSibling;} 
                            };
                            walk(root); return res;
                        }
                        
                        // Look for visual container
                        const selectors = ['.visual-container', '[data-automation-id*="table"]'];
                        let v = null;
                        for(let s of selectors) { v = document.querySelector(s); if(v) break; }
                        
                        if(v) {
                            v.scrollIntoView({block:'center'});
                            // Prefer finding the element first by automation-id or aria-label
                            let btn = v.querySelector('[data-automation-id*="options"]') || 
                                      v.querySelector('[data-automation-id*="menu"]') ||
                                      f(v, 'オプション') || f(v, 'メニュー');
                            
                            if(btn) {
                                // Scroll to center and return its position to Python
                                const r = btn.getBoundingClientRect();
                                return {x: r.left + r.width/2, y: r.top + r.height/2, found: true};
                            } else {
                                // If no explicit button, try the top-right area
                                const r = v.getBoundingClientRect();
                                return {x: r.right - 25, y: r.top + 25, found: false};
                            }
                        }
                        return null;
                    """)
                    
                    if click_target:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(driver)
                        # Move to absolute coordinates and click
                        # Note: we need to handle viewport scroll offset if we use absolute screen coords
                        # But since it's headless and we just did scrollIntoView, we can use relative.
                        actions.move_by_offset(click_target['x'], click_target['y']).click().perform()
                        # Reset mouse for next attempt
                        actions.move_by_offset(-click_target['x'], -click_target['y']).perform()
                        time.sleep(2)
                        
                        # Fallback: also try JS click
                        driver.execute_script(f"const el = document.elementFromPoint({click_target['x']}, {click_target['y']}); if(el) el.click();")
                    
                    time.sleep(5) 
                    
                    driver.save_screenshot(os.path.join(ARTIFACT_DIR, f"debug_egz100_menu_{attempt}.png"))
                    
                    # 2. Open Menu
                    exported = driver.execute_script("""
                        function f(root, t){
                            let res = null;
                            const walk = n => { if(res) return; if(n.nodeType===1 && ((n.getAttribute('aria-label')||'').includes(t) || (n.innerText||'').includes(t))){res=n;return;} if(n.shadowRoot) walk(n.shadowRoot); let c=n.firstChild; while(c){walk(c);c=c.nextSibling;} };
                            walk(root); return res;
                        }
                        const menu = f(document.body, 'メニューオプション');
                        if(menu) { menu.click(); return true; }
                        return false;
                    """)
                    if not exported:
                        log(f"  -> Attempt {attempt+1}: Export Menu not found.")
                        continue
                    
                    time.sleep(3)
                    
                    # 3. Click CSV Export
                    csv_clicked = driver.execute_script("""
                        function findCSV(root){
                            let found = [];
                            const walk = n => { if(n.nodeType===1 && (n.innerText||'').includes('CSV')) found.push(n); if(n.shadowRoot) walk(n.shadowRoot); let c=n.firstChild; while(c){walk(c);c=c.nextSibling;} };
                            walk(root); return found;
                        }
                        const items = findCSV(document.body);
                        let ok = false;
                        items.forEach(i => { 
                            if(i.offsetParent !== null || i.getBoundingClientRect().width > 0) { 
                                const r = i.getBoundingClientRect();
                                const cx = r.left + 5;
                                const cy = r.top + 5;
                                i.dispatchEvent(new MouseEvent('mouseover', {bubbles:true, clientX:cx, clientY:cy}));
                                i.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:cx, clientY:cy}));
                                i.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:cx, clientY:cy}));
                                i.click(); 
                                ok=true; 
                            } 
                        });
                        return ok;
                    """)
                    if not csv_clicked:
                        log(f"  -> Attempt {attempt+1}: CSV click failed.")
                        continue
                        

                    # 4. Wait for file in downloads_egz100
                    for i in range(120):
                        time.sleep(1)
                        if i % 30 == 0:
                            # Clear toaster
                            driver.execute_script("""
                                function findT(root){
                                    let res = [];
                                    const walk = n => { if(n.nodeType===1 && (n.innerText||'').includes('準備')) res.push(n); if(n.shadowRoot) walk(n.shadowRoot); let c=n.firstChild; while(c){walk(c);c=c.nextSibling;} };
                                    walk(root); return res;
                                }
                                findT(document.body).forEach(t => { if(t.offsetParent !== null) t.click(); });
                            """)

                        # We don't know the exact base name it downloads as, so we grab the newest CSV
                        files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.csv"))
                        if files and not any(".crdownload" in f for f in files):
                            # Filter files created in the last 2 minutes to ensure we don't grab old ones
                            recent_files = [f for f in files if (time.time() - os.path.getctime(f)) < 120]
                            if recent_files:
                                latest = max(recent_files, key=os.path.getctime)
                                if os.path.getsize(latest) > 100 and filename not in latest:
                                    # Found the new file!
                                    time.sleep(2)
                                    dest = os.path.join(DOWNLOAD_DIR, filename)
                                    if os.path.exists(dest): os.remove(dest) # Replace if exists
                                    shutil.copy2(latest, dest)
                                    os.remove(latest)
                                    log(f"  -> SUCCESS: {filename}")
                                    success = True
                                    break
                    if success: break
                except Exception as e:
                    log(f"  -> ERROR during attempt {attempt+1}: {e}")
            if not success:
                log(f"  -> FAILED to download: {filename}")

        log("EGZ100 EXTRACTION COMPLETE")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_extraction()
