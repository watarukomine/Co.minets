import win32com.client
import os
import json

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

def find_kanagawa(path):
    if not os.path.exists(path): return
    
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(path))
        
        target_code = "85371"
        found = False
        
        print(f"Searching for {target_code} across {wb.Sheets.Count} sheets...")
        
        for i in range(1, wb.Sheets.Count + 1):
            sheet = wb.Sheets(i)
            # Search in the first 500 rows and 20 columns
            for r in range(1, 501):
                # Using Find is faster than iterating Cells
                res = sheet.UsedRange.Find(target_code)
                if res:
                    print(f"FOUND {target_code} in Sheet: {sheet.Name} at Row: {res.Row}, Col: {res.Column}")
                    # Extract surrounding data
                    header_row = 2 # Assuming row 2 has headers based on previous observation
                    row_data = []
                    for c in range(1, 15):
                        row_data.append(str(sheet.Cells(res.Row, c).Value or ""))
                    print(f"Data: {row_data}")
                    found = True
                    break
            if found: break
            
        wb.Close(False)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if excel:
            excel.Quit()

if __name__ == "__main__":
    find_kanagawa(file_path)
