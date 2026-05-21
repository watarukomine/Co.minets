# debug_controls.py
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
try:
    driver = webdriver.Edge(options=options)
    # Recursively find dashboard context
    def find_context(d):
        if "EGZ010" in d.execute_script("return document.body.innerText"):
            return True
        iframes = d.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                d.switch_to.frame(iframe)
                if find_context(d): return True
                d.switch_to.parent_frame()
            except: pass
        return False

    if find_context(driver):
        print("Switched to EGZ010 context.")
        html = driver.execute_script("return document.body.innerHTML")
        with open("dump.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Dumped innerHTML to dump.html")
    else:
        print("Context not found.")

except Exception as e:
    print(f"Error: {e}")
