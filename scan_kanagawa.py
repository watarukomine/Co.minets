import win32com.client
import os
import json

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

def scan_for_kanagawa():
    if not os.path.exists(file_path): return
    
    excel = None
    try:
        # Try to get existing Excel instance first
        try:
            excel = win32com.client.GetActiveObject("Excel.Application")
            print("Attached to existing Excel instance.")
        except:
            excel = win32com.client.Dispatch("Excel.Application")
            print("Started new Excel instance.")
            
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(file_path), ReadOnly=True)
        
        target = "85371"
        found = False
        
        for i in range(1, wb.Sheets.Count + 1):
            sheet = wb.Sheets(i)
            # Find is more efficient
            res = sheet.Cells.Find(What=target)
            if res:
                print(f"FOUND {target} in Sheet: {sheet.Name} at Row: {res.Row}")
                data = []
                for c in range(1, 15):
                    data.append(str(sheet.Cells(res.Row, c).Value or ""))
                print(f"DATA: {' | '.join(data)}")
                found = True
                break
        
        wb.Close(False)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Don't quit if we attached to an existing one, but we started it so maybe safe?
        # Actually, let's just leave it if it fails.
        pass

if __name__ == "__main__":
    scan_for_kanagawa()
