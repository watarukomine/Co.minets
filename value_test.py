# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

EXPECTED_OLD_VAL = "2026/02/28"
NEW_VAL = "2026/02/15"

def run_value_based_test():
    print(f"Connecting to Edge... Searching for input with value '{EXPECTED_OLD_VAL}'")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    found = False
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if "コントロール" in driver.execute_script("return document.body.innerText"):
                    found = True; break
                driver.switch_to.default_content()
            except: pass
        if found: break
    
    if found:
        print("Dashboard found. Searching by value...")
        res = driver.execute_script(f"""
            const findInputByVal = (val) => {{
                const walk = n => {{
                    if(!n) return null;
                    if(n.tagName === 'INPUT' && n.value === val) return n;
                    if(n.shadowRoot) {{ let r = walk(n.shadowRoot); if(r) return r; }}
                    let c = n.firstChild; while(c){{ let r = walk(c); if(r) return r; c = c.nextSibling; }}
                    return null;
                }};
                return walk(document.body);
            }};
            
            const target = findInputByVal('{EXPECTED_OLD_VAL}');
            if(target) {{
                target.focus(); target.click(); target.value = '';
                document.execCommand('insertText', false, '{NEW_VAL}');
                target.dispatchEvent(new Event('change', {{bubbles:true}}));
                return true;
            }}
            return false;
        """)
        print(f"Value-based Set Result: {res}")
        time.sleep(5)
        driver.save_screenshot("value_test_result.png")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    run_value_based_test()
