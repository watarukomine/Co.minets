import os
import time
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# 抽出パターンのマスターデータ
# ※実際の環境に合わせてリストの中身を追加・修正してください
# ==========================================
AMOUNT_TYPES = ["売上", "粗利"]
BRANCH = "すべて"

ROUTES = [
    "a-00 総販",
    "b-01 販売店", 
    "b-02 外販",
    "b-03 ジェームス", 
    "c-01 卸売",    
    "c-02 直売",    
    "d-01 部品商",  
    "d-02 その他再販業者",
    "d-03 修理業者",
    "d-04 GSS",
    "d-05 用品小売り店",
    "d-06 その他",
    "e-01 修理工場",
    "e-02 特定修理業者",
    "e-03 大口ユーザー"
]

SALES_CLASSES = [
    "100_総売上",
    "110_総売上(除通信事業）",
    "200_重点商品",
    "210_特販部品",
    "211_特販6品目",
    "212_競争品",
    "213_クリーンエアフィルター",
    "214_特販部品その他",
    "220_タイヤ",
    "221_GYタイヤ",
    "222_ミシュランタイヤ",
    "223_レクサスセット",
    "224_タイヤその他",
    "225_ダンロップタイヤ",
    "230_バッテリー",
    "231_ACデルコ",
    "232_パナソニック",
    "233_GSユアサ",
    "234_レクサスバッテリー",
    "235_地場バッテリー",
    "236_地場パナソニック",
    "237_地場GSユアサ",
    "238_パナソニック(本部＋地場)",
    "239_GSユアサ(本部＋地場)",
    "240_礦油",
    "241_エンジンオイル",
    "242_シャシオイル",
    "243_フルード",
    "244_ケミカル",
    "245_礦油その他",
    "300_一般部品",
    "310_外装部品",
    "320_機能部品",
    "321_S部品",
    "400_用品",
    "410_ナビ",
    "411_T-Connect対応ナビ",
    "412_ベーシックナビ",
    "413_エントリーナビ",
    "414_ナビキット",
    "415_T-Connectナビキット",
    "416_エントリーナビキット",
    "417_本部扱いナビ",
    "418_ナビその他",
    "420_ナビ関連オプション",
    "421_後席ディスプレイ",
    "422_モニターカメラ類",
    "423_地図ソフト",
    "424_ドライブレコーダー",
    "425_純正ドライブレコーダー",
    "426_本部調達ドライブレコーダー",
    "427_その他ドライブレコーダー",
    "428_ナビ関連オプションその他",
    "430_オーディオ",
    "440_ITS関連商品",
    "450_ベーシック推奨用品",
    "460_オプション推販用品",
    "461_後付け安全4商品",
    "462_TRD",
    "463_モデリスタ",
    "464_オプション推販用品その他",
    "470_レクサス用品",
    "480_用品その他",
    "500_その他",
    "510_通信事業",
    "520_工具",
    "521_本部調達工具",
    "522_地場工具",
    "530_C＋WALK(本体)",
    "540_本部商品その他",
    "550_新車カタログ",
    "560_その他(その他)",
    "901_プレミアムCAF",
    "902_パナソニックバッテリー(本部＋地場)",
    "903_GSユアサバッテリー(本部＋地場)",
    "904_ブレーキフルード",
    "905_LLC",
    "906_一般部品(S部品除き)",
    "907_純正ETC2.0",
    "907_純正ETC",
    "909_TCD用品",
    "910_トヨタ車TRD",
    "911_レクサス車TRD",
    "912_トヨタ車モデリスタ",
    "913_レクサス車モデリスタ",
    "914_TMP用品",
    "915_TZ用品",
    "916_TMP車種専用品",
    "917_夏タイヤ",
    "918_冬タイヤ"
]

START_DATE = "2019/04/01"
END_DATE = datetime.today().strftime("%Y/%m/%d")

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


def set_quicksight_dropdown(frame, filter_name, target_value):
    """
    フィルター名（例：「ルート」）の横のドロップダウンを開き、
    すべて選択を解除してから目的の文字を選択する関数
    """
    print(f"  [{filter_name}] を「{target_value}」に変更します...")
    
    # フィルター名が書かれている付近のクリック可能な領域を開く
    # （見出し文字のちょっと下にある入力枠を狙うイメージ）
    try:
        frame.get_by_text(filter_name, exact=True).locator("..").click()
    except Exception:
        # 万が一見つからなければ、画面上の対象テキスト自体を無理やりクリック
        frame.get_by_text(filter_name, exact=True).click(force=True)
    
    time.sleep(1)
    
    # リストの一番上にある「すべて選択」が表示されていれば、クリックして一括解除する
    # ※すでに解除されている場合はスキップ
    select_all = frame.get_by_text("すべて選択", exact=True)
    if select_all.is_visible():
        try:
            # aria-selected="true"（チェックが入っている状態）なら外す
            if select_all.get_attribute("aria-selected") == "true" or select_all.locator("input").is_checked():
                select_all.click()
                time.sleep(0.5)
        except Exception:
            pass

    # 文字検索の入力欄（プレースホルダー「検索」）があれば文字を入れて絞り込む
    search_box = frame.get_by_placeholder("検索")
    if search_box.is_visible():
        search_box.fill(target_value)
        time.sleep(1)
    
    # 対象の値（例：「100_総売上」）をクリック
    frame.get_by_text(target_value, exact=True).first.click()
    time.sleep(0.5)
    
    # リストを閉じるために何もない何処か（画面上部など）をクリック
    frame.locator("body").click(position={"x": 10, "y": 10})
    time.sleep(1)


