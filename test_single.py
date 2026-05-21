# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

def test_single():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(options=options)
    
    print("Searching for Dashboard...")
    found = False
    for h in driver.window_handles:
        driver.switch_to.window(h)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if "コントロール" in driver.execute_script("return document.body.innerText"):
                    print("Found frame!")
                    found = True; break
                driver.switch_to.default_content()
            except: pass
        if found: break
    
    if not found:
        print("Not found.")
        return

    # Test Param Set
    res = driver.execute_script("""
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        const walk = (n, map={}) => {
            if(!n) return map;
            const text = (n.innerText || '').trim();
            if(['売上/粗利', 'ルート', '販売区分', '支社'].includes(text)) {
                const widget = n.closest('.visual-view, .widget-container, .quicksight-parameter-control, .sheet-control-block');
                if(widget) {
                    const sel = widget.querySelector('#sheet_control_value, .MuiSelect-select');
                    if(sel) map[text] = sel;
                }
            }
            if(n.shadowRoot) walk(n.shadowRoot, map);
            let c = n.firstChild; while(c){ walk(c, map); c = c.nextSibling; }
            return map;
        };
        const selOpt = async (sel, val) => {
            if(!sel) return false;
            console.log('Selecting', val, 'on', sel);
            sel.click(); await sleep(2000);
            const walkItems = (n, items=[]) => {
                if(!n) return items;
                if(n.getAttribute && (n.getAttribute('role')==='option' || n.className.includes('MuiListItem-root'))) items.push(n);
                if(n.shadowRoot) walkItems(n.shadowRoot, items);
                let c = n.firstChild; while(c){ walkItems(c, items); c = c.nextSibling; }
                return items;
            };
            const list = walkItems(document.body);
            const target = list.find(i => i.innerText.trim().includes(val));
            if(target) { target.click(); await sleep(2000); return true; }
            document.body.click(); return false;
        };
        const run = async () => {
            const map = walk(document.body);
            const ok = await selOpt(map['ルート'], 'b-01 販売店');
            return {ok, keys: Object.keys(map)};
        };
        return run();
    """)
    print("Result:", res)

if __name__ == "__main__":
    test_single()
