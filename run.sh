#!/data/data/com.termux/files/usr/bin/env bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting 36MProxys Setup for Termux...${NC}"

# --- Step 1: Update Termux and install system dependencies ---
echo -e "\n${YELLOW}[INFO] Updating packages and installing system dependencies...${NC}"
pkg update -y && pkg upgrade -y
pkg install -y python libcurl openssl-dev build-essential

# Check if pkg install was successful
if [ $? -ne 0 ]; then
    echo -e "\n${RED}[ERROR] Failed to install system dependencies. Please check your internet connection and try again.${NC}"
    exit 1
fi

# --- Step 2: Install Python dependencies using pip ---
echo -e "\n${YELLOW}[INFO] Installing Python libraries (requests, colorama, pycurl)...${NC}"
pip install --upgrade pip
pip install --upgrade requests colorama certifi pycurl

# Check if pip install was successful
if [ $? -ne 0 ]; then
    echo -e "\n${RED}[ERROR] Failed to install Python libraries. Please check the error messages above.${NC}"
    exit 1
fi

# --- Step 3: Run the main script ---
PYTHON_SCRIPT="36m-proxys.py"

if [ -f "$PYTHON_SCRIPT" ]; then
    echo -e "\n${GREEN}[SUCCESS] Setup complete. Launching 36MProxys...${NC}"
    sleep 2
    # Run the python script
    python "$PYTHON_SCRIPT"
else
    echo -e "\n${RED}[ERROR] Main script '$PYTHON_SCRIPT' not found.${NC}"
    echo -e "${YELLOW}[INFO] Please save the Python code as '36m-proxys.py' in the same folder as this script.${NC}"
    exit 1
fi

echo -e "\n${GREEN}36MProxys has finished. Thank you for using!${NC}"
