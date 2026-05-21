# -*- coding: utf-8 -*-
import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service

def dump_portal_info():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(executable_path=r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.72\msedgedriver.exe")
    try:
        driver = webdriver.Edge(options=options, service=service)
        print("Connected to Edge session.")
        
        # Helper to find and click control to open dropdown
        def open_dropdown(dr, label_part):
            js = r"""
            const labelPart = arguments[0];
            const walk = (n) => {
                if(!n) return null;
                if(n.getAttribute && n.getAttribute('data-automation-id') === 'sheet_control_value') {
                    let p = n;
                    while(p && p !== document.body) {
                        const lname = p.querySelector('[data-automation-id="sheet_control_name"]');
                        if(lname && lname.innerText.includes(labelPart)) return n;
                        p = p.parentElement || (p.parentNode && p.parentNode.host);
                    }
                }
                if(n.shadowRoot) { let res = walk(n.shadowRoot); if(res) return res; }
                let c = n.firstChild; while(c){ let res = walk(c); if(res) return res; c = c.nextSibling; }
                return null;
            };
            const target = walk(document.body);
            if(target) { target.click(); return true; }
            return false;
            """
            # Try top level then iframes
            if dr.execute_script(js, label_part): return True
            iframes = dr.find_elements(By.TAG_NAME, "iframe")
            for ifr in iframes:
                try:
                    dr.switch_to.frame(ifr)
                    if dr.execute_script(js, label_part): return True
                    dr.switch_to.parent_frame()
                except: dr.switch_to.parent_frame()
            return False

        print("Opening '売上/粗利' dropdown...")
        if not open_dropdown(driver, "売上"):
            print("Failed to open dropdown.")
        
        time.sleep(3)
        print("Scanning for '売上' or '粗利' in all frames...")

        js_scan = r"""
        const results = [];
        const walk = (n, framePath) => {
            if(!n) return;
            const txt = (n.innerText || "").trim();
            if(txt === '売上' || txt === '粗利') {
                const info = {
                    tag: n.nodeName,
                    role: n.getAttribute ? n.getAttribute('role') : null,
                    auto: n.getAttribute ? n.getAttribute('data-automation-id') : null,
                    classes: n.className,
                    path: framePath,
                    visible: n.offsetWidth > 0 && n.offsetHeight > 0
                };
                results.push(info);
            }
            if(n.shadowRoot) walk(n.shadowRoot, framePath + ' > SHADOW');
            let c = n.firstChild; while(c){ walk(c, framePath); c = c.nextSibling; }
        };
        walk(document.body, 'TOP');
        return results;
        """

        driver.switch_to.default_content()
        all_hits = driver.execute_script(js_scan)
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, ifr in enumerate(iframes):
            try:
                driver.switch_to.frame(ifr)
                hits = driver.execute_script(js_scan.replace('TOP', f'IFRAME[{i}]'))
                all_hits.extend(hits)
                driver.switch_to.parent_frame()
            except: driver.switch_to.parent_frame()

        print(f"Grand Total Hits: {len(all_hits)}")
        for i, h in enumerate(all_hits):
            print(f"Hit {i+1}: {json.dumps(h, ensure_ascii=False)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_portal_info()
