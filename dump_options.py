# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def dump_dropdown_options():
    print("Connecting to Edge to dump '販売区分' options...")
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
        print("Dashboard found. Identifying '販売区分' dropdown...")
        options_list = driver.execute_script("""
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            const walk = (n, text) => {
                if(!n) return null;
                if((n.innerText || '').includes(text) && n.className.includes('parameter-control-label')) return n;
                if(n.shadowRoot) { let r = walk(n.shadowRoot, text); if(r) return r; }
                let c = n.firstChild; while(c){ let r = walk(c, text); if(r) return r; c = c.nextSibling; }
                return null;
            };

            const dump = async () => {
                // Find label then its select
                const label = walk(document.body, '販売区分');
                if(!label) return ["Label not found"];
                const container = label.closest('.quicksight-parameter-control');
                if(!container) return ["Container not found"];
                const select = container.querySelector('.MuiSelect-select');
                if(!select) return ["Select box not found"];
                
                select.click();
                await sleep(3000);
                
                // Read from portal
                const items = Array.from(document.querySelectorAll('.MuiListItem-root, [role="option"]'));
                const texts = items.map(i => i.innerText.trim()).filter(t => t);
                
                // Close dropdown
                document.body.click(); 
                return texts;
            };
            return dump();
        """)
        with open("販売区分_options.json", "w", encoding="utf-8") as f:
            json.dump(options_list, f, ensure_ascii=False, indent=2)
        print(f"Dumped {len(options_list)} options. Total: {len(options_list)}")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    dump_dropdown_options()
