@echo off
setlocal
set SCRIPT_DIR=%~dp0

if "%1"=="" (
  echo Usage:
  echo   run_refrepos_sync.bat sync [--dry-run] [--keep-old] [--json-out path]
  echo   run_refrepos_sync.bat inspect [--include-readme] [--extract-fallback] [--json-out path]
  echo   run_refrepos_sync.bat discover [--queries "..."] [--json-out path]
  echo.
  echo Example:
  echo   run_refrepos_sync.bat sync --dry-run
  exit /b 0
)

python "%SCRIPT_DIR%refrepos_sync.py" %*
set ERR=%ERRORLEVEL%

if not "%ERR%"=="0" (
  echo.
  echo Command failed with exit code %ERR%.
)

exit /b %ERR%

