import os
import sys
import io
import time
import json

# Windows cp932コンソール対策
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except:
    pass

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

BASE_URL = "https://report.tmp-one.com/portal#"
TARGET_DASHBOARD = "EGZ010_日別実績"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".tmp_one_selenium_profile")

options = Options()
options.add_argument(f"user-data-dir={USER_DATA_DIR}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

print("Launching Edge...")
driver = webdriver.Edge(options=options)

try:
    driver.maximize_window()
    driver.get(BASE_URL)
    print("Waiting for portal to load...")
    time.sleep(5)
    
    # Handle login if needed
    try:
        page_text = driver.page_source.lower()
        if "employee" in page_text or "ソーシャル" in page_text:
            print("Login screen detected, clicking login...")
            xpaths = ["//*[normalize-space(text())='TMP Employee Login']", "//*[contains(text(), 'Employee Login')]"]
            for xpath in xpaths:
                try:
                    el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    if el.is_displayed():
                        el.click()
                        time.sleep(25)
                        break
                except: continue
    except: pass
    
    time.sleep(10)
    
    # Switch to iframe
    def switch_to_qs_iframe(d):
        d.switch_to.default_content()
        iframes = d.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src")
            if src and ("quicksight" in src.lower() or "dashboard" in src.lower() or "amazon" in src.lower()):
                d.switch_to.frame(iframe)
                return True
        return False
    
    if not switch_to_qs_iframe(driver):
        print("Iframe not found, waiting...")
        time.sleep(15)
    
    # Click dashboard
    try:
        dashboard_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{TARGET_DASHBOARD}')]"))
        )
        dashboard_link.click()
        print(f"Opened dashboard: {TARGET_DASHBOARD}")
        time.sleep(20)
    except Exception as e:
        print(f"Dashboard link not found or already open: {e}")
    
    # Re-switch to iframe after dashboard opens
    switch_to_qs_iframe(driver)
    time.sleep(15)
    
    # --- DEBUG: Find all buttons and their aria-labels ---
    print("\n=== DEBUGGING: Finding all buttons ===")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Total buttons found: {len(buttons)}")
    for i, btn in enumerate(buttons):
        aria_label = btn.get_attribute("aria-label") or ""
        title = btn.get_attribute("title") or ""
        text = btn.text.strip()[:50] if btn.text else ""
        classes = btn.get_attribute("class") or ""
        displayed = btn.is_displayed()
        if aria_label or title or text:
            print(f"  Button {i}: aria-label='{aria_label}' title='{title}' text='{text}' displayed={displayed} class='{classes[:80]}'")
    
    print("\n=== DEBUGGING: Finding elements with 'export', 'CSV', 'オプション' text ===")
    all_els = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'export') or contains(., 'CSV') or contains(., 'エクスポート') or contains(., 'csv') or contains(., 'オプション')]")
    print(f"Found {len(all_els)} elements")
    for i, el in enumerate(all_els):
        tag = el.tag_name
        text = el.text.strip()[:100] if el.text else ""
        aria_label = el.get_attribute("aria-label") or ""
        displayed = el.is_displayed()
        print(f"  [{i}] <{tag}> aria-label='{aria_label}' text='{text}' displayed={displayed}")
    
    # Try to find 3-dot menu / options button by various strategies
    print("\n=== DEBUGGING: Trying to find and click the three-dot menu ===")
    
    # Strategy 1: SVG with three vertical dots pattern
    svgs = driver.find_elements(By.CSS_SELECTOR, "button svg, button[aria-label] svg")
    print(f"Found {len(svgs)} SVG elements inside buttons")
    
    # Strategy 2: aria-label contains 'menu' or 'more' or 'option' 
    menu_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'menu') or contains(@aria-label, 'more') or contains(@aria-label, 'Menu') or contains(@aria-label, 'More') or contains(@aria-label, 'オプション') or contains(@aria-label, 'options') or contains(@aria-label, 'Options')]")
    print(f"Menu/More buttons found: {len(menu_buttons)}")
    for i, mb in enumerate(menu_buttons):
        print(f"  [{i}] aria-label='{mb.get_attribute('aria-label')}' displayed={mb.is_displayed()}")
    
    # Strategy 3: data-testid containing 'menu' or 'options'
    testid_btns = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='menu'], [data-testid*='option'], [data-testid*='export']")
    print(f"TestID buttons: {len(testid_btns)}")
    for i, tb in enumerate(testid_btns):
        print(f"  [{i}] data-testid='{tb.get_attribute('data-testid')}' tag={tb.tag_name}")
    
    # Strategy 4: Find any element with an SVG that has 3 circles (three-dot icon)
    print("\n=== DEBUGGING: Checking for '...' / ellipsis icons ===")
    ellipsis_els = driver.find_elements(By.XPATH, "//*[contains(@class, 'ellipsis') or contains(@class, 'dots') or contains(@class, 'kebab') or contains(@class, 'Kebab')]")
    print(f"Ellipsis class elements: {len(ellipsis_els)}")
    
    # Strategy 5: QuickSight specific - find the visual's menu
    print("\n=== DEBUGGING: Looking for QuickSight visual header ===")
    qs_btns = driver.find_elements(By.CSS_SELECTOR, ".visual-header button, [class*='VisualHeader'] button, [class*='visual-menu'] button")
    print(f"QuickSight visual header buttons: {len(qs_btns)}")
    for i, qb in enumerate(qs_btns):
        print(f"  [{i}] aria-label='{qb.get_attribute('aria-label')}' class='{(qb.get_attribute('class') or '')[:80]}' displayed={qb.is_displayed()}")
    
    # Dump a portion of the page source
    print("\n=== Page source snippet (searching for 'export' and 'CSV') ===")
    page_src = driver.page_source
    # Find all occurrences of 'export', 'csv', 'エクスポート' in the page source
    import re
    for keyword in ['CSVにエクスポート', 'CSV にエクスポート', 'export', 'Export', 'オプション', 'options']:
        positions = [m.start() for m in re.finditer(re.escape(keyword), page_src, re.IGNORECASE)]
        if positions:
            print(f"  '{keyword}' found at {len(positions)} positions")
            for pos in positions[:3]:  # Show first 3
                snippet = page_src[max(0,pos-50):pos+len(keyword)+50]
                print(f"    ...{snippet}...")
        else:
            print(f"  '{keyword}' NOT found in page source")
    
    print("\nDone! Keeping browser open for 30 seconds for manual inspection...")
    time.sleep(30)
    
finally:
    driver.quit()
    print("Browser closed.")
