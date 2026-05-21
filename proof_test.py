# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options

TEST_END_DATE = "2026/02/15" # Specific date for proof

def run_proof_test():
    print(f"Step 1: Connecting to Edge for PROOF TEST (Target: {TEST_END_DATE})...")
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
        print("Dashboard found. Attempting to change ONLY End Date...")
        res = driver.execute_script(f"""
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            const walk = (n, text) => {{
                if(!n) return null;
                if((n.innerText || '').includes(text) && n.id === 'sheet_control_panel_header') return n;
                if(n.shadowRoot) {{ let r = walk(n.shadowRoot, text); if(r) return r; }}
                let c = n.firstChild; while(c){{ let r = walk(c, text); if(r) return r; c = c.nextSibling; }}
                return null;
            }};

            const doProof = async () => {{
                const header = walk(document.body, 'コントロール');
                if(header) {{
                    header.click();
                    await sleep(3000);
                }}

                const findInp = (label) => {{
                    const find = n => {{
                        if(!n) return null;
                        if((n.innerText||'').includes('期間') && (n.innerText||'').includes(label)) {{
                            const parent = n.closest('.quicksight-parameter-control, .sheet-control-panel-body, .parameter-control-container');
                            if(parent) return parent.querySelector('input');
                        }}
                        if(n.shadowRoot) {{ let r = find(n.shadowRoot); if(r) return r; }}
                        let c = n.firstChild; while(c){{ let r = find(c); if(r) return r; c = c.nextSibling; }}
                        return null;
                    }};
                    return find(document.body);
                }};

                const endInp = findInp('終了');
                if(endInp) {{
                    endInp.focus(); endInp.click(); 
                    endInp.value = '';
                    document.execCommand('insertText', false, '{TEST_END_DATE}');
                    endInp.dispatchEvent(new Event('change', {{bubbles:true}}));
                    await sleep(2000);
                }}

                if(header) {{
                    header.click();
                }}
                return !!endInp;
            }};
            return doProof();
        """)
        time.sleep(10)
        driver.save_screenshot("proof_test_result.png")
        print(f"Proof Test Result: {res}")
        driver.switch_to.default_content()
    else:
        print("Dashboard not found.")

if __name__ == "__main__":
    # Import By locally to avoid name error in script
    from selenium.webdriver.common.by import By
    run_proof_test()
