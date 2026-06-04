import csv
import json
import os
import math
import glob
import time
import zipfile
import io
import logging

import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import sys as _sys
        _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
        _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8')

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# 共通設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "extracted_data")
OUTPUT_JSON = os.path.join(BASE_DIR, "data_matrix.json")
OUTPUT_JS = os.path.join(BASE_DIR, "data_matrix.js")
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
SYNC_PROGRESS_FILE = os.path.join(BASE_DIR, "sync_progress.json")

def get_access_token():
    """サービスアカウントからアクセストークンを取得"""
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
        print(f"[ERROR] トークン取得失敗: {e}")
        return None

def _load_sync_progress():
    """同期進捗ファイルを読み込む"""
    if os.path.exists(SYNC_PROGRESS_FILE):
        try:
            with open(SYNC_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": None, "timeline_len": 0, "timeline": [], "completed": [], "mode": "full", "delta_start": 0}

def _save_sync_progress(progress):
    """同期進捗ファイルを保存する"""
    with open(SYNC_PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def _detect_append(old_timeline, new_timeline):
    """末尾追記かどうかを判定。追記ならdelta_start indexを返す"""
    old_len = len(old_timeline)
    if old_len == 0 or len(new_timeline) <= old_len:
        return False, 0
    # サンプリング比較で高速判定（先頭・中間・末尾）
    checks = [0, old_len // 4, old_len // 2, 3 * old_len // 4, old_len - 1]
    for idx in checks:
        if old_timeline[idx] != new_timeline[idx]:
            return False, 0
    return True, old_len

def sync_to_cloud_iterative(metadata, metric, route, cls, branches, force_full=False, progress=None):
    """REST API 経由で1ドキュメント（1パターン）ずつ Firestore にデータをアップロード"""
    import requests
    token = get_access_token()
    if not token: return False
    
    project_id = "cominet-8799b"
    db_id = "cominets"
    base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    new_timeline = metadata["timeline"]
    doc_id = f"{metric}_{route}_{cls}".replace("/", "-").replace(" ", "")
    
    # 進捗チェック (同じバージョン・同じドキュメントならスキップ)
    if progress and doc_id in progress.get("completed", []) and progress.get("version") == metadata["updatedAt"]:
        return True

    sync_mode = progress.get("mode", "full") if progress else "full"
    delta_start = progress.get("delta_start", 0) if progress else 0

    doc_path = f"projects/{project_id}/databases/{db_id}/documents/dashboard_data/{doc_id}"
    
    # 1. 親ドキュメントの更新日時を更新 (単独でコミット)
    update_time_url = f"https://firestore.googleapis.com/v1/{doc_path}?updateMask.fieldPaths=updatedAt"
    try:
        requests.patch(update_time_url, json={"fields": {"updatedAt": {"stringValue": metadata["updatedAt"]}}}, headers=headers, timeout=30)
    except: pass

    batch_limit = 35 # 31ブランチを一括で送信できるようにサイズ制限内に調整

    def commit_batch(w_list):
        if not w_list: return True
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents:commit"
        try:
            res = requests.post(url, json={"writes": w_list}, headers=headers, timeout=60)
            if res.status_code != 200:
                print(f"  [ERROR] Commit failed: {res.status_code} {res.text}")
                return False
            return True
        except Exception as e:
            print(f"  [ERROR] Request failed: {e}")
            return False

    all_success = True
    writes = []
    
    for bname, bdata in branches.items():
        bid = bname.replace("/", "-")
        branch_path = f"{doc_path}/branches/{bid}"

        if sync_mode == "append" and not force_full:
            c_ext = bdata["current"][delta_start:]
            p_ext = bdata["previous"][delta_start:]
            writes.append({"update": {
                "name": branch_path,
                "fields": {
                    "c_ext": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in c_ext]}},
                    "p_ext": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in p_ext]}}
                }
            }, "updateMask": {"fieldPaths": ["c_ext", "p_ext"]}})
        else:
            writes.append({"update": {
                "name": branch_path,
                "fields": {
                    "c": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in bdata["current"]]}},
                    "p": {"arrayValue": {"values": [{"doubleValue": float(v)} for v in bdata["previous"]]}},
                    "c_ext": {"arrayValue": {"values": []}},
                    "p_ext": {"arrayValue": {"values": []}}
                }
            }})
        
        if len(writes) >= batch_limit:
            if not commit_batch(writes):
                all_success = False
            writes = []
    
    if writes:
        if not commit_batch(writes):
            all_success = False
            
    return all_success

