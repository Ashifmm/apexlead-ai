#!/usr/bin/env bash
# Exit immediately on error
set -o errexit

echo "========================================="
echo "  ApexLead AI Root Render Build Script"
echo "========================================="

if [ -d "backend" ]; then
    cd backend
fi

# 1. Upgrade pip and install Python dependencies
echo "--> Step 1: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Install Playwright Chromium browser
echo "--> Step 2: Installing Playwright Chromium browser..."
playwright install chromium

# 3. Attempt to install Linux system dependencies for Chromium
echo "--> Step 3: Installing Playwright system dependencies..."
if command -v playwright &> /dev/null; then
    playwright install-deps chromium || echo "Notice: System package installation skipped or not permitted; headless fallback mode active."
fi

# 4. Ensure demo directory exists
mkdir -p static/demos

echo "========================================="
echo "  ApexLead AI Build Complete"
echo "========================================="
