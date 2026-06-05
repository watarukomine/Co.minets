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

# プロキシを自動バイパス（インターネットへの直接接続を優先）
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 標準出力を即座にフラッシュ
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except AttributeError:
        import sys as _sys
        _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding='utf-8', line_buffering=True)

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
        print(f"[ERROR] トークン取得失敗: {e}", flush=True)
        return None

def get_valid_token(force_refresh=False):
    """スレッドセーフな有効トークンの取得と自動更新"""
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

def _load_sync_progress():
    if os.path.exists(SYNC_PROGRESS_FILE):
        try:
            with open(SYNC_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": None, "timeline_len": 0, "timeline": [], "completed": [], "mode": "full", "delta_start": 0}

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

def process_single_file(f_name, total_files, local_only=False):
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
        if local_only:
            sync_success = True
        else:
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
                failed_details.append(f"{f_name}: 同期失敗")
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

def run_once(local_only=False, force_full=False, skip_scan=False):
    global progress, completed_set
    updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n--- {updated_at} 並列同期処理開始 (省メモリモード) ---", flush=True)
    
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"[ERROR] フォルダなし: {DOWNLOAD_DIR}", flush=True)
        return

    # WinError 1237 などのネットワークドライブ切断対策として、まず os.listdir が成功するか検証・リトライ
    print("[INFO] ネットワークドライブの接続を確認中...", flush=True)
    for attempt in range(5):
        try:
            target_files = [f for f in os.listdir(DOWNLOAD_DIR) if (f.startswith("【") or f.startswith("[ZERO_DATA]")) and (f.endswith(".csv") or f.endswith(".zip"))]
            break
        except OSError as e:
            print(f"[WARNING] ネットワークドライブへのアクセスに失敗しました (試行 {attempt+1}/5): {e}", flush=True)
            time.sleep(3)
    else:
        print("[ERROR] ネットワークドライブへの接続を確立できませんでした。処理を中断します。", flush=True)
        sys.exit(1)

    if not target_files:
        print("[INFO] 対象フォルダに処理対象のCSV/ZIPが見つかりません。", flush=True)
        return

    progress = _load_sync_progress()
    
    # --- Pass 1: メタデータ（タイムライン等）の収集 ---
    if skip_scan and progress.get("timeline"):
        print("[PASS 1] スキャンをスキップし、既存のメタデータを使用します。", flush=True)
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
        print(f"[PASS 1] タイムラインとメタデータをスキャン中 ({len(target_files)}件) [スレッド並列版]...", flush=True)
        import concurrent.futures
        import threading
        
        all_dates = set()
        all_branches = set()
        all_metrics, all_routes, all_classes = set(), set(), set()
        
        lock = threading.Lock()
        scan_count = 0
        
        def scan_single_file(f_name):
            nonlocal scan_count
            dates_local = set()
            branches_local = set()
            metric_local = None
            route_local = None
            class_local = None
            
            try:
                clean_name = f_name.replace("[ZERO_DATA]", "")
                metric_local = clean_name.split('】')[0].replace('【', '')
                rest = clean_name.split('】')[1].replace('.csv', '').replace('.zip', '')
                rest = rest.replace('鉱油', '礦油')
                route_local, class_local = rest.split('_', 1) if '_' in rest else (rest, "全体")
                
                if not f_name.startswith("[ZERO_DATA]"):
                    filepath = os.path.join(DOWNLOAD_DIR, f_name)
                    if f_name.endswith('.zip'):
                        with zipfile.ZipFile(filepath, 'r') as z:
                            csv_filename = z.namelist()[0]
                            with z.open(csv_filename) as f:
                                # ネットワークIO削減のため先頭128KBだけ部分ロード
                                chunk = f.read(131072)
                                content = chunk.decode('utf-8-sig', errors='ignore')
                                # 簡易パース (ヘッダー行とデータ行から日付・支社を抽出)
                                lines = content.split('\n')
                                if len(chunk) >= 131072 and len(lines) > 2:
                                    lines = lines[:-1]  # 途中で切れている最後の行を除外
                                
                                if len(lines) > 1:
                                    headers = [h.strip('"') for h in lines[0].split(',')]
                                    date_idx = -1
                                    branch_idx = -1
                                    for idx, h in enumerate(headers):
                                        if '日付' in h: date_idx = idx
                                        elif h in ['支社', '管轄支社名']: branch_idx = idx
                                    
                                    import re
                                    date_pat = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$')
                                    
                                    for line in lines[1:]:
                                        if not line.strip(): continue
                                        cols = [c.strip('"') for c in line.split(',')]
                                        if date_idx >= 0 and date_idx < len(cols):
                                            d = cols[date_idx].split(' ')[0]
                                            if d and date_pat.match(d):
                                                dates_local.add(d)
                                        if branch_idx >= 0 and branch_idx < len(cols):
                                            b = cols[branch_idx].strip()
                                            if b: branches_local.add(b)
                    else:
                        with open(filepath, 'r', encoding='utf-8-sig') as f:
                            # 128KB部分ロード
                            chunk = f.read(131072)
                            content = chunk
                            lines = content.split('\n')
                            if len(chunk) >= 131072 and len(lines) > 2:
                                lines = lines[:-1]  # 途中で切れている最後の行を除外
                            
                            if len(lines) > 1:
                                headers = [h.strip('"') for h in lines[0].split(',')]
                                date_idx = -1
                                branch_idx = -1
                                for idx, h in enumerate(headers):
                                    if '日付' in h: date_idx = idx
                                    elif h in ['支社', '管轄支社名']: branch_idx = idx
                                
                                import re
                                date_pat = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$')
                                
                                for line in lines[1:]:
                                    if not line.strip(): continue
                                    cols = [c.strip('"') for c in line.split(',')]
                                    if date_idx >= 0 and date_idx < len(cols):
                                        d = cols[date_idx].split(' ')[0]
                                        if d and date_pat.match(d):
                                            dates_local.add(d)
                                    if branch_idx >= 0 and branch_idx < len(cols):
                                        b = cols[branch_idx].strip()
                                        if b: branches_local.add(b)
            except Exception as e:
                pass
                
            with lock:
                scan_count += 1
                if scan_count % 500 == 0 or scan_count == len(target_files):
                    print(f"  スキャン済み: {scan_count}/{len(target_files)} 件...", flush=True)
                if metric_local: all_metrics.add(metric_local)
                if route_local: all_routes.add(route_local)
                if class_local: all_classes.add(class_local)
                all_dates.update(dates_local)
                all_branches.update(branches_local)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            executor.map(scan_single_file, target_files)

        if not all_dates:
            print("[ERROR] 有効なデータが見つかりませんでした。", flush=True)
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

    # ローカルのメタデータ保存 (JS & JSON)
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write("const DATA_MATRIX = ")
        json.dump(metadata, f, ensure_ascii=False)
        f.write(";")

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # --- Firestore メタデータ更新 ---
    if not local_only:
        print("[FIRESTORE] メタデータを更新中...", flush=True)
        tk = get_valid_token()
        if tk:
            project_id = "cominet-8799b"
            db_id = "cominets"
            headers = {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"}
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

    # 同期完了リストの維持
    if not force_full and progress.get("timeline") == timeline:
        print("[INFO] タイムラインが前回と同一のため、既存の進捗を維持します。", flush=True)
        completed_set = set(progress.get("completed", []))
    else:
        print("[INFO] タイムラインの変更または強制フラグにより、進捗をリセットします。", flush=True)
        completed_set = set()

    progress = {
        "version": updated_at,
        "timeline_len": len(timeline),
        "timeline": timeline,
        "completed": list(completed_set),
        "mode": "full",
        "delta_start": 0,
        "branches": metadata.get("branches", []),
        "metrics": metadata.get("metrics", []),
        "routes": metadata.get("routes", []),
        "classes": metadata.get("classes", [])
    }
    _save_sync_progress_safe(progress)

    # --- Pass 2: 個別データの処理とアップロード (16スレッド並列実行) ---
    print(f"[PASS 2] 個別データの処理と同期を開始 (16スレッド並列)...", flush=True)
    total_files = len(target_files)
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        for f_name in target_files:
            executor.submit(process_single_file, f_name, total_files, local_only=local_only)

    _save_sync_progress_safe(progress)
    
    print(f"\n--- 同期処理完了サマリー ---", flush=True)
    print(f"総ファイル数: {total_files}", flush=True)
    print(f"新規成功: {success_count}", flush=True)
    print(f"失敗: {fail_count}", flush=True)
    print(f"スキップ(既済): {skip_count}", flush=True)
    
    if fail_count > 0:
        print("\n[WARNING] 以下のファイルで問題が発生しました:", flush=True)
        for detail in failed_details[:20]:
            print(f"  - {detail}", flush=True)
    else:
        print("\n[SUCCESS] 全ての処理が正常に完了しました！", flush=True)

def load_target_month_str():
    json_path = os.path.join(BASE_DIR, "target_month.json")
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
    # デフォルトは前月
    from datetime import datetime
    now = datetime.now()
    y, m = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return f"{y:04d}-{m:02d}"

def load_always_zero_combinations():
    json_path = os.path.join(BASE_DIR, "always_zero_combinations.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [(item['route'], item['sales_class']) for item in data]
        except Exception:
            pass
    return []

def run_scan_only():
    print("\n--- データ精査モード (Scan Only) 開始 ---", flush=True)
    target_month_str = load_target_month_str()
    print(f"[INFO] 精査対象年月: {target_month_str}", flush=True)
    
    # 除外パターンと進捗のロード
    exclude_combos = load_always_zero_combinations()
    exclude_set = set(exclude_combos)
    prog = _load_sync_progress()
    completed_set = set(prog.get("completed", []))
    
    # 2700パターンの定義
    AMOUNT_TYPES = ["売上", "粗利"]
    ROUTES_CORE = ["a-00 総販", "b-01 販売店", "b-02 外販", "b-03 ジェームス", "c-01 卸売", "c-02 直売", "d-01 部品商"]
    ROUTES_DETAIL = ["d-02 その他再販業者", "d-03 修理業者", "d-04 GSS", "d-05 用品小売り店", "d-06 その他", "e-01 修理工場", "e-02 特定修理業者", "e-03 大口ユーザー"]
    ROUTES_ALL = ROUTES_CORE + ROUTES_DETAIL
    
    SALES_CLASSES_CORE = ["100_総売上", "110_総売上（除通信事業）", "200_重点商品", "210_特販部品", "212_競争品", "213_クリーンエアフィルター", "220_タイヤ", "221_GYタイヤ", "222_ミシュランタイヤ", "225_ダンロップタイヤ", "230_バッテリー", "240_礦油", "244_ケミカル", "300_一般部品", "310_外装部品", "321_S部品", "400_用品", "520_工具", "906_一般部品（S部品除き）"]
    SALES_CLASSES_DETAIL = ["211_特販6品目", "214_特販部品その他", "223_レクサスセット", "224_タイヤその他", "231_ACデルコ", "232_パナソニック", "233_GSユアサ", "234_レクサスバッテリー", "235_地場バッテリー", "236_地場パナソニック", "237_地場GSユアサ", "238_パナソニック（本部＋地場）", "239_GSユアサ（本部＋地場）", "241_エンジンオイル", "242_シャシオイル", "243_フルード", "245_礦油その他", "320_機能部品", "410_ナビ", "411_T-Connect対応ナビ", "412_ベーシックナビ", "413_エントリーナビ", "414_ナビキット", "415_T-Connectナビキット", "416_エントリーナビキット", "417_本部扱いナビ", "418_ナビその他", "420_ナビ関連オプション", "421_後席ディスプレイ", "422_モニターカメラ類", "423_地図ソフト", "424_ドライブレコーダー", "425_純正ドライブレコーダー", "426_本部調達ドライブレコーダー", "427_その他ドライブレコーダー", "428_ナビ関連オプションその他", "430_オーディオ", "440_ITS関連商品", "450_ベーシック推奨用品", "460_オプション推販用品", "461_後付け安全4商品", "462_TRD", "463_モデリスタ", "464_オプション推販用品その他", "470_レクサス用品", "480_用品その他", "500_その他", "510_通信事業", "521_本部調達工具", "522_地場工具", "530_C＋WALK（本体）", "540_本部商品その他", "550_新車カタログ", "560_その他（その他）", "901_プレミアムCAF", "902_パナソニックバッテリー（本部＋地場）", "903_GSユアサバッテリー（本部＋地場）", "904_ブレーキフルード", "905_LLC", "907_純正ETC2.0", "907_純正ETC", "909_TCD用品", "910_トヨタ車TRD", "911_レクサス車TRD", "912_トヨタ車モデリスタ", "913_レクサス車モデリスタ", "914_TMP用品", "915_TZ用品", "916_TMP車種専用品", "917_夏タイヤ", "918_冬タイヤ"]
    SALES_CLASSES_ALL = SALES_CLASSES_CORE + SALES_CLASSES_DETAIL
    
    # Xドライブのファイルリストの取得 (WinError 1237 対策リトライ)
    target_files = []
    for attempt in range(5):
        try:
            if os.path.exists(DOWNLOAD_DIR):
                target_files = os.listdir(DOWNLOAD_DIR)
                break
        except OSError as e:
            print(f"[WARNING] ネットワークドライブ接続エラー (精査時試行 {attempt+1}/5): {e}", flush=True)
            time.sleep(3)
            
    files_in_dest = set(target_files)
    
    missing_list = []
    missing_lock = threading.Lock()
    
    def check_pattern(amount, route, sc):
        sc_fname = sc.replace("(", "（").replace(")", "）")
        target_filename = f"【{amount}】{route}_{sc_fname}.csv"
        doc_id = f"{amount}_{route}_{sc}".replace("/", "-").replace(" ", "")
        doc_id = doc_id.replace("鉱油", "礦油")
        
        if (route, sc) in exclude_set:
            return
            
        zip_filename = target_filename.replace(".csv", ".zip")
        zero_filename = f"[ZERO_DATA]{target_filename}"
        
        has_file = False
        file_to_check = None
        
        if zero_filename in files_in_dest:
            has_file = True
            file_to_check = zero_filename
        elif zip_filename in files_in_dest:
            has_file = True
            file_to_check = zip_filename
        elif target_filename in files_in_dest:
            has_file = True
            file_to_check = target_filename
            
        if not has_file:
            with missing_lock:
                missing_list.append({
                    "amount": amount,
                    "route": route,
                    "sales_class": sc,
                    "filename": target_filename,
                    "reason": "Xドライブにファイルが存在しません。"
                })
            return
            
        # CSVデータ妥当性チェック
        if file_to_check.endswith(".zip"):
            zip_path = os.path.join(DOWNLOAD_DIR, file_to_check)
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    csv_name = z.namelist()[0]
                    with z.open(csv_name) as f:
                        # 最初の64KBを部分読み込みしてネットワークIOを削減
                        chunk = f.read(65536).decode('utf-8-sig', errors='ignore')
                        if (target_month_str not in chunk) and (target_month_str.replace("-", "/") not in chunk):
                            # 全体フォールバック
                            content = chunk + f.read().decode('utf-8-sig', errors='ignore')
                            if (target_month_str not in content) and (target_month_str.replace("-", "/") not in content):
                                with missing_lock:
                                    missing_list.append({
                                        "amount": amount,
                                        "route": route,
                                        "sales_class": sc,
                                        "filename": target_filename,
                                        "reason": f"CSV内に対象年月 {target_month_str} のデータが含まれていません。"
                                    })
                                return
            except Exception as e:
                with missing_lock:
                    missing_list.append({
                        "amount": amount,
                        "route": route,
                        "sales_class": sc,
                        "filename": target_filename,
                        "reason": f"ZIPファイル破損または読み込みエラー: {e}"
                    })
                return
                
        if doc_id not in completed_set:
            with missing_lock:
                missing_list.append({
                    "amount": amount,
                    "route": route,
                    "sales_class": sc,
                    "filename": target_filename,
                    "reason": "Firestoreへの同期が完了していません。"
                })

    # ThreadPoolExecutorによる16スレッド並列検証
    patterns = []
    for amount in AMOUNT_TYPES:
        for route in ROUTES_ALL:
            for sc in SALES_CLASSES_ALL:
                patterns.append((amount, route, sc))
                
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(check_pattern, p[0], p[1], p[2]) for p in patterns]
        for fut in futures:
            fut.result()
            
    # 結果の書き出し
    missing_json_path = os.path.join(BASE_DIR, "missing_patterns.json")
    try:
        with open(missing_json_path, 'w', encoding='utf-8') as f:
            json.dump(missing_list, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] 精査完了。不足パターン数: {len(missing_list)} 件", flush=True)
        print(f"不足リストを保存しました: {missing_json_path}", flush=True)
    except Exception as e:
        print(f"[ERROR] 不足リストの保存失敗: {e}", flush=True)
        
    return len(missing_list)
                    
    # 結果の書き出し
    missing_json_path = os.path.join(BASE_DIR, "missing_patterns.json")
    try:
        with open(missing_json_path, 'w', encoding='utf-8') as f:
            json.dump(missing_list, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] 精査完了。不足パターン数: {len(missing_list)} 件", flush=True)
        print(f"不足リストを保存しました: {missing_json_path}", flush=True)
    except Exception as e:
        print(f"[ERROR] 不足リストの保存失敗: {e}", flush=True)
        
    return len(missing_list)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="実績データ処理・Firestore同期 (並列高速化版)")
    parser.add_argument("--watch", action="store_true", help="ファイル変更を監視して自動処理")
    parser.add_argument("--local-only", action="store_true", help="ローカル保存のみ（Firestore同期スキップ）")
    parser.add_argument("--consolidate", action="store_true", help="全件再同期")
    parser.add_argument("--resume", action="store_true", help="Pass 1 をスキップして前回の続きから再開")
    parser.add_argument("--scan-only", action="store_true", help="XドライブとFirestoreの同期整合性を精査し不足データリストを出力")
    args = parser.parse_args()
    
    if args.scan_only:
        missing_count = run_scan_only()
        sys.exit(0 if missing_count == 0 else 1)
    
    if args.watch:
        print("[WATCH] 監視モード開始...", flush=True)
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
            except Exception as e: 
                print(f"Error in main loop: {e}", flush=True)
                time.sleep(10)
    else:
        run_once(local_only=args.local_only, force_full=args.consolidate, skip_scan=args.resume)

if __name__ == "__main__":
    main()
