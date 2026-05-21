from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
try:
    driver = webdriver.Edge(options=options)
    print(f"Current URL: {driver.current_url}")
    driver.save_screenshot("diagnose_current.png")
    print("Screenshot saved to diagnose_current.png")
except Exception as e:
    print(f"Error: {e}")
