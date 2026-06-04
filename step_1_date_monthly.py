# -*- coding: utf-8 -*-
import sys
import os
import json
import time
import calendar
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_target_period(target_arg=None):
    # デフォルトは前月
    now = datetime.now()
    if now.month == 1:
        default_year = now.year - 1
        default_month = 12
    else:
        default_year = now.year
        default_month = now.month - 1
        
    target = f"{default_year}/{default_month:02d}"
    
    if target_arg:
        arg = target_arg.strip()
        arg = arg.replace("-", "/")
        parts = arg.split("/")
        if len(parts) == 2 and len(parts[0]) == 4 and parts[1].isdigit():
            y = int(parts[0])
            m = int(parts[1])
            if 1 <= m <= 12:
                target = f"{y}/{m:02d}"
            else:
                print(f"[警告] 月の指定が不正です: {arg}。デフォルトの前月を使用します。")
        else:
            print(f"[警告] 引数のフォーマットが不正です: {arg}。'YYYY/MM' 形式で指定してください。デフォルトの前月を使用します。")
            
    year, month = map(int, target.split("/"))
    _, last_day = calendar.monthrange(year, month)
    
    start_date = f"{year}/{month:02d}/01"
    end_date = f"{year}/{month:02d}/{last_day:02d}"
    return start_date, end_date