def process_csv_to_matrix(filepath):
    """1つのCSVまたはZIPを解析"""
    raw_data = {}
    if not os.path.exists(filepath): return None
    
    try:
        if filepath.endswith('.zip'):
            with zipfile.ZipFile(filepath, 'r') as z:
                # ZIP内の最初のファイルを読み込む
                csv_filename = z.namelist()[0]
                with z.open(csv_filename) as f:
                    # bytesをテキストに変換
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
        print(f"Failed to read {filepath}: {e}")
    return raw_data

def _process_row(row, raw_data):
    """1行分の処理ロジックを共通化"""
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

def run_once(local_only=False, force_full=False, skip_scan=False):
    updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n--- {updated_at} 処理開始 (省メモリモード) ---")
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"[ERROR] フォルダなし: {DOWNLOAD_DIR}")
        return

    target_files = [f for f in os.listdir(DOWNLOAD_DIR) if (f.startswith("【") or f.startswith("[ZERO_DATA]")) and (f.endswith(".csv") or f.endswith(".zip"))]
    if not target_files:
        print("[INFO] 対象フォルダに処理対象のCSV/ZIPが見つかりません。")
        return

    progress = _load_sync_progress()
    
    # --- Pass 1: メタデータ（タイムライン等）の収集 ---
    if skip_scan and progress.get("timeline"):
        print("[PASS 1] スキャンをスキップし、既存のメタデータを使用します。")
        timeline = progress["timeline"]
        metadata = {
            "updatedAt": updated_at,
            "timeline": timeline,
            "branches": progress.get("branches", []),
            "metrics": progress.get("metrics", []),
            "routes": progress.get("routes", []),
            "classes": progress.get("classes", [])
        }
    else:
        print(f"[PASS 1] タイムラインとメタデータをスキャン中 ({len(target_files)}件)...")
        all_dates = set()
        all_branches = set()
        all_metrics, all_routes, all_classes = set(), set(), set()
        
        for i, f_name in enumerate(target_files):
            if (i + 1) % 200 == 0: print(f"  スキャン済み: {i+1}/{len(target_files)} 件...")
            try:
                # [ZERO_DATA] のプレフィックスを考慮
                clean_name = f_name.replace("[ZERO_DATA]", "")
                metric = clean_name.split('】')[0].replace('【', '')
                rest = clean_name.split('】')[1].replace('.csv', '').replace('.zip', '')
                rest = rest.replace('鉱油', '礦油')
                route, classification = rest.split('_', 1) if '_' in rest else (rest, "全体")
                all_metrics.add(metric); all_routes.add(route); all_classes.add(classification)
                
                if not f_name.startswith("[ZERO_DATA]"):
                    # 高速スキャン：日付だけ取得
                    filepath = os.path.join(DOWNLOAD_DIR, f_name)
                    if f_name.endswith('.zip'):
                        with zipfile.ZipFile(filepath, 'r') as z:
                            csv_filename = z.namelist()[0]
                            with z.open(csv_filename) as f:
                                content = f.read().decode('utf-8-sig')
                                reader = csv.DictReader(io.StringIO(content))
                                for row in reader:
                                    d = row.get('日付', '').split(' ')[0]
                                    if d: all_dates.add(d)
                                    b = row.get('支社', row.get('管轄支社名', '')).strip()
                                    if b: all_branches.add(b)
                    else:
                        with open(filepath, 'r', encoding='utf-8-sig') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                d = row.get('日付', '').split(' ')[0]
                                if d: all_dates.add(d)
                                b = row.get('支社', row.get('管轄支社名', '')).strip()
                                if b: all_branches.add(b)
            except: pass

        if not all_dates:
            print("[ERROR] 有効なデータが見つかりませんでした。")
            return

        timeline = sorted(list(all_dates))
        metadata = {
            "updatedAt": updated_at,
            "timeline": timeline,
            "branches": sorted(list(all_branches)),
            "metrics": sorted(list(all_metrics)),
            "routes": sorted(list(all_routes)),
            "classes": sorted(list(all_classes))
        }

    # ローカルのメタデータ保存
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write("const DATA_MATRIX = ")
        json.dump(metadata, f, ensure_ascii=False)
        f.write(";")

    # --- Firestore メタデータ更新 ---
    progress = _load_sync_progress()
    if not local_only:
        print("[FIRESTORE] メタデータを更新中...")
        token = get_access_token()
        if token:
            import requests
            project_id = "cominet-8799b"
            db_id = "cominets"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            meta_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/{db_id}/documents/dashboard_metadata/current"
            meta_fields = {
                "updatedAt": {"stringValue": updated_at},
                "timeline": {"arrayValue": {"values": [{"stringValue": t} for t in timeline]}},
                "metrics": {"arrayValue": {"values": [{"stringValue": m} for m in metadata["metrics"]]}},
                "routes": {"arrayValue": {"values": [{"stringValue": r} for r in metadata["routes"]]}},
                "classes": {"arrayValue": {"values": [{"stringValue": c} for c in metadata["classes"]]}},
                "branches": {"arrayValue": {"values": [{"stringValue": b} for b in metadata["branches"]]}}
            }
            requests.patch(f"{meta_url}?updateMask.fieldPaths=updatedAt&updateMask.fieldPaths=timeline&updateMask.fieldPaths=metrics&updateMask.fieldPaths=routes&updateMask.fieldPaths=classes&updateMask.fieldPaths=branches",
                           json={"fields": meta_fields}, headers=headers)

    # 同期モード判定
    is_append, ds = _detect_append(progress.get("timeline", []), timeline)
    sync_mode = "append" if is_append and not force_full else "full"
    delta_start = ds if sync_mode == "append" else 0
    
    # レジューム判定: タイムラインが同一なら進捗を維持
    if sync_mode == "full":
        if not force_full and progress.get("timeline") == timeline:
            print("[INFO] タイムラインが前回と同一のため、既存の進捗を維持します。")
            completed_set = set(progress.get("completed", []))
        else:
            print("[INFO] タイムラインの変更または強制フラグにより、進捗をリセットします。")
            completed_set = set()
    else:
        completed_set = set(progress.get("completed", []))

    progress = {
        "version": updated_at,
        "timeline_len": len(timeline),
        "timeline": timeline,
        "completed": list(completed_set),
        "mode": sync_mode,
        "delta_start": delta_start,
        "branches": metadata.get("branches", []),
        "metrics": metadata.get("metrics", []),
        "routes": metadata.get("routes", []),
        "classes": metadata.get("classes", [])
    }
    _save_sync_progress(progress)

    # --- Pass 2: 個別データの処理とアップロード ---
    print(f"[PASS 2] 個別データの処理と同期を開始 ({sync_mode}モード)...")
    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_details = []

    for i, f_name in enumerate(target_files):
        try:
            # [ZERO_DATA] のプレフィックスを考慮
            clean_name = f_name.replace("[ZERO_DATA]", "")
            metric = clean_name.split('】')[0].replace('【', '')
            rest = clean_name.split('】')[1].replace('.csv', '').replace('.zip', '')
            rest = rest.replace('鉱油', '礦油')
            route, classification = rest.split('_', 1) if '_' in rest else (rest, "全体")
            doc_id = f"{metric}_{route}_{classification}".replace("/", "-").replace(" ", "")

            if doc_id in completed_set:
                skip_count += 1
                continue

            if f_name.startswith("[ZERO_DATA]"):
                print(f"  [SKIP] {f_name} はデータなしとしてマークされました。")
                completed_set.add(doc_id)
                progress["completed"] = list(completed_set)
                success_count += 1
                continue

            # リトライループ
            max_retries = 2
            data = None
            for attempt in range(max_retries):
                try:
                    data = process_csv_to_matrix(os.path.join(DOWNLOAD_DIR, f_name))
                    if not data:
                        raise ValueError("Data loading failed (empty or invalid)")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  [RETRY] {f_name} の読み込みに失敗、再試行します... ({e})")
                        time.sleep(2)
                    else:
                        raise

            if not data:
                fail_count += 1
                failed_details.append(f"{f_name}: データの読み込み失敗")
                continue

            # タイムラインに沿って整形
            branch_matrix = {}
            for branch, date_map in data.items():
                cl, pl = [], []
                for d in timeline:
                    vals = date_map.get(d, {'current': 0, 'previous': 0})
                    cl.append(vals['current']); pl.append(vals['previous'])
                branch_matrix[branch] = {'current': cl, 'previous': pl}

            # 1. 個別JSON保存
            fid = doc_id
            with open(os.path.join(DATA_DIR, f"{fid}.json"), 'w', encoding='utf-8') as f:
                json.dump(branch_matrix, f, ensure_ascii=False)

            # 2. クラウド同期
            if local_only:
                success_count += 1
            else:
                sync_success = False
                for attempt in range(max_retries):
                    try:
                        if sync_to_cloud_iterative(metadata, metric, route, classification, branch_matrix, force_full=force_full, progress=progress):
                            sync_success = True
                            break
                        else:
                            raise ConnectionError("Firestore commit failed")
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"  [RETRY] {f_name} の同期に失敗、再試行します... ({e})")
                            time.sleep(5)
                        else:
                            print(f"  [ERROR] {f_name} の同期に失敗: {e}")

                if sync_success:
                    completed_set.add(doc_id)
                    progress["completed"] = list(completed_set)
                    success_count += 1
                    if len(completed_set) % 10 == 0:
                        _save_sync_progress(progress)
                        print(f"  進捗: {len(completed_set)}/{len(target_files)} 件完了 (失敗:{fail_count})")
                else:
                    fail_count += 1
                    failed_details.append(f"{f_name}: クラウド同期失敗")

            # 明示的にメモリ解放
            del data
            del branch_matrix
        except Exception as e:
            fail_count += 1
            failed_details.append(f"{f_name}: {e}")
            print(f"  [ERROR] {f_name} の処理中に例外発生: {e}")

    _save_sync_progress(progress)
    
    print(f"\n--- 処理完了サマリー ---")
    print(f"総ファイル数: {len(target_files)}")
    print(f"新規成功: {success_count}")
    print(f"失敗: {fail_count}")
    print(f"スキップ(既済): {skip_count}")
    
    if fail_count > 0:
        print("\n[WARNING] 以下のファイルで問題が発生しました:")
        for detail in failed_details[:20]:
            print(f"  - {detail}")
        if len(failed_details) > 20:
            print(f"  ...他 {len(failed_details)-20} 件")
    else:
        print("\n[SUCCESS] 全ての処理が正常に完了しました！")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="実績データ処理・Firestore同期")
    parser.add_argument("--watch", action="store_true", help="ファイル変更を監視して自動処理")
    parser.add_argument("--local-only", action="store_true", help="ローカル保存のみ（Firestore同期スキップ）")
    parser.add_argument("--consolidate", action="store_true", help="全件再同期（c_ext を c に統合）")
    parser.add_argument("--resume", action="store_true", help="Pass 1 をスキップして前回の続きから再開")
    args = parser.parse_args()
    if args.watch:
        print("[WATCH] 監視モード開始...")
        last_state = None
        while True:
            try:
                current_files = os.listdir(DOWNLOAD_DIR)
                current_state = [(f, os.path.getmtime(os.path.join(DOWNLOAD_DIR, f))) for f in current_files if f.endswith(".csv")]
                if current_state != last_state:
                    run_once(local_only=args.local_only, force_full=args.consolidate, skip_scan=args.resume)
                    last_state = current_state
                time.sleep(10)
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error in main loop: {e}"); time.sleep(10)
    else:
        run_once(local_only=args.local_only, force_full=args.consolidate, skip_scan=args.resume)

if __name__ == "__main__":
    main()
