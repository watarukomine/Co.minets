import time
import json
from selenium import webdriver
from selenium.webdriver.edge.options import Options

def main():
    print("ブラウザを起動しています...")
    
    options = Options()
    # ネットワークログをキャプチャするための設定
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.set_capability("ms:loggingPrefs", {"performance": "ALL"})
    
    # ブラウザが閉じないようにする
    options.add_experimental_option("detach", True)
    
    # 「自動テストソフトウェアによって制御されています」のバーを消し、自動操縦ブロックを回避しやすくする
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Edge(options=options)
    except Exception as e:
        print(f"Edgeドライバーの起動に失敗しました: {e}")
        return

    print("=========================================================")
    print("ブラウザが起動しました。")
    print("TMP-ONEのポータルに自動遷移します...")
    
    # 自動でTMP-ONEへアクセス
    try:
        driver.get("https://report.tmp-one.com/portal")
    except Exception as e:
        print(f"アクセスに失敗しました: {e}")

    print("---------------------------------------------------------")
    print("1. そのままログインし、ダッシュボードを開いてください。")
    print("2. データの【検索】や【CSVダウンロード】ボタンを押してみてください。")
    print("3. 新しくログが追加されたら、それが対象のデータです。")
    print("=========================================================")
    print("ネットワーク監視待機中...\n")

    processed_requests = set()

    try:
        while True:
            time.sleep(2)
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    log_data = json.loads(entry["message"])["message"]
                    
                    if log_data["method"] == "Network.responseReceived":
                        params = log_data["params"]
                        response = params.get("response", {})
                        url = response.get("url", "")
                        req_id = params.get("requestId")
                        resp_type = params.get("type", "")
                        
                        # 画像やフォント、不要なスクリプト等のノイズを排除し、
                        # 動的なデータ通信（XHR, Fetch, Document）のみをすべて検知する
                        # XHRとFetch(実際のデータ通信)のみをフィルタリング。HTML(Document)や画像、フォントはノイズになるので完全に除外
                        if resp_type in ["XHR", "Fetch"]:
                            
                            # base64の画像データなどが混ざるのを徹底排除
                            if url.startswith("data:") or "font" in url.lower() or ".b2clogin.com" in url.lower():
                                continue

                            # ただし、明らかに不要な拡張子のものはスキップ
                            if url.endswith((".js", ".css", ".png", ".jpg", ".svg", ".woff2", ".ico")):
                                continue
                                
                            if req_id not in processed_requests:
                                processed_requests.add(req_id)
                                print(f"[データ通信検知] Type: {resp_type} | URL: {url}")
                                
                                # レスポンスボディの取得を試みる
                                try:
                                    body_data = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req_id})
                                    body = body_data.get('body', '')
                                    if body:
                                        print(f"   >>> [サンプル]: {body[:250]}...")
                                except Exception as cdp_err:
                                    pass
                                print("-" * 70)
                except Exception as e:
                    pass

    except KeyboardInterrupt:
        print("\nキャプチャを終了します。")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