def ensure_dashboard_open(driver, target_dashboard="EGZ010"):
    # 1. 既に開いているか確認
    found = False
    for h in driver.window_handles:
        try:
            driver.switch_to.window(h)
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    if "コントロール" in driver.execute_script("return document.body.innerText"):
                        found = True
                        break
                    driver.switch_to.default_content()
                except:
                    pass
            if found:
                break
        except:
            pass
            
    if found:
        print("✅ すでにQuickSightダッシュボードが開かれています。")
        return True
        
    # 2. 開いていない場合、ポータルにアクセス
    print("QuickSightダッシュボードが開かれていません。自動ログイン・遷移を開始します...")
    portal_url = "https://report.tmp-one.com/portal#"
    
    if not driver.window_handles:
        print("[エラー] ウィンドウが見つかりません。")
        return False
        
    driver.switch_to.window(driver.window_handles[0])
    
    # 常に再ロードして確実に最新のコンテンツを読み込む
    print(f"ポータルへ移動します: {portal_url}")
    driver.get(portal_url)
    time.sleep(5)
        
    # 3. ログイン画面の検知とクリック
    try:
        page_text = driver.page_source.lower()
        if "employee" in page_text or "ソーシャル" in page_text or "social" in page_text:
            print("ログイン画面を検出しました。「TMP Employee Login」をクリックします...")
            
            login_btn = None
            login_xpaths = [
                "//*[normalize-space(text())='TMP Employee Login']",
                "//*[contains(text(), 'Employee Login')]",
                "//*[contains(text(), 'ログイン') or contains(text(), 'サインイン')]",
                "//button[contains(., 'Employee')]"
            ]
            for xpath in login_xpaths:
                try:
                    el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    if el.is_displayed():
                        login_btn = el
                        break
                except:
                    continue
            
            if login_btn:
                login_btn.click()
                print("サインイン処理を待機しています (20秒)...")
                time.sleep(20)
            else:
                print("[警告] ログインボタンが見つかりませんでした。")
    except Exception as e:
        print(f"[警告] ログインボタンのクリック処理中に問題が発生しました: {e}")
        
    # 4. QuickSight iframe への切り替え
    print("QuickSight iframe のロードを待機しています...")
    iframe_found = False
    for attempt in range(15): # 最大45秒
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                src = iframe.get_attribute("src")
                if src and ("quicksight" in src.lower() or "dashboard" in src.lower() or "amazon" in src.lower()):
                    driver.switch_to.frame(iframe)
                    iframe_found = True
                    break
            except:
                pass
        if iframe_found:
            print("✅ QuickSight iframe への切り替えに成功しました。")
            break
        time.sleep(3)
        
    if not iframe_found:
        print("[エラー] QuickSight iframe が見つかりませんでした。")
        return False
        
    # 5. iframe 内でのダッシュボード選択
    print(f"iframe 内でダッシュボード 「{target_dashboard}」 の表示を待機中...")
    dashboard_link = None
    dashboard_xpath = (
        f"//*[(contains(text(), '{target_dashboard}') or contains(@title, '{target_dashboard}') or contains(@aria-label, '{target_dashboard}')) "
        f"and not(contains(@aria-label, 'お気に入り') or contains(@aria-label, 'favorite') or contains(@aria-label, 'star') "
        f"or contains(@title, 'お気に入り') or contains(@title, 'favorite') or contains(@title, 'star') "
        f"or contains(@class, 'favorite') or contains(@class, 'star'))]"
    )
    
    try:
        dashboard_link = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, dashboard_xpath))
        )
    except Exception as e:
        print(f"[警告] WebDriverWait でダッシュボードリンクが見つかりませんでした: {e}")
        
    if dashboard_link:
        try:
            print(f"ダッシュボード 「{target_dashboard}」 をクリックします...")
            dashboard_link.click()
            time.sleep(10)
        except Exception as e:
            print(f"[エラー] ダッシュボードのクリックに失敗しました: {e}")
            return False
    else:
        # フォールバック：JSを使用して iframe 全体からターゲットテキストを探してクリックを試みる
        print("フォールバックJSによる要素の探索を実行します...")
        click_fallback_js = f"""
        function findAndClick(root, text) {{
            let res = null;
            const walk = n => {{
                if(!n || res) return;
                let t = '';
                let isFavoriteButton = false;
                try {{
                    const ariaLabel = n.getAttribute ? (n.getAttribute('aria-label') || '').toLowerCase() : '';
                    const title = n.getAttribute ? (n.getAttribute('title') || '').toLowerCase() : '';
                    const className = n.className ? String(n.className).toLowerCase() : '';
                    if (ariaLabel.includes('favorite') || ariaLabel.includes('お気に入り') || ariaLabel.includes('star') ||
                        title.includes('favorite') || title.includes('お気に入り') || title.includes('star') ||
                        className.includes('favorite') || className.includes('star')) {{
                        isFavoriteButton = true;
                    }}
                    t = (n.nodeType === 3 ? n.textContent : (n.nodeType === 1 ? (n.innerText || n.getAttribute('aria-label') || '') : ''));
                }} catch(e) {{}}
                if(!isFavoriteButton && t && t.includes(text) && (n.nodeType === 3 || n.children.length === 0)) {{
                    res = (n.nodeType === 3 ? n.parentElement : n);
                    return;
                }}
                if(n.shadowRoot) walk(n.shadowRoot);
                let c = n.firstChild;
                while(c) {{
                    walk(c);
                    c = c.nextSibling;
                }}
            }};
            walk(root);
            if(res) {{
                const clickable = res.closest('a, button, [role="button"]') || res;
                try {{ clickable.scrollIntoView({{block:'center'}}); }} catch(e){{}}
                clickable.click();
                return true;
            }}
            return false;
        }}
        return findAndClick(document.body, '{target_dashboard}');
        """
        dashboard_clicked = driver.execute_script(click_fallback_js)
        print(f"フォールバックJSクリック結果: {dashboard_clicked}")
        if not dashboard_clicked:
            print("[エラー] ダッシュボードが見つかりませんでした。")
            return False
        time.sleep(10)
    
    # 6. iframe 内のコントロールパネルが読み込まれるのを待機
    print("QuickSightダッシュボードの読み込み完了（コントロール表示）を待機しています...")
    for attempt in range(12):  # 最大60秒
        # 念のため毎回iframe内の最前面に戻して検索
        driver.switch_to.default_content()
        # 再度iframeに切り替え
        iframe_found = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                src = iframe.get_attribute("src")
                if src and ("quicksight" in src.lower() or "dashboard" in src.lower() or "amazon" in src.lower()):
                    driver.switch_to.frame(iframe)
                    iframe_found = True
                    break
            except:
                pass
        
        if iframe_found:
            try:
                if "コントロール" in driver.execute_script("return document.body.innerText"):
                    print("✅ QuickSightダッシュボードの読み込みが完了しました。")
                    return True
            except:
                pass
                
        print(f"  ...待機中 ({attempt*5 + 5}s経過)")
        time.sleep(5)
        
    print("[エラー] ダッシュボードの読み込みがタイムアウトしました。")
    return False

