#!/bin/bash
# Exit on error
set -e

echo "Setting up Python virtual environment..."
# Check if python3-venv is installed, which is sometimes required on Linux Mint/Ubuntu
if ! dpkg -l | grep -q python3-venv; then
    echo "python3-venv is not installed. Trying to install it with sudo apt update && sudo apt install python3-venv"
    sudo apt update && sudo apt install -y python3-venv
fi

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "Building executable with PyInstaller..."
# We use the existing ManuscriptMatch.spec which has been made cross-platform
pyinstaller ManuscriptMatch.spec --noconfirm

echo ""
echo "=========================================================="
echo "Build complete! "
echo "You can find your executable in: dist/ManuscriptMatch/"
echo "Run it using: ./dist/ManuscriptMatch/ManuscriptMatch"
echo "=========================================================="
