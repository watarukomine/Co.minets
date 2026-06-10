# -*- coding: utf-8 -*-
import csv
import json
import os
import math
import time
import zipfile
import io
import requests
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# 標準出力を即座にフラッシュ
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except AttributeError:
        import sys as _sys
        _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "extracted_data")
OUTPUT_JS = os.path.join(BASE_DIR, "data_matrix.js")
DATA_DIR = os.path.join(BASE_DIR, "data")
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
SYNC_PROGRESS_FILE = os.path.join(BASE_DIR, "sync_progress.json")

# スレッド間共有リソースとロック
lock = threading.RLock()
success_count = 0
fail_count = 0
skip_count = 0
failed_details = []
completed_set = set()
progress = {}

# トークン管理用グローバル変数
token_lock = threading.Lock()
global_token = None
token_expires_at = 0

def get_valid_token(force_refresh=False):
    global global_token, token_expires_at
    with token_lock:
        now = time.time()
        if force_refresh or not global_token or now >= token_expires_at - 300:
            print("[INFO] アクセストークンを更新中...", flush=True)
            for attempt in range(3):
                new_token = get_access_token()
                if new_token:
                    global_token = new_token
                    token_expires_at = now + 3600
                    break
                time.sleep(2)
        return global_token


def get_access_token():
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=['https://www.googleapis.com/auth/datastore']
        )
        creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"[ERROR] トークン取得失敗: {e}", flush=True)
        return None

def _load_sync_progress():
    if os.path.exists(SYNC_PROGRESS_FILE):
        try:
            with open(SYNC_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _save_sync_progress_safe(prog):
    with lock:
        try:
            with open(SYNC_PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prog, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] 進捗ファイル保存失敗: {e}", flush=True)

def sync_to_cloud_full(metadata, metric, route, cls, branches):
    project_id = "cominet-8799b"
    db_id = "cominets"

    doc_id = f"{metric}_{route}_{cls}".replace("/", "-").replace(" ", "")
    doc_path = f"projects/{project_id}/databases/{db_id}/documents/dashboard_data/{doc_id}"
    
    # 1. 親ドキュメントの更新日時を更新
    tk = get_valid_token()
    if tk:
        headers = {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"}
        update_time_url = f"https://firestore.googleapis.com/v1/{doc_path}?updateMask.fieldPaths=updatedAt"
        try:
            requests.patch(update_time_url, json={"fields": {"updatedAt": {"stringValue": metadata["updatedAt"]}}}, headers=headers, timeout=10)
        except: pass

    batch_limit = 5  # トランザクションサイズエラー回避のための小さなバッチサイズ
    writes = []
    
    def commit_batch(w_list):
        if not w_list: return True
        tk_local = get_valid_token()
        if not tk_local: return False
        
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents:commit"
        headers_local = {"Authorization": f"Bearer {tk_local}", "Content-Type": "application/json"}
        try:
            res = requests.post(url, json={"writes": w_list}, headers=headers_local, timeout=20)
            if res.status_code == 401:
                print(f"  [INFO] トークン失効を検知。再取得してリトライします... ({doc_id})", flush=True)
                tk_local = get_valid_token(force_refresh=True)
                if not tk_local: return False
                headers_local["Authorization"] = f"Bearer {tk_local}"
                res = requests.post(url, json={"writes": w_list}, headers=headers_local, timeout=20)
                
            if res.status_code != 200:
                print(f"  [ERROR] Commit failed for {doc_id}: {res.status_code} {res.text}", flush=True)
                return False
            return True
        except Exception as e:
            print(f"  [ERROR] Request failed for {doc_id}: {e}", flush=True)
            return False

    all_success = True
    for bname, bdata in branches.items():
        bid = bname.replace("/", "-")
        branch_path = f"{doc_path}/branches/{bid}"

        # c, p に全データを保存し、c_ext, p_ext をクリアするフル同期
        writes.append({
            "update": {
                "name": branch_path,
                "fields": {
                    "c": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in bdata["current"]]}},
                    "p": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in bdata["previous"]]}},
                    "c_ext": {"arrayValue": {"values": []}},
                    "p_ext": {"arrayValue": {"values": []}}
                }
            }
        })
        
        if len(writes) >= batch_limit:
            if not commit_batch(writes):
                all_success = False
            writes = []
            
    if writes:
        if not commit_batch(writes):
            all_success = False
            
    return all_success

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

