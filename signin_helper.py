import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

print("="*50)
print(" Sign-in Helper (Remote Debugging Mode)")
print("="*50)

# Edgeをデバッグポート付きで再起動するための案内
print("\nTMP-One のボット検知を回避するため、以下の手順で進めてください：")
print("-" * 50)
print("1. 現在開いているすべての Edge ウィンドウを完全に閉じてください。")
print("2. 以下のコマンドをコピーして、別のコマンドプロンプトで実行してください：")
print(r'   start msedge --remote-debugging-port=9222 --user-data-dir="C:\Users\00137012\.tmp_one_selenium_profile_2"')
print("-" * 50)
print("\n上記を実行し、Edge が起動したら Enter キーを押してください。")
input(">>> 準備ができたら Enter を押してください...")

options = Options()
# 起動済みのブラウザに接続
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    print("Edge に接続中...")
    driver = webdriver.Edge(options=options)
    print("✅ 接続成功！")
    
    # ポータルへ遷移
    print("ポータル画面へ移動します...")
    driver.get("https://tmp-one.jp/portal/")
    
    print("\nブラウザ上で TMP-One にログインしてください。")
    print("ログイン完了後、このウィンドウを閉じるか Ctrl+C を押すと、自動抽出が再開可能になります。")
    
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nHelper を終了します。")
        # 接続解除のみ（ブラウザは閉じない）

except Exception as e:
    print(f"\n❌ 接続失敗: {e}")
    print("Edge が --remote-debugging-port=9222 付きで起動されているか確認してください。")
    input("\nプログラムを終了するには Enter を押してください...")
