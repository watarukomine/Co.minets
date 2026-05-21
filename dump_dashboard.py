# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def deep_inspect_dashboard():
    print("Connecting to Edge...")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    found = False
    for i in range(10):
        for h in driver.window_handles:
            driver.switch_to.window(h)
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    content = driver.execute_script("return document.body.innerText")
                    if "コントロール" in content:
                        print("Dashboard iframe found. Scanning...")
                        found = True
                        break
                    driver.switch_to.default_content()
                except: pass
            if found: break
        if found: break
        time.sleep(3)
        
    if found:
        print("Expanding controls for deep scan...")
        driver.execute_script("""
            const expand = n => {
                if(!n) return;
                if((n.innerText||'').includes('コントロール') && n.id==='sheet_control_panel_header') {
                    if(n.getAttribute('aria-expanded')==='false') n.click();
                }
                if(n.shadowRoot) expand(n.shadowRoot);
                let c = n.firstChild; while(c){ expand(c); c = c.nextSibling; }
            };
            expand(document.body);
        """)
        time.sleep(5)
        
        print("Walking all nodes including Shadow DOM...")
        nodes = driver.execute_script("""
            const all = [];
            const walk = (n, depth=0) => {
                if(!n) return;
                const nodeInfo = {
                    tag: n.nodeName,
                    id: n.id,
                    cls: n.className,
                    text: (n.innerText || n.textContent || '').slice(0, 50).trim(),
                    val: n.value || '',
                    aria: (n.getAttribute ? n.getAttribute('aria-label') : ''),
                    shadow: !!n.shadowRoot,
                    depth: depth
                };
                if(nodeInfo.tag === 'INPUT' || nodeInfo.tag === 'BUTTON' || nodeInfo.text.includes('2026') || nodeInfo.text.includes('開始')) {
                    all.push(nodeInfo);
                }
                if(n.shadowRoot) walk(n.shadowRoot, depth + 1);
                let c = n.firstChild; while(c){ walk(c, depth); c = c.nextSibling; }
            };
            walk(document.body);
            return all;
        """)
        with open("deep_dashboard_scan.json", "w", encoding="utf-8") as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2)
        print("Scan complete. Saved to deep_dashboard_scan.json")
        driver.save_screenshot("deep_dashboard_scan.png")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    deep_inspect_dashboard()
