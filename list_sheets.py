import win32com.client
import os

file_path = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\【A3印刷用】0417_改良2026年3月度実績集.xlsx"

def list_sheets(path):
    if not os.path.exists(path): return
    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(path))
        print("Sheets in this workbook:")
        for i in range(1, wb.Sheets.Count + 1):
            print(f"{i}: {wb.Sheets(i).Name}")
        wb.Close(False)
    except Exception as e: print(f"Error: {e}")
    finally:
        if excel: excel.Quit()

if __name__ == "__main__":
    list_sheets(file_path)
