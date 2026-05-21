import os
import glob
import pandas as pd

PROJECT_ROOT = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI"
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")

# 「日別実績_」で始まるリネーム漏れファイルをチェック
leftover_files = glob.glob(os.path.join(DOWNLOAD_DIR, "日別実績_*.csv"))

print(f"🔍 {len(leftover_files)} 件のリネーム漏れファイルをチェックします...")

target_category = "225_ダンロップタイヤ"
target_route = "a-00 総販"

for f in leftover_files:
    try:
        # ヘッダーやエンコーディングを考慮して読み込み
        df = pd.read_csv(f, encoding="cp932", nrows=10) # 最初の数行で判断
        content = str(df.to_dict())
        
        # ファイル内容にターゲットのキーワードが含まれているか
        if "ダンロップ" in content or "225" in content:
            print(f"✨ 発見したかもしれません: {os.path.basename(f)}")
            print(f"   内容一部: {content[:200]}...")
    except Exception as e:
        pass

print("🏁 チェック終了。")
