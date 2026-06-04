@echo off
set "CHROME_PATH_1=C:\Program Files\Google\Chrome\Application\chrome.exe"
set "CHROME_PATH_2=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
set "CHROME_PATH_3=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

set "USER_DATA=%LOCALAPPDATA%\chrome_profile_rpa"
set "URL=https://report.tmp-one.com/portal#"

if exist "%CHROME_PATH_1%" (
    set "EXE=%CHROME_PATH_1%"
) else if exist "%CHROME_PATH_2%" (
    set "EXE=%CHROME_PATH_2%"
) else if exist "%CHROME_PATH_3%" (
    set "EXE=%CHROME_PATH_3%"
) else (
    echo [WARNING] Chrome path not found. Trying 'start chrome' directly...
    start chrome --remote-debugging-port=9222 --user-data-dir="%USER_DATA%" --no-first-run --no-default-browser-check "%URL%"
    exit
)

start "" "%EXE%" --remote-debugging-port=9222 --user-data-dir="%USER_DATA%" --no-first-run --no-default-browser-check "%URL%"
exit
