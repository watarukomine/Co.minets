@echo off
set "EDGE_PATH_1=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "EDGE_PATH_2=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
set "USER_DATA=%~dp0edge_profile_rpa"
set "URL=https://report.tmp-one.com/portal#"

if exist "%EDGE_PATH_1%" (
    set "EXE=%EDGE_PATH_1%"
) else if exist "%EDGE_PATH_2%" (
    set "EXE=%EDGE_PATH_2%"
) else (
    echo [WARNING] Edge path not found. Trying 'start msedge' directly...
    start msedge --remote-debugging-port=9222 --user-data-dir="%USER_DATA%" --no-first-run --no-default-browser-check "%URL%"
    exit
)

start "" "%EXE%" --remote-debugging-port=9222 --user-data-dir="%USER_DATA%" --no-first-run --no-default-browser-check "%URL%"
exit
