# -*- coding: utf-8 -*-
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

START_DATE = "2023/04/01"
END_DATE = datetime.now().strftime("%Y/%m/%d")

def run_full_date_set():
    print(f"Connecting to Edge... Full Date Set: {START_DATE} ~ {END_DATE}")
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
        print("Dashboard found. Starting full sequence...")
        res = driver.execute_script(f"""
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            const walk = (n, text) => {{
                if(!n) return null;
                if((n.innerText || '').includes(text) && n.id === 'sheet_control_panel_header') return n;
                if(n.shadowRoot) {{ let r = walk(n.shadowRoot, text); if(r) return r; }}
                let c = n.firstChild; while(c){{ let r = walk(c, text); if(r) return r; c = c.nextSibling; }}
                return null;
            }};

            const doFullSet = async () => {{
                // 1. Expand
                const header = walk(document.body, 'コントロール');
                if(header && header.getAttribute('aria-expanded')==='false') {{
                    header.click();
                    await sleep(3000);
                }}

                // 2. Set Start
                const findAndSet = async (oldVal, newVal) => {{
                    const find = n => {{
                        if(!n) return null;
                        if(n.tagName === 'INPUT' && n.value && n.value.includes('20')) return n; // Match any date-like input
                        if(n.shadowRoot) {{ let r = find(n.shadowRoot); if(r) return r; }}
                        let c = n.firstChild; while(c){{ let r = find(c); if(r) return r; c = c.nextSibling; }}
                        return null;
                    }};
                    // Since there are two inputs, let's just find ALL date-like inputs
                    const inputs = [];
                    const walkAll = n => {{
                        if(!n) return;
                        if(n.tagName === 'INPUT' && n.value && n.value.includes('20')) inputs.push(n);
                        if(n.shadowRoot) walkAll(n.shadowRoot);
                        let c = n.firstChild; while(c){{ walkAll(c); c = c.nextSibling; }}
                    }};
                    walkAll(document.body);
                    
                    if(inputs.length >= 2) {{
                        // Assuming 1st is start, 2nd is end
                        // Start
                        inputs[0].focus(); inputs[0].click(); inputs[0].value = '';
                        document.execCommand('insertText', false, '{START_DATE}');
                        inputs[0].dispatchEvent(new Event('change', {{bubbles:true}}));
                        await sleep(2000);
                        // End
                        inputs[1].focus(); inputs[1].click(); inputs[1].value = '';
                        document.execCommand('insertText', false, '{END_DATE}');
                        inputs[1].dispatchEvent(new Event('change', {{bubbles:true}}));
                        await sleep(2000);
                        return true;
                    }}
                    return false;
                }};
                
                const success = await findAndSet();

                // 3. Collapse
                if(header && header.getAttribute('aria-expanded')==='true') {{
                    header.click();
                    await sleep(2000);
                }}
                return success;
            }};
            return doFullSet();
        """)
        print(f"Full Date Set Result: {res}")
        time.sleep(5)
        driver.save_screenshot("step_1_final_full_dates.png")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    run_full_date_set()
