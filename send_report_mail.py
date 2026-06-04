# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

# ==========================================
# 設定：デフォルトの送信先メールアドレス
# ==========================================
# ※ご自身のメールアドレスに書き換えてください。
DEFAULT_TO_EMAIL = "komine-wata@toyota-mp.co.jp"

def get_report_data():
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extraction_report.json")
    if not os.path.exists(report_path):
        return None
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[エラー] レポートファイルの読み込みに失敗しました: {e}")
        return None

def build_mail_content(report):
    target_year = report.get("target_year", datetime.now().year)
    target_month = report.get("target_month", datetime.now().month)
    total = report.get("total_expected", 2700)
    success = report.get("success_count", 0)
    skip = report.get("skip_count", 0)
    fail = report.get("fail_count", 0)
    failed_patterns = report.get("failed_patterns", [])

    subject = f"【RPA月次報告】実績データ抽出結果 (対象年月: {target_year}/{target_month:02d})"
    
    # 成功率計算
    newly_extracted = max(0, success - skip)
    processed_ok = success
    success_rate = (processed_ok / total) * 100 if total > 0 else 0

    body = f"""<html>
<body style="font-family: 'Meiryo', sans-serif; color: #333; line-height: 1.6;">
    <h2 style="color: #1A365D; border-bottom: 2px solid #2B6CB0; padding-bottom: 8px;">【Cominets】月次実績データ抽出結果レポート</h2>
    
    <p>RPAによる月次実績データの自動抽出処理が完了いたしました。<br>
    処理結果のサマリーは以下の通りです。</p>

    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin-top: 15px; margin-bottom: 15px;">
        <tr style="background-color: #E2E8F0;">
            <th style="border: 1px solid #CBD5E0; padding: 10px; text-align: left; width: 150px;">項目</th>
            <th style="border: 1px solid #CBD5E0; padding: 10px; text-align: left;">件数 / ステータス</th>
        </tr>
        <tr>
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold;">対象年月</td>
            <td style="border: 1px solid #CBD5E0; padding: 10px;">{target_year}年{target_month:02d}月度</td>
        </tr>
        <tr>
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold;">総パターン数</td>
            <td style="border: 1px solid #CBD5E0; padding: 10px;">{total} 件</td>
        </tr>
        <tr>
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold; color: #2F855A;">抽出・マージ完了</td>
            <td style="border: 1px solid #CBD5E0; padding: 10px; color: #2F855A; font-weight: bold;">{processed_ok} 件 (新規抽出: {newly_extracted}件 / スキップ: {skip}件)</td>
        </tr>
        <tr style="{'background-color: #FFF5F5;' if fail > 0 else ''}">
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold; color: {'#C53030' if fail > 0 else '#333'};">失敗・欠落</td>
            <td style="border: 1px solid #CBD5E0; padding: 10px; color: {'#C53030' if fail > 0 else '#333'}; font-weight: bold;">{fail} 件</td>
        </tr>
        <tr>
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold;">完了率</td>
            <td style="border: 1px solid #CBD5E0; padding: 10px; font-weight: bold;">{success_rate:.1f} %</td>
        </tr>
    </table>
"""

    if fail > 0:
        body += f"""
    <div style="background-color: #FFF5F5; border-left: 4px solid #C53030; padding: 15px; margin-top: 20px; border-radius: 4px; max-width: 750px;">
        <h3 style="margin-top: 0; color: #9B2C2C;">⚠️ 未処理・抽出失敗データがあります ({fail}件)</h3>
        <p style="margin-bottom: 10px;">一部のデータ抽出において、画面の読み込みタイムアウトや要素の操作に失敗しました。<br>
        <strong>リカバリ（不足分だけの追加抽出）</strong>を行う必要があります。</p>
        
        <h4 style="margin-bottom: 5px; color: #2D3748;">■ 失敗パターン詳細 (最初の15件を表示):</h4>
        <ul style="margin-top: 5px; padding-left: 20px; font-size: 14px;">
"""
        # 最初の15件のみリスト
        for item in failed_patterns[:15]:
            pat = item.get("pattern", "不明")
            reason = item.get("reason", "不明なエラー")
            body += f"            <li style='margin-bottom: 5px;'><strong>{pat}</strong><br><span style='color: #718096;'>エラー理由: {reason}</span></li>\n"
        
        if len(failed_patterns) > 15:
            body += f"            <li style='color: #718096;'>...他 {len(failed_patterns) - 15} 件の失敗パターンがあります</li>\n"

        body += """        </ul>
        
        <h4 style="margin-bottom: 5px; color: #2D3748; margin-top: 15px;">■ リカバリ（再実行）の手順:</h4>
        <p style="margin-top: 5px; font-size: 14px; background-color: #FFF; padding: 10px; border: 1px solid #E2E8F0; border-radius: 4px;">
            1. ご自身のPCで、共有フォルダにあるバッチファイル <strong>[run_monthly_update.bat]</strong> をダブルクリックして実行します。<br>
            2. カウントダウンが表示されるので、そのまま待機（または N キーを入力）して自動運転モードで進めます。<br>
            3. 既に完了した件数は自動的にスキップされ、<strong>失敗していた {fail} 件だけが自動的に追加抽出・マージ</strong>され、Firestoreに登録されます。<br>
            ※完了後、再度この報告メールが送信されます。
        </p>
    </div>
"""
    else:
        body += """
    <div style="background-color: #F0FFF4; border-left: 4px solid #38A169; padding: 15px; margin-top: 20px; border-radius: 4px; max-width: 600px;">
        <h3 style="margin-top: 0; color: #276749;">🎉 すべてのデータ抽出が正常に完了しました！</h3>
        <p style="margin-bottom: 0;">2,700パターンの抽出・マージおよびデータベース (Firestore) への同期がすべて完了いたしました。<br>
        追加の手動操作やリカバリ実行は不要です。</p>
    </div>
"""

    body += """
    <br>
    <hr style="border: 0; border-top: 1px solid #E2E8F0; max-width: 600px; margin-left: 0;">
    <p style="font-size: 12px; color: #A0AEC0;">※このメールはRPA実績分析抽出システムから自動送信されています。</p>
</body>
</html>
"""
    return subject, body

def send_outlook_mail(to_email, subject, body_html):
    try:
        import win32com.client as win32
        
        # win32comの初期化
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = to_email
        mail.Subject = subject
        mail.HTMLBody = body_html
        mail.Send()
        print(f"  [成功] Outlook経由で報告メールを送信しました。 (宛先: {to_email})")
        return True
    except Exception as e:
        print(f"[エラー] Outlookとの連携に失敗しました: {e}")
        print("※ win32com ライブラリがインストールされているか、Outlookが利用可能か確認してください。")
        return False

def main():
    print("【抽出結果報告メール送信システム】")
    
    report = get_report_data()
    if not report:
        print("[警告] 送信対象の抽出レポート (extraction_report.json) が存在しないため、送信をスキップします。")
        return

    # コマンドライン引数から宛先が指定されていればそれを使用
    to_email = DEFAULT_TO_EMAIL
    if len(sys.argv) > 1 and "@" in sys.argv[1]:
        to_email = sys.argv[1]

    subject, body_html = build_mail_content(report)
    
    print(f"  メール送信を開始します... (宛先: {to_email})")
    send_outlook_mail(to_email, subject, body_html)

if __name__ == "__main__":
    main()
