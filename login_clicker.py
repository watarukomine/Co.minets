from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time
import os

ARTIFACT_DIR = r"C:\Users\00137012\.gemini\antigravity\brain\c42f2c71-f35d-4389-9e30-17ff8c173dcb"

options = Options()
options.add_argument('--remote-debugging-port=9222')
options.debugger_address = '127.0.0.1:9222'

try:
    driver = webdriver.Edge(options=options)
    print(f"Current URL: {driver.current_url}")
    
    # Try to find login button
    script = """
    function findLoginButton(root){
        let found = null;
        const walk = n => {
            if(found) return;
            let text = '';
            if(n.nodeType === 3) text = n.textContent || '';
            if(n.nodeType === 1) text = (n.innerText || n.value || n.getAttribute('aria-label') || '');
            if(text.includes('ソーシャルアカウント') || text.includes('Social')) {
                found = (n.nodeType === 3 ? n.parentElement : n);
                return;
            }
            if(n.shadowRoot) walk(n.shadowRoot);
            let c = n.firstChild;
            while(c){ walk(c); c = c.nextSibling; }
        };
        walk(root);
        if(found) {
            found.scrollIntoView({block:'center'});
            found.click();
            return true;
        }
        return false;
    }
    return findLoginButton(document.body);
    """
    
    res = driver.execute_script(script)
    print(f"Login button click result: {res}")
    
    if not res:
        # Check if we are stuck on "Loading"
        body_text = driver.execute_script("return document.body.innerText")
        if "読み込み中" in body_text:
            print("Still loading. Refreshing...")
            driver.refresh()
            time.sleep(10)
            res = driver.execute_script(script)
            print(f"Retry login button click result: {res}")
            
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "after_login_click_attempt_v2.png"))

except Exception as e:
    print(f"Error: {e}")
