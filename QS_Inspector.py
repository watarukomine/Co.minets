import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def main():
    print("【QuickSight フィルター操作テスト v2】")

    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--start-maximized")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Edge(options=edge_options)
    driver.get("https://report.tmp-one.com/portal")

    input("\nダッシュボードを表示したらEnter: ")

    # iframe切り替え
    try:
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[contains(@src, 'quicksight')]")
            )
        )
        print("★ iframe切り替え成功")
    except:
        print("★ iframe見つからず")

    # ===== テスト1: 「販売区分」のcomboboxを見つけてクリック =====
    print("\n" + "="*60)
    print("テスト1: comboboxを見つける")
    print("="*60)

    # 全comboboxを取得
    comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
    print(f"combobox数: {len(comboboxes)}")
    for i, cb in enumerate(comboboxes):
        print(f"  [{i}] text='{cb.text}' displayed={cb.is_displayed()}")

    if len(comboboxes) < 3:
        print("comboboxが足りません。テスト終了。")
        input()
        driver.quit()
        return

    # 「販売区分」は3番目(index=2)のはず
    target_cb = comboboxes[2]
    print(f"\n販売区分combobox: text='{target_cb.text}'")

    # ===== テスト2: 3種類のクリック方法を試す =====
    print("\n" + "="*60)
    print("テスト2: クリック方法A - ActionChains（リアルクリック）")
    print("="*60)
    
    ActionChains(driver).move_to_element(target_cb).click().perform()
    time.sleep(2)

    # クリック後に何が出現したか調べる
    def dump_popup_state(label):
        print(f"\n--- {label}: 出現した要素 ---")
        
        # iframe内で探す
        for selector_name, xpath in [
            ("role=listbox", "//*[@role='listbox']"),
            ("role=option", "//*[@role='option']"),
            ("role=menuitem", "//*[@role='menuitem']"),
            ("MuiMenu", "//*[contains(@class, 'MuiMenu')]"),
            ("MuiPopover", "//*[contains(@class, 'MuiPopover')]"),
            ("MuiList", "//*[contains(@class, 'MuiList')]"),
            ("MuiMenuItem", "//*[contains(@class, 'MuiMenuItem')]"),
            ("aria-expanded=true", "//*[@aria-expanded='true']"),
            ("100_総売上(テキスト)", "//*[contains(text(), '100_総売上')]"),
            ("値を検索(input)", "//input[@placeholder='値を検索']"),
        ]:
            try:
                els = driver.find_elements(By.XPATH, xpath)
                if els:
                    print(f"  {selector_name}: {len(els)}個")
                    for j, el in enumerate(els[:3]):
                        txt = (el.text or "")[:80]
                        aria = el.get_attribute("aria-label") or ""
                        cls = (el.get_attribute("class") or "")[:60]
                        print(f"    [{j}] tag=<{el.tag_name}> aria='{aria}' class='{cls}' text='{txt}'")
            except:
                pass
        
        # 親フレームにも探しに行く
        print(f"\n--- {label}: 親フレーム側を確認 ---")
        try:
            driver.switch_to.parent_frame()
            for selector_name, xpath in [
                ("role=listbox(親)", "//*[@role='listbox']"),
                ("role=option(親)", "//*[@role='option']"),
                ("MuiPopover(親)", "//*[contains(@class, 'MuiPopover')]"),
                ("100_総売上(親)", "//*[contains(text(), '100_総売上')]"),
                ("値を検索(親)", "//input[@placeholder='値を検索']"),
            ]:
                try:
                    els = driver.find_elements(By.XPATH, xpath)
                    if els:
                        print(f"  {selector_name}: {len(els)}個")
                        for j, el in enumerate(els[:3]):
                            txt = (el.text or "")[:80]
                            print(f"    [{j}] tag=<{el.tag_name}> text='{txt}'")
                except:
                    pass
            # iframeに戻る
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[contains(@src, 'quicksight')]")
                )
            )
        except Exception as e:
            print(f"  親フレーム確認失敗: {e}")

    dump_popup_state("ActionChains click後")

    # ESCで閉じる
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)

    # ===== テスト3: JavaScript clickも試す =====
    print("\n" + "="*60)
    print("テスト3: クリック方法B - JavaScript click")
    print("="*60)

    # comboboxを再取得（stale対策）
    comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
    target_cb = comboboxes[2]
    driver.execute_script("arguments[0].click();", target_cb)
    time.sleep(2)
    dump_popup_state("JS click後")

    # ESCで閉じる
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)

    # ===== テスト4: comboboxのariaプロパティを詳しく調べる =====
    print("\n" + "="*60)
    print("テスト4: combobox要素の詳細属性")
    print("="*60)
    
    comboboxes = driver.find_elements(By.XPATH, "//div[@role='combobox' and @data-automation-id='sheet_control_value']")
    target_cb = comboboxes[2]
    
    attrs = ["id", "class", "role", "aria-expanded", "aria-haspopup", "aria-owns",
             "aria-controls", "aria-activedescendant", "aria-labelledby",
             "data-automation-id", "tabindex", "data-testid"]
    for attr in attrs:
        val = target_cb.get_attribute(attr)
        if val:
            print(f"  {attr} = '{val}'")
    
    # 親要素のaria-haspopup等も確認
    parent = target_cb.find_element(By.XPATH, "./..")
    print(f"\n  親: tag=<{parent.tag_name}> class='{(parent.get_attribute('class') or '')[:60]}'")
    for attr in ["aria-haspopup", "aria-expanded", "role", "id"]:
        val = parent.get_attribute(attr)
        if val:
            print(f"  親.{attr} = '{val}'")

    # comboboxのouterHTMLを出力
    print(f"\n  outerHTML:")
    html = target_cb.get_attribute("outerHTML")
    print(f"  {html[:500]}")

    print("\n\n========== テスト完了！ ==========")
    print("結果をコピーしてチャットに貼り付けてください。")
    input()
    driver.quit()

if __name__ == '__main__':
    main()
