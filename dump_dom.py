# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options

def dump():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Edge(options=options)
        print(f"URL: {driver.current_url}")
        print(f"Title: {driver.title}")
        
        script = """
        const dump = (root, depth=0) => {
            let res = [];
            const walk = (n, d) => {
                if(!n) return;
                if(n.nodeType === 1) {
                    let attrs = '';
                    for(let i=0; i<n.attributes.length; i++) {
                        attrs += `${n.attributes[i].name}="${n.attributes[i].value}" `;
                    }
                    let text = (n.innerText || '').slice(0, 20).replace(/\\n/g, ' ');
                    res.push('  '.repeat(d) + `<${n.tagName} ${attrs}> [${text}]`);
                }
                if(n.shadowRoot) {
                    res.push('  '.repeat(d) + '--- SHADOW ROOT ---');
                    walk(n.shadowRoot, d+1);
                }
                let c = n.firstChild;
                while(c) { walk(c, d+1); c = c.nextSibling; }
            };
            walk(root, depth);
            return res.join('\\n');
        };
        return dump(document.body);
        """
        result = driver.execute_script(script)
        with open("dom_dump.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("Dump saved to dom_dump.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump()
