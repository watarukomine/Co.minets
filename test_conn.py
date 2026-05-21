from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
import os

def test():
    driver_path = r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.78\msedgedriver.exe"
    if not os.path.exists(driver_path):
        print(f"Driver not found at {driver_path}")
        return

    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(executable_path=driver_path)
    
    print(f"Attempting to connect with driver {driver_path}...")
    try:
        driver = webdriver.Edge(options=options, service=service)
        print(f"Connected! Page title: {driver.title}")
        driver.quit()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test()
