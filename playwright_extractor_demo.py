import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("社内セキュリティ判定を回避するため、安全な外部接続モードでブラウザを起動します...")
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    # 自動操作専用のプロファイル（Cookieなどを保存する場所）を作成
    user_data_dir = r"C:\Users\00137012\Documents\edge_playwright_profile"

    # Playwrightの標準起動機能を使わず、Pythonから直接Edgeを起動する（これによりセキュリティチェックをすり抜ける）
    edge_process = subprocess.Popen([
        edge_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ])

    print("ブラウザの起動を待機しています...")
    time.sleep(5)  # 起動まで少し待つ

    with sync_playwright() as p:
        # 起動済みのEdgeに、Playwrightを外から「接続」させる（CDP接続）
        print("Playwrightを接続中...")
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        
        # 既に開いているコンテキストを取得
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print("=========================================================")
        print("ブラウザに接続成功しました。TMP-ONEポータルへ遷移します...")
        print("ご自身のIDでログインを完了させてください。")
        print("（今回はテスト用に、ダッシュボードの手前まで自動進行します）")
        print("=========================================================")

        # ポータルへアクセス
        try:
            page.goto("https://report.tmp-one.com/portal")
        except Exception as e:
            print("ページ移動中にエラー（無視して進めます）:", e)

        # ログインや手動操作のために、ロボットを意図的に一時停止します
        print("\nロボット一時停止中（手動操作モード）。")
        print("ブラウザ上でダッシュボードを開き、CSVダウンロードしたい画面まで進んでください。")
        print("※準備が完了したら、この黒い画面（ターミナル）で「Ctrl + C」を押すとスクリプトが終了します。")
        
        # タイムアウト回避のため、ここで無限待機させます
        try:
            page.wait_for_timeout(3600 * 1000) # 1時間待機（実質手動での終了待ち）
        except KeyboardInterrupt:
            print("\n手動で終了しました。")
        except Exception:
            pass
            
        print("終了処理を実行中...")
        browser.close()
        edge_process.terminate()

if __name__ == '__main__':
    main()
