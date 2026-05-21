import os, time, logging, json
from selenium import webdriver
from selenium.webdriver.edge.service import Service

def get_options():
    svc = Service(executable_path=r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.72\msedgedriver.exe")
    opt = webdriver.EdgeOptions()
    opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(service=svc, options=opt)
    
    js = """
    const sleep = ms => new Promise(res => setTimeout(res, ms));
    const findAllSelects = () => {
        const selects = [];
        const walk = (n) => {
            if(!n) return;
            try {
                if(n.getAttribute && n.getAttribute('data-automation-id') === 'sheet_control_value') {
                    let label = "Unknown";
                    let p = n;
                    while(p && p !== document.body) {
                        const lname = p.querySelector('[data-automation-id="sheet_control_name"]');
                        if(lname) { label = lname.innerText; break; }
                        p = p.parentElement || (p.parentNode && p.parentNode.host);
                    }
                    selects.push({ el: n, label: label ? label.trim() : "Unknown" });
                }
            } catch(e) {}
            if(n.shadowRoot) walk(n.shadowRoot);
            let child = n.firstChild; while(child){ walk(child); child = child.nextSibling; }
        };
        walk(document.body);
        return selects;
    };

    async function main() {
        const ctrls = findAllSelects();
        const results = {};
        for (const c of ctrls) {
            c.el.click(); await sleep(1500);
            const items = Array.from(document.querySelectorAll('li[role="option"]')).map(i => i.innerText.trim());
            results[c.label] = items;
            // Click away
            document.body.click(); await sleep(500);
        }
        return results;
    }
    return main();
    """
    options = driver.execute_script(js)
    print(json.dumps(options, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_options()
