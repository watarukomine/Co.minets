import os, time, logging, json
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO)

def debug_dropdown():
    svc = Service(executable_path=r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.72\msedgedriver.exe")
    opt = webdriver.EdgeOptions()
    opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    driver = webdriver.Edge(service=svc, options=opt)
    
    js = """
    function findRecursive(root) {
        if (root.innerText && (root.innerText.includes('EGZ010') || root.innerText.includes('コントロール'))) return root;
        const frames = root.querySelectorAll('iframe');
        for (let f of frames) {
            try {
                const found = findRecursive(f.contentDocument);
                if (found) return found;
            } catch(e) {}
        }
        return null;
    }
    const dash = findRecursive(document);
    if (!dash) return {error: "Dashboard not found"};
    
    const win = dash.contentWindow || dash;
    const doc = dash.contentDocument || dash;

    // Open Category dropdown (Label is '販売区分')
    const labels = Array.from(doc.querySelectorAll('*')).filter(el => el.innerText === '販売区分');
    if (labels.length === 0) return {error: "Label '販売区分' not found"};
    
    const label = labels[labels.length - 1];
    const ctrl = label.nextElementSibling;
    if (!ctrl) return {error: "Control not found"};
    
    ctrl.click();
    return {ok: true, msg: "Clicked dropdown. Check UI and run again to see items."};
    """
    
    res = driver.execute_script(js)
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    debug_dropdown()
