# -*- coding: utf-8 -*-
import os
import csv
import io
import shutil
import zipfile
import traceback

SRC_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data_temp"
DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

def normalize_date(d_str):
    if not d_str:
        return ""
    d = d_str.split(' ')[0].strip()
    d = d.replace('/', '-')
    parts = d.split('-')
    if len(parts) == 3:
        try:
            return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except ValueError:
            pass
    return d

def get_branch_field(row):
    for k in ['支社', '管轄支社名']:
        if k in row:
            return k, row[k].strip()
    return '支社', ''

def read_zip_csv(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        csv_filename = z.namelist()[0]
        with z.open(csv_filename) as f:
            return f.read().decode('utf-8-sig'), csv_filename

def write_zip_csv(zip_path, csv_content, csv_filename):
    temp_zip = zip_path + ".tmp"
    try:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr(csv_filename, csv_content.encode('utf-8-sig'))
        
        if os.path.exists(zip_path):
            os.remove(zip_path)
        os.rename(temp_zip, zip_path)
    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        raise e

def merge_csv_content(exist_content, new_content):
    def parse_csv(content):
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        return fieldnames, rows

    exist_fields, exist_rows = parse_csv(exist_content)
    new_fields, new_rows = parse_csv(new_content)

    merged = {}
    fields = list(exist_fields) if exist_fields else ['支社', '日付', '当年', '前年']
    
    # ヘッダーフィールドの補完
    for f in new_fields:
        if f not in fields:
            fields.append(f)

    # 既存データのロード
    for row in exist_rows:
        _, branch = get_branch_field(row)
        date_str = normalize_date(row.get('日付', ''))
        if branch and date_str:
            row['日付'] = date_str
            merged[(branch, date_str)] = row

    # 新規データのマージ (重複は上書き)
    for row in new_rows:
        _, branch = get_branch_field(row)
        date_str = normalize_date(row.get('日付', ''))
        if branch and date_str:
            row['日付'] = date_str
            merged[(branch, date_str)] = row

    # 日付昇順、支社名昇順でソート
    sorted_keys = sorted(merged.keys(), key=lambda x: (x[1], x[0]))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for key in sorted_keys:
        writer.writerow(merged[key])

    return output.getvalue()

def process_merge():
    print("【データマージ処理を開始します】")
    if not os.path.exists(SRC_DIR):
        print(f"[警告] 送り元フォルダが見つかりません: {SRC_DIR}")
        return

    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    temp_files = os.listdir(SRC_DIR)
    if not temp_files:
        print("[情報] 一時フォルダ内に処理対象ファイルがありません。")
        return

    success_count = 0
    skip_count = 0
    error_count = 0

    for f_name in temp_files:
        # [ZERO_DATA] マーカーファイルの処理
        if f_name.startswith("[ZERO_DATA]"):
            clean_name = f_name.replace("[ZERO_DATA]", "")
            dest_zip_name = clean_name.replace(".csv", ".zip")
            dest_zip_path = os.path.join(DEST_DIR, dest_zip_name)
            
            # すでに過去の正規データがある場合は、今月の0件データで上書きせずスキップ
            if os.path.exists(dest_zip_path):
                print(f"  [スキップ (既存データ維持)] {f_name} -> 既に過去データが存在します")
                skip_count += 1
            else:
                # 既存データがない場合は、マーカーファイルをコピー
                shutil.copy2(os.path.join(SRC_DIR, f_name), os.path.join(DEST_DIR, f_name))
                print(f"  [コピー (新規ゼロデータ)] {f_name} をコピーしました")
                success_count += 1
            continue

        if not (f_name.endswith(".zip") or f_name.endswith(".csv")):
            continue

        src_file_path = os.path.join(SRC_DIR, f_name)
        # 最終保存先ではZIP形式で統一する
        dest_filename = f_name.replace(".csv", ".zip")
        dest_file_path = os.path.join(DEST_DIR, dest_filename)

        try:
            if os.path.exists(dest_file_path):
                # 既存のZIPが存在する場合はマージ
                print(f"  [マージ処理] {dest_filename} ...")
                
                # 新規と既存のCSV内容をロード
                new_content, csv_filename = read_zip_csv(src_file_path)
                exist_content, _ = read_zip_csv(dest_file_path)
                
                # マージ
                merged_content = merge_csv_content(exist_content, new_content)
                
                # 上書き保存
                write_zip_csv(dest_file_path, merged_content, csv_filename)
                success_count += 1
            else:
                # 既存データがない場合はそのままコピー
                print(f"  [新規コピー] {dest_filename} ...")
                shutil.copy2(src_file_path, dest_file_path)
                success_count += 1
        except Exception as e:
            print(f"  [エラー] {f_name} のマージ失敗: {e}")
            traceback.print_exc()
            error_count += 1

    print(f"\nマージ処理完了: 成功 {success_count} 件 / スキップ {skip_count} 件 / エラー {error_count} 件")

    # 処理が完了し、エラーがなければ一時フォルダをクリーンアップ
    if error_count == 0:
        print("\n[一時フォルダのクリーンアップを開始します]")
        for f_name in temp_files:
            try:
                os.remove(os.path.join(SRC_DIR, f_name))
            except Exception as e:
                print(f"  [警告] 一時ファイルの削除に失敗: {f_name} ({e})")
        print("一時フォルダのクリーンアップが完了しました。")
    else:
        print("\n[警告] エラーが発生したため、一時フォルダのクリーンアップはスキップしました。データを調査してください。")

if __name__ == "__main__":
    process_merge()
