# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def debug_scan():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe.quicksight-embedding-iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            print("--- SCANNING FOR '期間' ---")
            res = driver.execute_script("""
                const logs = [];
                const walk = n => {
                    if(!n) return;
                    const t = (n.innerText || '').trim();
                    if(t.includes('期間')) {
                        logs.push({tag:n.tagName, id:n.id, text:t.slice(0,50)});
                    }
                    if(n.shadowRoot) walk(n.shadowRoot);
                    let c = n.firstChild; while(c){ walk(c); c = c.nextSibling; }
                };
                walk(document.body);
                return logs;
            """)
            for l in res: print(l)
            driver.save_screenshot("debug_scan.png")
            driver.switch_to.default_content()
            return
    print("Dashboard not found.")

if __name__ == "__main__":
    debug_scan()
