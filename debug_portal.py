from selenium import webdriver
from selenium.webdriver.edge.options import Options
import json

options = Options()
options.add_argument('--remote-debugging-port=9222')
options.debugger_address = '127.0.0.1:9222'
driver = webdriver.Edge(options=options)

js = """
const text = 'EGZ010';
const elements = Array.from(document.querySelectorAll('*')).filter(e => (e.innerText||'').includes(text) && e.children.length < 5);
return elements.map(e => ({
    tag: e.tagName,
    text: e.innerText,
    html: e.outerHTML.substring(0, 500),
    rect: e.getBoundingClientRect()
}));
"""
results = driver.execute_script(js)
print(json.dumps(results, indent=2, ensure_ascii=False))
