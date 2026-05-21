import win32com.client
import os
import json

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"
output_json = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\kanagawa_deep_scan.json"

def deep_scan(path, out_path):
    if not os.path.exists(path): return
    
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        wb = excel.Workbooks.Open(os.path.abspath(path), ReadOnly=True)
        sheet = wb.Sheets(1)
        
        data = []
        # Scan from row 1 to 2000
        for r in range(1, 2001):
            # Check column 1 for the branch code
            val = sheet.Cells(r, 1).Value
            if str(val) == "85371":
                # Found Kanagawa! Extract the next 50 rows (likely dealers within Kanagawa)
                for i in range(r, r + 60):
                    row = []
                    for c in range(1, 15):
                        row.append(sheet.Cells(i, c).Value or "")
                    data.append(row)
                break
        
        wb.Close(False)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e: print(f"Error: {e}")
    finally:
        if excel: excel.Quit()

if __name__ == "__main__":
    deep_scan(file_path, output_json)
