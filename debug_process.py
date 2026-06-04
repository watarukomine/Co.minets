import os
import json
import time
import zipfile
import csv
import io
import sys

# 標準出力を即座にフラッシュ
sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "extracted_data")
DATA_DIR = os.path.join(BASE_DIR, "data")

def process_csv_to_matrix(filepath):
    raw_data = {}
    if not os.path.exists(filepath): return None
    try:
        if filepath.endswith('.zip'):
            with zipfile.ZipFile(filepath, 'r') as z:
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    content = f.read().decode('utf-8-sig')
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        _process_row(row, raw_data)
        else:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    _process_row(row, raw_data)
    except Exception as e:
        print(f"Failed to read {filepath}: {e}", flush=True)
    return raw_data

def _process_row(row, raw_data):
    try:
        branch = row.get('支社', row.get('管轄支社名', '')).strip()
        if not branch: return
        date_str = row.get('日付', '').split(' ')[0]
        if not date_str: return
        cur_str = row.get('当年', '0').replace(',', '').strip()
        prev_str = row.get('前年', '0').replace(',', '').strip()
        current = float(cur_str) if cur_str else 0.0
        previous = float(prev_str) if prev_str else 0.0
        if branch not in raw_data: raw_data[branch] = {}
        raw_data[branch][date_str] = {'current': current, 'previous': previous}
    except Exception:
        pass

def main():
    print("--- Debug Process Start ---", flush=True)
    target_files = [f for f in os.listdir(DOWNLOAD_DIR) if (f.startswith("【") or f.startswith("[ZERO_DATA]")) and (f.endswith(".csv") or f.endswith(".zip"))]
    print(f"Total files found: {len(target_files)}", flush=True)
    
    # タイムラインの代わりにダミーを使用
    timeline = ["2026-05-01", "2026-05-02", "2026-05-31"]
    
    # 本物のファイルと ZERO_DATA ファイルをそれぞれ 3 件ずつテスト
    test_files = []
    real_count = 0
    zero_count = 0
    for f in target_files:
        if f.startswith("[ZERO_DATA]") and zero_count < 3:
            test_files.append(f)
            zero_count += 1
        elif f.startswith("【") and real_count < 3:
            test_files.append(f)
            real_count += 1
            
    print(f"Test files: {test_files}", flush=True)
    
    for f_name in test_files:
        t0 = time.time()
        print(f"\nProcessing: {f_name} ...", end="", flush=True)
        
        clean_name = f_name.replace("[ZERO_DATA]", "")
        metric = clean_name.split('】')[0].replace('【', '')
        rest = clean_name.split('】')[1].replace('.csv', '').replace('.zip', '')
        rest = rest.replace('鉱油', '礦油')
        route, classification = rest.split('_', 1) if '_' in rest else (rest, "全体")
        doc_id = f"{metric}_{route}_{classification}".replace("/", "-").replace(" ", "")
        
        if f_name.startswith("[ZERO_DATA]"):
            t1 = time.time()
            print(f" [SKIP (ZERO)] (Time: {t1-t0:.4f}s)", flush=True)
            continue
            
        # 本物ファイルの処理
        filepath = os.path.join(DOWNLOAD_DIR, f_name)
        data = process_csv_to_matrix(filepath)
        if not data:
            print(" [FAILED (NO DATA)]", flush=True)
            continue
            
        branch_matrix = {}
        for branch, date_map in data.items():
            cl, pl = [], []
            for d in timeline:
                vals = date_map.get(d, {'current': 0, 'previous': 0})
                cl.append(vals['current'])
                pl.append(vals['previous'])
            branch_matrix[branch] = {'current': cl, 'previous': pl}
            
        # JSON保存
        json_path = os.path.join(DATA_DIR, f"debug_{doc_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(branch_matrix, f, ensure_ascii=False)
            
        t1 = time.time()
        print(f" [OK] Saved to debug_{doc_id}.json (Time: {t1-t0:.4f}s)", flush=True)
        
    print("\n--- Debug Process End ---", flush=True)

if __name__ == "__main__":
    main()
