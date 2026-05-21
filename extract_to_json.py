import win32com.client
import os
import json

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"
output_json = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data.json"

def extract_excel_to_json(path, out_path):
    if not os.path.exists(path):
        return
    
    excel = None
    data = {}
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(path))
        
        for i in range(1, min(wb.Sheets.Count, 5) + 1):
            sheet = wb.Sheets(i)
            sheet_name = sheet.Name
            rows = []
            # Extract first 50 rows
            for r in range(1, 51):
                row_data = []
                for c in range(1, 15):
                    val = sheet.Cells(r, c).Value
                    row_data.append(val if val is not None else "")
                rows.append(row_data)
            data[sheet_name] = rows
        
        wb.Close(False)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if excel:
            excel.Quit()

if __name__ == "__main__":
    extract_excel_to_json(file_path, output_json)