def run_monthly_date_set(target_arg=None, is_auto=False):
    start_date, end_date = get_target_period(target_arg)
    print(f"Connecting to Edge... Target Month Set: {start_date} ~ {end_date}")
    
    # 対象年月を一時ファイルに保存
    try:
        target_info = {
            "year": int(start_date.split("/")[0]),
            "month": int(start_date.split("/")[1]),
            "start_date": start_date,
            "end_date": end_date
        }
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target_month.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(target_info, f, ensure_ascii=False, indent=2)
        print(f"  [情報] 対象年月情報を target_month.json に保存しました: {start_date} ~ {end_date}")
    except Exception as e:
        print(f"  [警告] 対象年月の保存に失敗しました: {e}")
        
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Edge(options=options)
        try:
            driver.maximize_window()
            print("  [設定] ウィンドウを最大化しました。")
            time.sleep(1)
        except Exception as e:
            print(f"  [警告] ウィンドウの最大化に失敗しました: {e}")
    except Exception as e:
        print(f"[エラー] Edgeブラウザへの接続に失敗しました。Edgeがデバッグモード(9222ポート)で起動しているか確認してください。: {e}")
        sys.exit(1)
        
    # 自動ログインおよびダッシュボード遷移処理を含めてダッシュボードを確保する
    found = ensure_dashboard_open(driver, "EGZ010")
            
    if found:
        if not is_auto:
            print("\n------------------------------------------------------------")
            print("【手動確認】ダッシュボードが表示されたことを確認してください。")
            print("※ログインにMFA認証等が必要な場合は、ブラウザ上で認証を完了させてください。")
            print("------------------------------------------------------------")
            input("準備が整いましたら、Enterキーを押して日付入力を開始します...")
            
            # 再接続
            found = False
            for h in driver.window_handles:
                driver.switch_to.window(h)
                iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        if "コントロール" in driver.execute_script("return document.body.innerText"):
                            found = True
                            break
                        driver.switch_to.default_content()
                    except:
                        pass
                if found:
                    break
            
            if not found:
                print("[エラー] ダッシュボードが見つかりませんでした。")
                sys.exit(1)

        print("Dashboard found. Starting date sequence...")
        res = driver.execute_script(f"""
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            const walk = (n, text) => {{
                if(!n) return null;
                if((n.innerText || '').includes(text) && n.id === 'sheet_control_panel_header') return n;
                if(n.shadowRoot) {{ let r = walk(n.shadowRoot, text); if(r) return r; }}
                let c = n.firstChild; while(c){{ let r = walk(c, text); if(r) return r; c = c.nextSibling; }}
                return null;
            }};

            const doMonthlySet = async () => {{
                // 1. Expand Panel
                const header = walk(document.body, 'コントロール');
                if(header && header.getAttribute('aria-expanded')==='false') {{
                    header.click();
                    await sleep(3000);
                }}

                // 2. Set Dates
                const findAndSet = async () => {{
                    const inputs = [];
                    const walkAll = n => {{
                        if(!n) return;
                        if(n.tagName === 'INPUT' && n.value && n.value.includes('20')) inputs.push(n);
                        if(n.shadowRoot) walkAll(n.shadowRoot);
                        let c = n.firstChild; while(c){{ walkAll(c); c = c.nextSibling; }}
                    }};
                    walkAll(document.body);
                    
                    if(inputs.length >= 2) {{
                        // Start Date
                        inputs[0].focus(); inputs[0].click(); inputs[0].value = '';
                        document.execCommand('insertText', false, '{start_date}');
                        inputs[0].dispatchEvent(new Event('change', {{bubbles:true}}));
                        await sleep(2000);
                        
                        // End Date
                        inputs[1].focus(); inputs[1].click(); inputs[1].value = '';
                        document.execCommand('insertText', false, '{end_date}');
                        inputs[1].dispatchEvent(new Event('change', {{bubbles:true}}));
                        await sleep(2000);
                        return true;
                    }}
                    return false;
                }};
                
                const success = await findAndSet();

                // 3. Collapse Panel
                if(header && header.getAttribute('aria-expanded')==='true') {{
                    header.click();
                    await sleep(2000);
                }}
                return success;
            }};
            return doMonthlySet();
        """)
        print(f"Date Set Result: {res}")
        time.sleep(5)
        driver.save_screenshot("step_1_monthly_dates.png")
        driver.switch_to.default_content()
    else:
        print("[エラー] QuickSightダッシュボードが見つかりませんでした。ダッシュボードを開いた状態で実行してください。")
        sys.exit(1)

if __name__ == "__main__":
    is_auto = False
    target_month_arg = None
    
    for arg in sys.argv[1:]:
        if arg.lower() == "auto":
            is_auto = True
        else:
            target_month_arg = arg
            
    run_monthly_date_set(target_month_arg, is_auto)
