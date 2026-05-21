# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def scan():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Edge(options=options)
        for h in driver.window_handles:
            driver.switch_to.window(h)
            try:
                iframes = driver.find_elements(By.CSS_SELECTOR, "iframe.quicksight-embedding-iframe")
                if iframes:
                    driver.switch_to.frame(iframes[0])
                    print(f"Scanning Iframe in window {h}...")
                    
                    results = driver.execute_script("""
                        const data = [];
                        const walk = (n, depth=0) => {
                            if(!n) return;
                            const info = {
                                tag: n.nodeName || '',
                                id: n.id || '',
                                cls: n.className || '',
                                text: (n.innerText || n.textContent || '').slice(0, 100).trim(),
                                val: n.value || '',
                                aria: (n.getAttribute ? n.getAttribute('aria-label') : '') || '',
                                automation: (n.getAttribute ? n.getAttribute('data-automation-id') : '') || '',
                                depth: depth
                            };
                            if(info.tag === 'INPUT' || info.tag === 'BUTTON' || info.text.includes('期間') || info.text.includes('開始') || info.text.includes('終了')) {
                                data.push(info);
                            }
                            if(n.shadowRoot) walk(n.shadowRoot, depth + 1);
                            let c = n.firstChild; while(c){ walk(c, depth); c = c.nextSibling; }
                        };
                        walk(document.body);
                        return data;
                    """)
                    with open("dom_scan_results.json", "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    driver.switch_to.default_content()
                    print(f"Scan complete for window {h}.")
                    return True
            except: pass
    except Exception as e:
        print(f"Scan error: {e}")
    return False

if __name__ == "__main__":
    scan()
