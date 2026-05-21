import os
import glob

PROJECT_ROOT = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI"
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")
TARGET_FILENAME = "【売上】a-00 総販_225_ダンロップタイヤ.csv"
TARGET_PATH = os.path.join(DOWNLOAD_DIR, TARGET_FILENAME)

# 「日別実績_」で始まるリネーム漏れファイルをチェック
leftover_files = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))

print(f"🔍 {len(leftover_files)} 件のリネーム漏れファイルをチェックします...")

for f in leftover_files:
    content = ""
    try:
        # まずはUTF-8(BOMあり)を試す
        with open(f, "r", encoding="utf-8-sig") as file:
            content = file.read(1000)
    except:
        try:
            # ダメならCP932(Shift-JIS)を試す
            with open(f, "r", encoding="cp932") as file:
                content = file.read(1000)
        except:
            print(f"⚠️ {os.path.basename(f)} の読み込みに失敗しました（エンコーディング不明）")
            continue

    if "ダンロップ" in content:
        print(f"✨ ターゲットの可能性が高いファイルを発見: {os.path.basename(f)}")
        # リネームして終了
        try:
            os.rename(f, TARGET_PATH)
            print(f"✅ 「{TARGET_FILENAME}」として復元しました！")
            found = True
            break
        except Exception as e:
            print(f"❌ リネームに失敗: {e}")

if not found:
    print("❌ 該当するファイルは見つかりませんでした。")
