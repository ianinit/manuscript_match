#!/bin/bash
# Exit on error
set -e

echo "Setting up Python virtual environment..."
# Check if python-venv and python3-tk are installed, which are often required on Linux Mint/Ubuntu
if ! dpkg -l | grep -q python3-venv || ! dpkg -l | grep -q python3-tk; then
    echo "Required system packages (python3-venv, python3-tk) are missing. Attempting to install them with apt..."
    sudo apt update && sudo apt install -y python3-venv python3-tk
fi

# Create and activate virtual environment
python3 -m venv .venv_linux
source .venv_linux/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "Building executable with PyInstaller..."
# Clear old build directories to force PyInstaller to detect tkinter
rm -rf build/ dist/

# We use the existing ManuscriptMatch.spec which has been made cross-platform
pyinstaller ManuscriptMatch.spec --noconfirm --clean

echo ""
echo "=========================================================="
echo "Build complete! "
echo "You can find your executable in: dist/ManuscriptMatch/"
echo "Run it using: ./dist/ManuscriptMatch/ManuscriptMatch"
echo "=========================================================="
