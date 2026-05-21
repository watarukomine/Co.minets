import os
import glob
import shutil
import datetime

# 定数
DOWNLOADS_DIR = r"C:\Users\00137012\Downloads"
PROJECT_DOWNLOADS_DIR = r"x:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\downloads"

def main():
    print(f"Searching for CSV files in {DOWNLOADS_DIR}...")
    
    # 2時間以内に更新されたCSVファイルを探す（前回の抽出から時間が経っている可能性があるため広めに）
    time_limit = datetime.datetime.now() - datetime.timedelta(hours=48)
    
    # ダウンロードフォルダ内のすべてのCSVを検索
    search_pattern = os.path.join(DOWNLOADS_DIR, "*.csv")
    csv_files = glob.glob(search_pattern)
    
    recent_files = []
    
    for file_path in csv_files:
        try:
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if mod_time > time_limit:
                # ファイル名が日別実績から始まるか、特徴的な命名規則を持つものを対象とする
                filename = os.path.basename(file_path)
                if filename.startswith("日別実績") or "売上" in filename or "粗利" in filename:
                     recent_files.append((file_path, mod_time))
        except Exception as e:
             print(f"Error checking file {file_path}: {e}")
             
    # 更新日時でソート (新しい順)
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    if not recent_files:
        print("No recent target CSV files found in the Downloads folder.")
        # プロジェクトフォルダ内のdownloadsも確認してみる
        project_csv_pattern = os.path.join(PROJECT_DOWNLOADS_DIR, "日別実績*.csv")
        project_csvs = glob.glob(project_csv_pattern)
        if project_csvs:
             print(f"Found {len(project_csvs)} potential CSV files in the project downloads directory.")
             # datetimeオブジェクトのソート処理
             sorted_project_csvs = []
             for f in project_csvs:
                  mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(f))
                  sorted_project_csvs.append((f, mod_time))
             sorted_project_csvs.sort(key=lambda x: x[1], reverse=True)
             
             for f, m in sorted_project_csvs[:15]:
                 print(f"  - {os.path.basename(f)} (Mod: {m})")
        return

    print(f"Found {len(recent_files)} recent target CSV files:")
    for file_path, mod_time in recent_files[:20]: # 念のため最大20件表示
        filename = os.path.basename(file_path)
        print(f"  - {filename} (Modified: {mod_time})")
        
        # オプション：ここから必要に応じてプロジェクトフォルダに移動する処理を追加できる
        # dest_path = os.path.join(PROJECT_DOWNLOADS_DIR, filename)
        # shutil.move(file_path, dest_path)
        # print(f"    Moved to {dest_path}")

if __name__ == "__main__":
    main()
