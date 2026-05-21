from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
try:
    driver = webdriver.Edge(options=options)
    print(f"Total Windows: {len(driver.window_handles)}")
    for h in driver.window_handles:
        driver.switch_to.window(h)
        print(f"Handle: {h} | URL: {driver.current_url} | Title: {driver.title}")
except Exception as e:
    print(f"Error: {e}")
