@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PY_CMD="
set "VENV_PATHS=.venv venv env .env"
for %%V in (%VENV_PATHS%) do (
    set "VENV_PY=%~dp0%%V\Scripts\python.exe"
    if exist "!VENV_PY!" (
        set "PY_CMD=!VENV_PY!"
        goto :FOUND_PY
    )
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY_CMD=py -3"
    )
)
:FOUND_PY
if "%PY_CMD%"=="" (
    echo Error: No Python found in PATH or any virtual environment. Please install Python or add it to PATH.
    exit /b 1
)

set "LOGFILE=run.log"
chcp 65001 >nul
powershell -NoProfile -Command "Set-Content -Path '%LOGFILE%' -Value [char]0xFEFF -Encoding UTF8" >nul 2>&1
set "PYTHONUTF8=1"
echo === Starting main.py at %DATE% %TIME% ===> "%LOGFILE%"
echo === Starting main.py at %DATE% %TIME% ===> "%LOGFILE%" >> "%LOGFILE%"

set "SCRIPT="
if exist "%~dp0main.py" (
    set "SCRIPT=%~dp0main.py"
) else (
    if exist "%~dp0main\main.py" (
        set "SCRIPT=%~dp0main\main.py"
    )
)

if "%SCRIPT%"=="" (
    echo Error: Could not find main.py in repository root or in the subfolder "main".>&2
    echo Searched: "%~dp0main.py" and "%~dp0main\main.py".>&2
    exit /b 2
)

echo Command: "%PY_CMD%" "%SCRIPT%" >> "%LOGFILE%"

start "Eagle_AItagger" /wait cmd /c "chcp 65001>nul & call "%PY_CMD%" "%SCRIPT%" || (echo. & echo 程序运行出错，退出代码 !ERRORLEVEL! & echo 按任意键关闭此窗口... & pause >nul)"

set "EXITCODE=%ERRORLEVEL%"

if %EXITCODE%==0 (
    echo main.py exited with code 0. See "%LOGFILE%" for details.
    exit /b 0
) else (
    echo ERROR: main.py failed (exit code %EXITCODE%). See "%LOGFILE%" for details.
    exit /b %EXITCODE%
)