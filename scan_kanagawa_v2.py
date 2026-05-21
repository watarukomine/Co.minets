import win32com.client
import os

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

def scan_for_kanagawa():
    if not os.path.exists(file_path): return
    
    excel = None
    try:
        try:
            excel = win32com.client.GetActiveObject("Excel.Application")
        except:
            excel = win32com.client.Dispatch("Excel.Application")
            
        wb = excel.Workbooks.Open(os.path.abspath(file_path), ReadOnly=True)
        
        target = "85371"
        found = False
        
        for i in range(1, wb.Sheets.Count + 1):
            sheet = wb.Sheets(i)
            res = sheet.Cells.Find(What=target)
            if res:
                print(f"FOUND {target} in Sheet: {sheet.Name}")
                # Get the whole row
                row_idx = res.Row
                data = []
                for c in range(1, 20):
                    v = sheet.Cells(row_idx, c).Value
                    data.append(str(v) if v is not None else "")
                print(f"DATA_ROW: {' | '.join(data)}")
                found = True
                break
        
        wb.Close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_for_kanagawa()
