import os
import glob
import csv

PROJECT_ROOT = r"X:\全社共有\371神奈川\営業企画部\01_営業総括室\01_総括G\18_DX\Antigravity\異常値Search 実績分析UI"
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")

def verify():
    print("🧪 データの整合性チェックを開始します...")
    
    # 1. ファイル数の確認
    files = glob.glob(os.path.join(DOWNLOAD_DIR, "【*】*.csv"))
    print(f"📁 見つかったCSVファイル数: {len(files)} / 266")
    
    if len(files) != 266:
        print("⚠️ 警告: ファイル数が266件ではありません。")

    # 2. ブランチ名の不一致チェック
    all_branch_sets = {}
    empty_files = []
    
    for f in files:
        f_name = os.path.basename(f)
        branches = set()
        has_data = False
        try:
            with open(f, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    b = row.get('支社', row.get('管轄支社名', '')).strip()
                    if b:
                        branches.add(b)
                        has_data = True
            
            if not has_data:
                empty_files.append(f_name)
            
            all_branch_sets[f_name] = branches
        except Exception as e:
            print(f"❌ {f_name} の読み込みエラー: {e}")

    if empty_files:
        print(f"⚠️ 警告: 以下のファイルにデータが含まれていません: {empty_files}")
    else:
        print("✅ 全ファイルにデータ行が存在することを確認しました。")

    # 3. 支社名の整合性
    first_file = list(all_branch_sets.keys())[0]
    expected_branches = all_branch_sets[first_file]
    mismatch_count = 0
    for f_name, branches in all_branch_sets.items():
        if branches != expected_branches:
            # 軽微な差（支社が増減しているなど）がないか確認
            diff = branches.symmetric_difference(expected_branches)
            if diff:
                print(f"❓ {f_name} の支社リストに差異があります: {diff}")
                mismatch_count += 1
    
    if mismatch_count == 0:
        print(f"✅ 全ファイルで支社リストが一致しています ({len(expected_branches)} 支社)。")
    else:
        print(f"⚠️ {mismatch_count} 件のファイルで支社リストに差異があります。")

    print("\n✨ チェック完了")

if __name__ == "__main__":
    verify()
