# -*- coding: utf-8 -*-
import os
import csv
import io
import shutil
import zipfile
import traceback
import json
import time

# プロキシ自動バイパス
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

SRC_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data_temp"
DEST_DIR = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI\extracted_data"

def safe_x_drive_op(op_func, *args, retries=5, delay=3, **kwargs):
    """Xドライブの接続一時切断(WinError 1237等)に対応するリトライラッパー"""
    for i in range(retries):
        try:
            return op_func(*args, **kwargs)
        except OSError as e:
            print(f"  [WARNING] Xドライブ操作失敗 (試行 {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

def load_target_month_str():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "target_month.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                info = json.load(f)
                y = info.get("year")
                m = info.get("month")
                if y and m:
                    return f"{y:04d}-{m:02d}"
        except Exception:
            pass
    return None

def validate_csv_content(csv_content, target_month_str):
    """CSVデータ内に対象年月のレコードが1件以上含まれているか確認する"""
    if not target_month_str:
        return True # 対象年月が特定できない場合はスルー
        
    target_prefix = target_month_str
    target_prefix_slash = target_month_str.replace("-", "/")
    
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)
    row_count = 0
    for row in reader:
        row_count += 1
        date_str = row.get('日付', '')
        if not date_str:
            continue
        if date_str.startswith(target_prefix) or date_str.startswith(target_prefix_slash):
            return True
            
    if row_count == 0:
        return False
        
    return False

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
    target_month_str = load_target_month_str()
    print(f"  [情報] 対象年月: {target_month_str}")

    # 不足リスト (missing_patterns.json) のロード
    base_dir = os.path.dirname(os.path.abspath(__file__))
    missing_patterns_json = os.path.join(base_dir, "missing_patterns.json")
    missing_list = []
    if os.path.exists(missing_patterns_json):
        try:
            with open(missing_patterns_json, "r", encoding="utf-8") as f:
                missing_list = json.load(f)
        except Exception as e:
            print(f"  [警告] missing_patterns.json のロードに失敗しました: {e}")

    # 元の不足ファイル名セット
    processed_filenames = set()

    if not safe_x_drive_op(os.path.exists, SRC_DIR):
        print(f"[警告] 送り元フォルダが見つかりません: {SRC_DIR}")
        return

    if not safe_x_drive_op(os.path.exists, DEST_DIR):
        safe_x_drive_op(os.makedirs, DEST_DIR)

    temp_files = safe_x_drive_op(os.listdir, SRC_DIR)
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
            
            # すでに過去の正規データがある場合でも、今月の0件マーカーをコピーして両存させる
            try:
                safe_x_drive_op(shutil.copy2, os.path.join(SRC_DIR, f_name), os.path.join(DEST_DIR, f_name))
                if safe_x_drive_op(os.path.exists, dest_zip_path):
                    print(f"  [コピー＆既存維持] {f_name} をコピーしました（過去データZIPも維持されます）")
                else:
                    print(f"  [コピー (新規ゼロデータ)] {f_name} をコピーしました")
                success_count += 1
                processed_filenames.add(clean_name)
            except Exception as e:
                print(f"  [エラー] {f_name} のコピーに失敗しました: {e}")
                error_count += 1
            continue

        if not (f_name.endswith(".zip") or f_name.endswith(".csv")):
            continue

        src_file_path = os.path.join(SRC_DIR, f_name)
        # 最終保存先ではZIP形式で統一する
        dest_filename = f_name.replace(".csv", ".zip")
        dest_file_path = os.path.join(DEST_DIR, dest_filename)

        try:
            # 新規CSV内容をロードして年月バリデーション
            new_content, csv_filename = read_zip_csv(src_file_path)
            
            # 対象年月データが含まれているかチェック
            if not validate_csv_content(new_content, target_month_str):
                raise ValueError(f"CSV内に対象年月 {target_month_str} のデータが1件も含まれていません。またはデータが空です。")

            if safe_x_drive_op(os.path.exists, dest_file_path):
                # 既存のZIPが存在する場合はマージ
                print(f"  [マージ処理] {dest_filename} ...")
                
                exist_content, _ = read_zip_csv(dest_file_path)
                
                # マージ
                merged_content = merge_csv_content(exist_content, new_content)
                
                # 上書き保存
                write_zip_csv(dest_file_path, merged_content, csv_filename)
                success_count += 1
                processed_filenames.add(csv_filename)
            else:
                # 既存データがない場合はそのままコピー
                print(f"  [新規コピー] {dest_filename} ...")
                safe_x_drive_op(shutil.copy2, src_file_path, dest_file_path)
                success_count += 1
                processed_filenames.add(csv_filename)
        except Exception as e:
            print(f"  [エラー] {f_name} のマージまたはバリデーション失敗: {e}")
            traceback.print_exc()
            error_count += 1

    print(f"\nマージ処理完了: 成功 {success_count} 件 / スキップ {skip_count} 件 / エラー {error_count} 件")

    # 不足リストの更新と保存
    if missing_list:
        new_missing_list = [item for item in missing_list if item["filename"] not in processed_filenames]
        if len(new_missing_list) != len(missing_list):
            try:
                with open(missing_patterns_json, "w", encoding="utf-8") as f:
                    json.dump(new_missing_list, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 不足リストを更新しました (残り不足数: {len(new_missing_list)} 件)")
            except Exception as e:
                print(f"  [警告] missing_patterns.json の更新保存失敗: {e}")

    # 処理が完了し、エラーがなければ一時フォルダをクリーンアップ
    if error_count == 0:
        print("\n[一時フォルダのクリーンアップを開始します]")
        for f_name in temp_files:
            try:
                safe_x_drive_op(os.remove, os.path.join(SRC_DIR, f_name))
            except Exception as e:
                print(f"  [警告] 一時ファイルの削除に失敗: {f_name} ({e})")
        print("一時フォルダのクリーンアップが完了しました。")
    else:
        print("\n[警告] エラーが発生したため、一時フォルダのクリーンアップはスキップしました。データを調査してください。")

if __name__ == "__main__":
    process_merge()
