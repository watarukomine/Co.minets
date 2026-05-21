import os, time, logging, json
from selenium import webdriver
from selenium.webdriver.edge.service import Service

def capture():
    svc = Service(executable_path=r"C:\Users\00137012\.cache\selenium\msedgedriver\win64\146.0.3856.72\msedgedriver.exe")
    opt = webdriver.EdgeOptions()
    opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Edge(service=svc, options=opt)
    
    path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\dashboard_state.png"
    driver.save_screenshot(path)
    print(f"Screenshot saved to {path}")

if __name__ == "__main__":
    capture()
