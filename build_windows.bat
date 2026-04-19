@echo off
setlocal enabledelayedexpansion

echo Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

:: Activate the virtual environment
call .venv\Scripts\activate.bat

echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Building executable with PyInstaller...
:: Clear old build directories to ensure a clean build
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

:: We use the existing ManuscriptMatch.spec
pyinstaller ManuscriptMatch.spec --noconfirm --clean

echo.
echo ==========================================================
echo Build complete! 
echo You can find your executable in: dist\ManuscriptMatch\
echo Run it using: .\dist\ManuscriptMatch\ManuscriptMatch.exe
echo ==========================================================
