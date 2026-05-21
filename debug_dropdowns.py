# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def debug_dropdowns():
    print("Connecting to Edge for Dropdown Debug...")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if "コントロール" in driver.execute_script("return document.body.innerText"):
                    res = driver.execute_script("""
                        const walk = (n, results=[]) => {
                            if(!n) return;
                            const text = (n.innerText || '').trim();
                            const cls = n.className || '';
                            if(text.length > 0 && text.length < 50) {
                                results.push({tag: n.tagName, text: text, class: cls});
                            }
                            if(n.shadowRoot) walk(n.shadowRoot, results);
                            let c = n.firstChild; while(c){ walk(c, results); c = c.nextSibling; }
                            return results;
                        };
                        return walk(document.body);
                    """)
                    with open("dropdown_debug.json", "w", encoding="utf-8") as f:
                        json.dump(res, f, ensure_ascii=False, indent=2)
                    print(f"Dumped {len(res)} elements to dropdown_debug.json")
                    return
                driver.switch_to.default_content()
            except: pass

if __name__ == "__main__":
    debug_dropdowns()
