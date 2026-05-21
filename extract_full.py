import win32com.client
import os
import json

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"
output_json = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\full_report_data.json"

def extract_full_report(path, out_path):
    if not os.path.exists(path):
        return
    
    excel = None
    all_data = {}
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(path))
        
        print(f"Reading {wb.Sheets.Count} sheets...")
        for i in range(1, wb.Sheets.Count + 1):
            sheet = wb.Sheets(i)
            name = sheet.Name
            print(f"Processing sheet: {name}")
            
            # Extract first 100 rows and 20 columns for each sheet
            rows = []
            # We use UsedRange to be more efficient if possible, but Cells is safer
            last_row = min(sheet.UsedRange.Rows.Count, 100)
            last_col = min(sheet.UsedRange.Columns.Count, 20)
            
            for r in range(1, last_row + 1):
                row_data = []
                for c in range(1, last_col + 1):
                    val = sheet.Cells(r, c).Value
                    row_data.append(val if val is not None else "")
                rows.append(row_data)
            all_data[name] = rows
            
        wb.Close(False)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print("Success!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if excel:
            excel.Quit()

if __name__ == "__main__":
    extract_full_report(file_path, output_json)
