# -*- coding: utf-8 -*-
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.edge.service import Service

def scan_browser():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(executable_path=r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.72\msedgedriver.exe")
    try:
        driver = webdriver.Edge(options=options, service=service)
        print(f"Total Windows: {len(driver.window_handles)}")
        for h in driver.window_handles:
            driver.switch_to.window(h)
            print(f"Window: {driver.title}")
            # Scan for search box or EGZ010 link
            buttons = driver.find_elements(By.TAG_NAME, "button")
            links = driver.find_elements(By.TAG_NAME, "a")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            
            print(f"      [SYSTEM] Buttons: {[b.text for b in buttons if b.text]}")
            for l in links:
                if "EGZ010" in l.text:
                    print(f"      !!! FOUND EGZ010 LINK: {l.text} !!!")
            
            for i in inputs:
                p = i.get_attribute("placeholder")
                if p and "検索" in p:
                    print(f"      !!! FOUND SEARCH BOX: id={i.get_attribute('id')} placeholder={p} !!!")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"      [SYSTEM] Top-level Iframes: {len(iframes)}")
            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    text = driver.execute_script("return document.body.innerText")
                    # Safe print for utf-8
                    safe_text = text.encode('ascii', 'ignore').decode('ascii')
                    print(f"      [SYSTEM] Iframe {i} text (first 500 chars): {safe_text[:500]}")
                    
                    # ALSO check for any specific Japanese keywords manually without printing them fully
                    if "コントロール" in text: print("      !!! FOUND 'コントロール' !!!")
                    if "売上" in text: print("      !!! FOUND '売上' !!!")
                    if "Amazon QuickSight" in text: print("      !!! FOUND 'Amazon QuickSight' !!!")
                    
                    driver.switch_to.parent_frame()
                except Exception as e:
                    print(f"      [SYSTEM] Error in Iframe {i}: {e}")
                    driver.switch_to.default_content()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    scan_browser()
