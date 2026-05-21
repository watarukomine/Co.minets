import os
import glob
import pandas as pd
import logging
import warnings

# Excel読み込み時の警告を非表示にする
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MASTER_DIR = "master_data"
UPLOAD_DIR = "excel_uploads"

def ensure_directories():
    for d in [MASTER_DIR, UPLOAD_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

def load_master_data():
    """マスタ表を読み込みます"""
    # ユーザーの画像にあったファイル名
    # ※一部の文字揺れを考慮し、ワイルドカードで検索
    search_pattern = os.path.join(MASTER_DIR, "*サマリーコード_ツリーコード_加減算フラグ*.xlsx")
    master_files = glob.glob(search_pattern)
    
    if master_files:
        master_file = master_files[0]
        logging.info(f"マスタ表を発見: {os.path.basename(master_file)}")
        
        # マスタを読み込み。ヘッダーは1行目
        df_master = pd.read_excel(master_file)
        
        # 後で照合しやすいように「販売ツリーコード」を全て半角文字列に統一
        if '販売ツリーコード' in df_master.columns:
            df_master['販売ツリーコード'] = df_master['販売ツリーコード'].astype(str).str.strip()
            return df_master
        else:
            logging.error("マスタ表に「販売ツリーコード」列がありません。")
            return None
    else:
        logging.warning("マスタファイルが見つかりません。処理は続行しますが、ツリーコードの紐付けは行われません。")
        return None

def process_uploaded_excel(file_path, df_master):
    logging.info(f"データ変換を開始: {os.path.basename(file_path)}")
    
    try:
        # Excelデータの読み込み
        # - .xls形式のため、エンジンに xlrd または openpyxl を自動で使用
        # - 見出しは2行目（画像を見ると1行目に「1, 2, 3...」とカウントがあるので header=1）
        # - まずは代表として「当日_売上金額」シートを対象
        df = pd.read_excel(file_path, header=1, sheet_name='当日_売上金額')
        
        # 見出しに改行やスペースが混ざっていることが多いので、すべて綺麗に除去する
        df.columns = df.columns.astype(str).str.replace(r'\s+', '', regex=True)
    except Exception as e:
        logging.error(f"ファイル読み込みエラー: {e} (xlrdパッケージがインストールされていない可能性があります)")
        return
        
    # --- 横持ちから縦持ちへの変換（アンピボット） ---
    # 人間の目には見えない文字が邪魔をして「お客様名」が見つからないのを防ぐため、
    # 確実に「ツリーコード（すべて数字の列名: 1421000 等）」が始まる場所を境界線として自動探知します
    split_index = None
    for i, col in enumerate(df.columns):
        if col.isdigit():
            split_index = i
            break
            
    if split_index is None:
        logging.error(f"境界線エラー: 数字のみの列（ツリーコード）が見つかりません。現在の見出し一覧: {df.columns.tolist()}")
        return
    
    # 属性列（IDとして残す列：左側すべて）
    id_vars = df.columns[:split_index].tolist()
    # 金額として縦一列に並べる列（ツリーコード列：右側すべて）
    val_vars = df.columns[split_index:].tolist()
    
    logging.info(f"アンピボット実行中... ツリーコードの列数: {len(val_vars)}列")
    df_melted = pd.melt(df, id_vars=id_vars, value_vars=val_vars, var_name='販売ツリーコード', value_name='売上金額')
    
    # 無駄なデータ（金額がゼロのもの）を削除して軽量化
    df_melted = df_melted.dropna(subset=['売上金額'])
    df_melted = df_melted[df_melted['売上金額'] != 0]

    # ツリーコードを文字列としてフォーマット統一
    df_melted['販売ツリーコード'] = df_melted['販売ツリーコード'].astype(str).str.strip()
    
    # --- マスタと結合（VLOOKUP相当） ---
    if df_master is not None:
        logging.info("マスタデータと結合処理中...")
        # 左外部結合（LEFT JOIN）でツリーコードをベースにくっつける
        df_clean = pd.merge(df_melted, df_master, on='販売ツリーコード', how='left')
        matched_count = df_clean['共販サマリーコード'].notna().sum()
        logging.info(f"マスタとの照合成功数: {matched_count} 件 / 全 {len(df_clean)} 件中")
    else:
        df_clean = df_melted
        
    # CSVとして保存
    output_filename = os.path.basename(file_path).replace('.xls', '.csv').replace('.xlsx', '.csv')
    output_path = os.path.join(UPLOAD_DIR, "クレンジング済_" + output_filename)
    
    # 日本語エクセルなのでBOM付きUTF-8で保存
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
    logging.info(f"CSV保存完了: {output_path} (最終行数: {len(df_clean)})")
    
    # --- ダッシュボード連携用 (JavaScript変数としての出力) ---
    js_output_path = os.path.join(UPLOAD_DIR, "dashboard_data.js")
    json_data = df_clean.to_json(orient="records", force_ascii=False)
    with open(js_output_path, 'w', encoding='utf-8-sig') as f:
        f.write(f"const EXCEL_DATA = {json_data};")
    logging.info(f"ダッシュボード用JS保存完了: {js_output_path}")
    
    print("-" * 50)

if __name__ == "__main__":
    print("=== Excelデータ自動クレンジング（アンピボット＆マスタ結合） ===")
    ensure_directories()
    
    # 1. マスタ読み込み
    master_data = load_master_data()
    
    # 2. 対象データ処理
    # xls も xlsx も両方対象にする
    target_files = glob.glob(os.path.join(UPLOAD_DIR, "*.xls*"))
    
    if not target_files:
        print("処理対象のExcelファイルが excel_uploads/ にありません。")
    else:
        for file in target_files:
            if not os.path.basename(file).startswith("~") and "クレンジング済" not in file:
                process_uploaded_excel(file, master_data)
                
    print("全処理が完了しました。")
