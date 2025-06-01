@echo off
setlocal

echo.
echo [1/4] Installing pipreqs if not present...

:: Ensure pipreqs is installed
pip show pipreqs >nul 2>&1 || pip install pipreqs

echo.
echo [2/4] Generating requirements.txt ...

pipreqs . --force --encoding=utf-8

:: Append pipreqs and pyinstaller if not already present
findstr /i "pipreqs" requirements.txt >nul || echo pipreqs>>requirements.txt
findstr /i "pyinstaller" requirements.txt >nul || echo pyinstaller>>requirements.txt

echo requirements.txt updated with development tools.

echo.
echo [3/4] Packaging main.py with PyInstaller ...

:: Optional: specify icon (.ico file)
:: set ICON=--icon=app.ico
set ICON=

:: Package using PyInstaller
pyinstaller --noconfirm --onefile --windowed %ICON% main.py

echo.
if exist dist\main.exe (
    echo [4/4] Build complete! Executable is located at dist\main.exe
) else (
    echo Build failed. Check if main.py exists and PyInstaller is installed.
)

pause
endlocal
