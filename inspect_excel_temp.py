import pandas as pd
import os

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

if os.path.exists(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Sheets: {xl.sheet_names}")
        # Focus on "実績集" or similar if it exists
        target_sheets = [s for s in xl.sheet_names if "実績" in s or "集計" in s]
        if not target_sheets:
            target_sheets = xl.sheet_names[:3]
            
        for sheet in target_sheets[:5]: 
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
            print(f"\n--- Sheet: {sheet} ---")
            print(df.to_string())
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File not found: {file_path}")
