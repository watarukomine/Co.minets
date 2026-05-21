import win32com.client
import os

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

def extract_excel_data(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(path))
        
        print(f"Total Sheets: {wb.Sheets.Count}")
        for i in range(1, min(wb.Sheets.Count, 5) + 1):
            sheet = wb.Sheets(i)
            print(f"\n--- Sheet: {sheet.Name} ---")
            # Extract first 10 rows and 10 columns
            for r in range(1, 11):
                row_data = []
                for c in range(1, 11):
                    val = sheet.Cells(r, c).Value
                    row_data.append(str(val) if val is not None else "")
                print("\t".join(row_data))
        
        wb.Close(False)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if excel:
            excel.Quit()

if __name__ == "__main__":
    extract_excel_data(file_path)