def process_single_file(f_name, total_files):
    global success_count, fail_count, skip_count, completed_set, failed_details
    try:
        clean_name = f_name.replace("[ZERO_DATA]", "")
        metric = clean_name.split('】')[0].replace('【', '')
        rest = clean_name.split('】')[1].replace('.csv', '').replace('.zip', '')
        rest = rest.replace('鉱油', '礦油')
        route, classification = rest.split('_', 1) if '_' in rest else (rest, "全体")
        doc_id = f"{metric}_{route}_{classification}".replace("/", "-").replace(" ", "")

        with lock:
            if doc_id in completed_set:
                skip_count += 1
                return

        if f_name.startswith("[ZERO_DATA]"):
            with lock:
                completed_set.add(doc_id)
                progress["completed"] = list(completed_set)
                success_count += 1
            return

        filepath = os.path.join(DOWNLOAD_DIR, f_name)
        data = process_csv_to_matrix(filepath)
        if not data:
            with lock:
                fail_count += 1
                failed_details.append(f"{f_name}: データ読み込み失敗")
            return

        # タイムラインに沿って整形
        timeline = progress["timeline"]
        branch_matrix = {}
        for branch, date_map in data.items():
            cl, pl = [], []
            for d in timeline:
                vals = date_map.get(d, {'current': 0, 'previous': 0})
                cl.append(vals['current'])
                pl.append(vals['previous'])
            branch_matrix[branch] = {'current': cl, 'previous': pl}

        # 1. 個別JSON保存（ローカル）
        fid = doc_id
        with open(os.path.join(DATA_DIR, f"{fid}.json"), 'w', encoding='utf-8') as f:
            json.dump(branch_matrix, f, ensure_ascii=False)

        # 2. クラウド同期（フル同期）
        sync_success = False
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if sync_to_cloud_full(progress, metric, route, classification, branch_matrix):
                    sync_success = True
                    break
                else:
                    raise ConnectionError("Firestore commit failed")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print(f"  [ERROR] {f_name} 同期失敗: {e}", flush=True)

        should_save = False
        with lock:
            if sync_success:
                completed_set.add(doc_id)
                progress["completed"] = list(completed_set)
                success_count += 1
                
                total_done = skip_count + success_count
                if success_count % 50 == 0 or total_done % 100 == 0:
                    should_save = True
            else:
                fail_count += 1
                failed_details.append(f"{f_name}: クラウド同期失敗")
                total_done = skip_count + success_count

        if should_save:
            _save_sync_progress_safe(progress)
            print(f"進捗: {total_done}/{total_files} 件完了 (成功:{success_count}, 失敗:{fail_count})", flush=True)
    except Exception as e:
        with lock:
            fail_count += 1
            failed_details.append(f"{f_name}: 例外発生 {e}")
        print(f"  [CRITICAL ERROR] {f_name} の処理中に未キャッチの例外発生: {e}", flush=True)
        import traceback
        traceback.print_exc()

def main():
    global progress, completed_set
    updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n--- {updated_at} 並列・フル同期処理開始 ---", flush=True)

    progress = _load_sync_progress()
    if not progress:
        print("[ERROR] 同期進捗ファイル (sync_progress.json) が見つかりません。", flush=True)
        return

    # コマンドライン引数で進捗をリセットするか判定
    reset_completed = True
    if len(sys.argv) > 1 and sys.argv[1] == "--resume":
        reset_completed = False

    if reset_completed:
        print("[INFO] 同期完了リストをリセットし、最初から全件フル同期します。", flush=True)
        progress["completed"] = []
        _save_sync_progress_safe(progress)

    timeline = progress["timeline"]
    print(f"Timeline Length: {len(timeline)}", flush=True)

    target_files = [f for f in os.listdir(DOWNLOAD_DIR) if (f.startswith("【") or f.startswith("[ZERO_DATA]")) and (f.endswith(".csv") or f.endswith(".zip"))]
    total_files = len(target_files)
    print(f"Total files: {total_files}", flush=True)

    # 初回トークン取得（有効性確認）
    if not get_valid_token():
        print("[ERROR] トークンの取得に失敗しました。", flush=True)
        return

    # メタデータの更新
    print("[FIRESTORE] メタデータを更新中...", flush=True)
    tk = get_valid_token()
    headers = {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"}
    meta_url = f"https://firestore.googleapis.com/v1/projects/cominet-8799b/databases/cominets/documents/dashboard_metadata/current"
    meta_fields = {
        "updatedAt": {"stringValue": updated_at},
        "timeline": {"arrayValue": {"values": [{"stringValue": t} for t in timeline]}},
        "metrics": {"arrayValue": {"values": [{"stringValue": m} for m in progress["metrics"]]}},
        "routes": {"arrayValue": {"values": [{"stringValue": r} for r in progress["routes"]]}},
        "classes": {"arrayValue": {"values": [{"stringValue": c} for c in progress["classes"]]}},
        "branches": {"arrayValue": {"values": [{"stringValue": b} for b in progress["branches"]]}}
    }
    requests.patch(f"{meta_url}?updateMask.fieldPaths=updatedAt&updateMask.fieldPaths=timeline&updateMask.fieldPaths=metrics&updateMask.fieldPaths=routes&updateMask.fieldPaths=classes&updateMask.fieldPaths=branches",
                   json={"fields": meta_fields}, headers=headers)

    # 完了リストをロード
    completed_set = set(progress.get("completed", []))
    print(f"Already completed: {len(completed_set)} patterns", flush=True)

    # ThreadPoolExecutorによる並列実行 (max_workers=8)
    print("[RUNNING] 並列スレッド実行を開始します (スレッド数: 8)...", flush=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        for f_name in target_files:
            executor.submit(process_single_file, f_name, total_files)

    # 最終的な保存
    _save_sync_progress_safe(progress)

    # 最後に data_matrix.js のメタデータも上書き
    metadata_js = {
        "updatedAt": updated_at,
        "timeline": timeline,
        "branches": progress["branches"],
        "metrics": progress["metrics"],
        "routes": progress["routes"],
        "classes": progress["classes"]
    }
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write("const DATA_MATRIX = ")
        json.dump(metadata_js, f, ensure_ascii=False)
        f.write(";")

    print(f"\n--- 同期処理完了サマリー ---", flush=True)
    print(f"総ファイル数: {total_files}", flush=True)
    print(f"新規成功: {success_count}", flush=True)
    print(f"失敗: {fail_count}", flush=True)
    print(f"スキップ(既済): {skip_count}", flush=True)

if __name__ == "__main__":
    main()
