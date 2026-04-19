$ErrorActionPreference = "Stop"

Write-Host "Setting up Python virtual environment..."
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
}

# Activate the virtual environment
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Write-Host "Building executable with PyInstaller..."
# Clear old build directories to ensure a clean build
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }

# We use the existing ManuscriptMatch.spec
pyinstaller ManuscriptMatch.spec --noconfirm --clean

Write-Host ""
Write-Host "=========================================================="
Write-Host "Build complete! "
Write-Host "You can find your executable in: dist\ManuscriptMatch\"
Write-Host "Run it using: .\dist\ManuscriptMatch\ManuscriptMatch.exe"
Write-Host "=========================================================="
