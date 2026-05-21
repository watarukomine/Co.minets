# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def deep_scan_v2():
    print("Connecting to Edge...")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe.quicksight-embedding-iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            print("Dashboard Iframe found. Expanding controls first...")
            # Try to expand
            driver.execute_script("""
                const walk = n => {
                    if(!n) return null;
                    if((n.innerText || '').includes('コントロール') && n.id === 'sheet_control_panel_header') {
                        const expanded = n.getAttribute('aria-expanded') === 'true';
                        if(!expanded) { n.click(); return 'clicked'; }
                        return 'already_expanded';
                    }
                    if(n.shadowRoot) { let r = walk(n.shadowRoot); if(r) return r; }
                    let c = n.firstChild; while(c){ let r = walk(c); if(r) return r; c = c.nextSibling; }
                    return null;
                };
                walk(document.body);
            """)
            time.sleep(5)
            
            print("Scanning all inputs and buttons specifically...")
            data = driver.execute_script("""
                const res = [];
                const walk = (n, depth=0) => {
                    if(!n) return;
                    if(n.tagName === 'INPUT' || n.tagName === 'BUTTON' || (n.innerText||'').includes('期間')) {
                        res.push({
                            tag: n.tagName,
                            id: n.id,
                            cls: n.className,
                            text: (n.innerText || '').slice(0, 50).trim(),
                            val: n.value || '',
                            placeholder: n.placeholder || '',
                            aria: n.getAttribute ? n.getAttribute('aria-label') : '',
                            depth: depth
                        });
                    }
                    if(n.shadowRoot) walk(n.shadowRoot, depth + 1);
                    let c = n.firstChild; while(c){ walk(c, depth); c = c.nextSibling; }
                };
                walk(document.body);
                return res;
            """)
            with open("iframe_scan_v2.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Scan complete. Saved to iframe_scan_v2.json")
            driver.save_screenshot("iframe_scan_v2.png")
            driver.switch_to.default_content()
            return

if __name__ == "__main__":
    deep_scan_v2()
