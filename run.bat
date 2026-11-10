@echo off
rem Windows launcher for scrape_course.py (counterpart of run.sh).
rem
rem   run.bat setup                             install dependencies and browser (run once)
rem   run.bat login   "<course url>"            sign in once (opens a browser)
rem   run.bat preview "<course url>" [options]  list what would be saved (dry run)
rem   run.bat scrape  "<course url>" [options]  download transcripts to .\output
rem
rem [options] are passed through to scrape_course.py, e.g. --only-module 2 --out C:\transcripts
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=.venv"
set "MARKER=%VENV%\.deps_installed"

set "CMD=%~1"
if "%CMD%"=="" goto usage
if /i "%CMD%"=="-h" goto usage
if /i "%CMD%"=="--help" goto usage
if /i "%CMD%"=="help" goto usage
if /i "%CMD%"=="setup" goto setup
if /i "%CMD%"=="login" goto args
if /i "%CMD%"=="preview" goto args
if /i "%CMD%"=="scrape" goto args
echo Unknown command: %CMD% 1>&2
goto usage_err

:args
set "URL=%~2"
if "%URL%"=="" (
    echo Missing course URL. 1>&2
    goto usage_err
)
if /i not "%URL:~0,27%"=="https://mylearn.oracle.com/" (
    echo URL must start with https://mylearn.oracle.com/ 1>&2
    exit /b 1
)

rem Collect any extra options (everything after the URL).
shift
shift
set "REST="
:restloop
if "%~1"=="" goto restdone
set "REST=%REST% %1"
shift
goto restloop
:restdone

call :env_ok
if errorlevel 1 (
    echo The environment is not set up yet. Run: run.bat setup 1>&2
    exit /b 1
)

if /i "%CMD%"=="login"   "%VENV%\Scripts\python.exe" scrape_course.py --login "%URL%" %REST%
if /i "%CMD%"=="preview" "%VENV%\Scripts\python.exe" scrape_course.py --dry-run "%URL%" %REST%
if /i "%CMD%"=="scrape"  "%VENV%\Scripts\python.exe" scrape_course.py "%URL%" %REST%
exit /b %errorlevel%

:setup
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo Python 3 is required but was not found. Install it from https://www.python.org/downloads/ 1>&2
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV% ...
    %PY% -m venv "%VENV%"
    if errorlevel 1 exit /b 1
)

call :env_ok
if not errorlevel 1 (
    echo Environment is already set up.
    exit /b 0
)

echo Installing dependencies ...
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
if errorlevel 1 exit /b 1
"%VENV%\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 exit /b 1
echo Installing browser (Chromium) ...
"%VENV%\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 exit /b 1
echo done> "%MARKER%"
echo Setup complete.
exit /b 0

:env_ok
rem Exit code 0 if setup has run and requirements.txt has not changed since.
if not exist "%MARKER%" exit /b 1
powershell -NoProfile -Command "if ((Get-Item 'requirements.txt').LastWriteTime -gt (Get-Item '%MARKER%').LastWriteTime) { exit 1 } else { exit 0 }"
exit /b %errorlevel%

:usage
call :print_usage
exit /b 0

:usage_err
call :print_usage 1>&2
exit /b 1

:print_usage
echo Launcher for scrape_course.py.
echo.
echo   run.bat setup                             install dependencies and browser (run once)
echo   run.bat login   "^<course url^>"            sign in once (opens a browser)
echo   run.bat preview "^<course url^>" [options]  list what would be saved (dry run)
echo   run.bat scrape  "^<course url^>" [options]  download transcripts to .\output
echo.
echo [options] are passed through to scrape_course.py, e.g. --only-module 2 --out C:\transcripts
exit /b 0
