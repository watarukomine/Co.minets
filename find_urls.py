import time
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument(r"user-data-dir=C:\Users\00137012\.tmp_one_selenium_profile")
options.add_argument("--headless=new")

driver = webdriver.Edge(options=options)
try:
    print("Navigating to portal...")
    driver.get("https://report.tmp-one.com/portal#")
    time.sleep(10)
    
    links = driver.execute_script("""
        const anchors = Array.from(document.querySelectorAll('a'));
        return anchors.map(a => a.href + " | " + a.innerText).filter(text => text.includes('EGZ100'));
    """)
    print("Direct URLs found:", set(links))
    
    # Also dump all hrefs just in case
    all_links = driver.execute_script("return Array.from(document.querySelectorAll('a')).map(a => a.href);")
    print("Total links on page:", len(all_links))
finally:
    driver.quit()