def main():
    print("【TMP-ONE データ抽出ループシステム】")
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    user_data_dir = r"C:\Users\00137012\Documents\edge_playwright_profile"

    # Playwrightの制限を回避するため、Pythonから直接Edgeを起動する
    edge_process = subprocess.Popen([
        edge_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ])

    print("自動操縦用のブラウザを起動しています...")
    time.sleep(5) 

    with sync_playwright() as p:
        try:
            # 起動したEdgeに外部接続
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("【エラー】ブラウザへの接続に失敗しました。")
            return

        context = browser.contexts[0]
        # アクティブなタブ（ダッシュボードが開かれているタブ）を取得
        page = context.pages[0] if context.pages else context.new_page()

        print("=========================================================")
        print("いつものブラウザに接続成功しました！")
        print("ブラウザ上で対象のダッシュボードを表示しておいてください。")
        print("準備が完了したら、この画面で【 Enterキー 】を押すと全自動ループが始まります！")
        print("=========================================================")

        input("\nダッシュボードが表示されていることを確認し、ここでEnterキーを押してください: ")
        print("\n--- 自動抽出ループを開始します ---")

        # QuickSightの内部フレームを取得
        frame = page.frame_locator("iframe[src*='quicksight.aws.amazon.com']")

        # --------------------------------------------------
        # 1. コントロール（期間）の展開とセット
        # --------------------------------------------------
        print("期間の初期セットを行います...")
        try:
            # 既にコントロールが開いていない場合のみ展開
            if not frame.get_by_text("期間（開始）").is_visible():
                frame.get_by_text("コントロール").click()
                time.sleep(1.5)

            # 期間（開始）の横にある四角い入力欄に日付を入れる
            frame.locator("input[placeholder='YYYY/MM/DD']").first.fill(START_DATE)
            frame.locator("input[placeholder='YYYY/MM/DD']").first.press("Enter")
            time.sleep(0.5)
            # 期間（終了）に本日の日付を入れる
            frame.locator("input[placeholder='YYYY/MM/DD']").nth(1).fill(END_DATE)
            frame.locator("input[placeholder='YYYY/MM/DD']").nth(1).press("Enter")
            time.sleep(1)

            # 再度コントロールをクリックして閉じる
            frame.get_by_text("コントロール").first.click()
            time.sleep(2)  # データ更新を待つ
        except Exception as e:
            print(f"期間の自動セットに失敗しました（手動でセット済の前提で続行します）: {e}")

        # --------------------------------------------------
        # 2. メインの多重ループ処理
        # --------------------------------------------------
        pattern_count = 1
        
        for amount in AMOUNT_TYPES:
            # ▼「売上」か「粗利」をセット
            try:
                set_quicksight_dropdown(frame, "売上/粗利", amount)
            except Exception:
                print(f"[{amount}]のセットに失敗しました。継続します。")

            for route in ROUTES:
                # ▼ルートをセット
                try:
                    set_quicksight_dropdown(frame, "ルート", route)
                except Exception:
                    print(f"[{route}]のセットに失敗しました。継続します。")

                for sc in SALES_CLASSES:
                    print(f"\n[処理中 {pattern_count}] {amount} / 支社:{BRANCH} / ルート:{route} / 販売区分:{sc}")
                    
                    try:
                        # ▼販売区分をセット
                        set_quicksight_dropdown(frame, "販売区分", sc)
                        
                        # データが裏で集計されて表が更新されるのを待つ
                        print("  グラフ更新を待機中...")
                        time.sleep(4) 
                        
                        # ▼CSV出力アクション
                        print("  [CSV出力] を実行します...")
                        # 1. 巨大な表の枠のあたりをマウスオーバー（Hover）して、右上のメニュー「･･･」を出現させる
                        frame.locator("div[data-automation-id='pivot-table-container']").first.hover()
                        # （もし上記で見つからない場合は、画面の真ん中あたりにマウスを移動）
                        # page.mouse.move(500, 500)
                        time.sleep(0.5)
                        
                        # 2. 出現した「･･･（メニューオプション）」ボタンをクリック
                        frame.locator("button[aria-label*='メニューオプション'], button[aria-label*='Visual menu']").first.click(force=True)
                        time.sleep(0.5)

                        # 3. リストから「CSV へエクスポート」をクリックしてダウンロード
                        with page.expect_download(timeout=120000) as download_info:
                            frame.get_by_role("menuitem", name="CSV へエクスポート").click()
                            
                        # ▼保存処理
                        download = download_info.value
                        
                        today_str = datetime.today().strftime("%Y%m%d")
                        safe_route = route.replace("/", "／")
                        safe_sc = sc.replace("/", "／")
                        
                        file_name = f"{amount}ー{BRANCH}ー{safe_route}ー{safe_sc}_{today_str}.csv"
                        save_path = os.path.join(DOWNLOAD_DIR, file_name)
                        
                        download.save_as(save_path)
                        print(f"  ✓ 保存完了: {file_name}")

                    except Exception as e:
                        print(f"  エラー発生（スキップして次へ）: {e}")

                    pattern_count += 1
        
        print("\n--- 全パターンの抽出が完全終了しました！ ---")
        browser.close()

if __name__ == '__main__':
    main()
