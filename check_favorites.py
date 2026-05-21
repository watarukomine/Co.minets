import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
import os

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Edge(options=options)
try:
    print("Navigating to portal...")
    driver.get("https://report.tmp-one.com/portal#")
    time.sleep(10)
    
    print("Saving screenshot...")
    path = r"C:\Users\00137012\.gemini\antigravity\brain\c42f2c71-f35d-4389-9e30-17ff8c173dcb\favorites_snapshot.png"
    driver.save_screenshot(path)
    
    print("Getting text...")
    favorites = driver.execute_script("""
        const items = Array.from(document.querySelectorAll('span')).filter(el => {
            const btn = el.closest('button');
            const aria = btn ? btn.getAttribute('aria-label') : '';
            return aria && aria.includes('お気に入り');
        });
        return items.map(i => i.innerText).filter(t => t.trim().length > 0);
    """)
    print("Found favorites:", favorites)
finally:
    driver.quit()
