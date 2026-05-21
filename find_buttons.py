# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def find_buttons():
    print("Connecting to Edge to find EXPORT buttons...")
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
        print("Dashboard found. Dumping all potential menu buttons...")
        buttons = driver.execute_script("""
            const btns = [];
            const walk = (n, depth=0) => {
                if(!n) return;
                const tag = n.tagName;
                const id = n.id || '';
                let cls = '';
                if(n.className) {
                    if(typeof n.className === 'string') cls = n.className;
                    else if(n.className.baseVal !== undefined) cls = n.className.baseVal;
                }
                const auto = (n.getAttribute ? n.getAttribute('data-automation-id') : '') || '';
                const aria = (n.getAttribute ? n.getAttribute('aria-label') : '') || '';
                const text = (n.innerText || '').trim().slice(0, 30);
                
                if(tag === 'BUTTON' || tag === 'SVG' || 
                   cls.toLowerCase().includes('icon') || cls.toLowerCase().includes('button') || 
                   auto.toLowerCase().includes('menu') || aria.includes('メニュー')) {
                    btns.push({tag, id, cls, auto, aria, text, depth});
                }
                
                if(n.shadowRoot) walk(n.shadowRoot, depth + 1);
                let c = n.firstChild; while(c){ walk(c, depth); c = c.nextSibling; }
            };
            walk(document.body);
            return btns;
        """)
        with open("button_scan.json", "w", encoding="utf-8") as f:
            json.dump(buttons, f, ensure_ascii=False, indent=2)
        print(f"Found {len(buttons)} potential buttons. Saved to button_scan.json")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    from selenium.webdriver.common.by import By
    find_buttons()
