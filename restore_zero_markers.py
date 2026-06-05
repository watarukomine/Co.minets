# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "extracted_data")
MISSING_JSON = os.path.join(BASE_DIR, "missing_patterns.json")

def main():
    if not os.path.exists(MISSING_JSON):
        print(f"[ERROR] missing_patterns.json が見つかりません: {MISSING_JSON}")
        return

    with open(MISSING_JSON, 'r', encoding='utf-8') as f:
        missing_list = json.load(f)

    print(f"読み込んだ不足パターン数: {len(missing_list)}")
    
    created_count = 0
    for item in missing_list:
        filename = item.get("filename")
        if not filename:
            continue
        
        # [ZERO_DATA]マーカーファイルのフルパス
        zero_filename = f"[ZERO_DATA]{filename}"
        zero_path = os.path.join(DOWNLOAD_DIR, zero_filename)
        
        if not os.path.exists(zero_path):
            try:
                with open(zero_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(f"Zero data (restored from missing list) at {datetime.now().isoformat()}")
                created_count += 1
            except Exception as e:
                print(f"[ERROR] マーカー作成失敗: {zero_filename} ({e})")
        else:
            # 既に存在する場合はカウントのみ
            created_count += 1

    print(f"処理完了: {created_count} 件の [ZERO_DATA] マーカーファイルを配置しました。")

if __name__ == "__main__":
    main()
