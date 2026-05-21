import win32com.client
import os

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\target_report.xlsx"

def scan():
    if not os.path.exists(file_path): return
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        wb = excel.Workbooks.Open(os.path.abspath(file_path), ReadOnly=True)
        
        target = "371"
        for i in range(1, wb.Sheets.Count + 1):
            sheet = wb.Sheets(i)
            # Find 371
            res = sheet.Cells.Find(What=target)
            if res:
                print(f"FOUND {target} in Sheet: {sheet.Name} at Row: {res.Row}")
                data = []
                for c in range(1, 15):
                    v = sheet.Cells(res.Row, c).Value
                    data.append(str(v) if v is not None else "")
                print(f"DATA_ROW: {' | '.join(data)}")
                # Also check the headers (row 2 usually)
                headers = []
                for c in range(1, 15):
                    v = sheet.Cells(2, c).Value
                    headers.append(str(v) if v is not None else "")
                print(f"HEADERS: {' | '.join(headers)}")
                break
        wb.Close(False)
        excel.Quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan()
