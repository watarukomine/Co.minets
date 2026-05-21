@echo off
chcp 65001 > nul
echo 🚀 異常値分析ダッシュボードを起動しています...

:: サーバーと監視スクリプトを別ウィンドウで起動
start "📊 ダッシュボード・サーバー" python -m http.server 8000
start "👀 データ監視（Watch Mode）" python process_data.py --watch

echo.
echo ✨ 以下のURLをブラウザで開いてください：
echo http://localhost:8000/異常値分析ダッシュボード.html
echo.
echo 💡 使い方：
echo ・downloads フォルダに新しいCSVを入れると、自動でデータが更新されます。
echo ・データ更新後は、ブラウザをリロード（F5）してください。
echo.
pause
