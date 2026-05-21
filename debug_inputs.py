from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
try:
    driver = webdriver.Edge(options=options)
    print(f"URL: {driver.current_url}")
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for i, e in enumerate(inputs):
        print(f"Input {i}: id={e.get_attribute('id')}, placeholder={e.get_attribute('placeholder')}, class={e.get_attribute('class')}")
except Exception as e:
    print(f"Error: {e}")
