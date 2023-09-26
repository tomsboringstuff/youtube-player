#!/bin/bash

# Function to check if a command is available
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python; then
  echo "Python is not installed. Installing Python..."
  # You can modify this part based on your system's package manager
  # For example, on Debian-based systems (e.g., Ubuntu):
  sudo apt-get update
  sudo apt-get install -y python
fi

# Check if pip is installed
if ! command_exists pip; then
  echo "pip is not installed. Installing pip..."
  # Install pip using the get-pip.py script
  curl -sSL https://bootstrap.pypa.io/get-pip.py | sudo python
fi

# Install Python dependencies using pip
pip install pyautogui selenium screeninfo pynput

# Check if yt-dlp is installed, and if not, install it
if ! command_exists yt-dlp; then
    echo "yt-dlp is not installed. Installing yt-dlp..."
    pip install yt-dlp
fi

echo "Python, pip, and Python dependencies have been installed."
