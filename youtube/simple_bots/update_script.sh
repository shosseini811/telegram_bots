#!/bin/bash

# Activate virtual environment (if you have one)
# source /path/to/your/env/bin/activate

# Install new requirements
pip install -r ~/requirements.txt

# Kill the currently running script
pkill -f youtubedl_bot.py

# Start the updated script
nohup python ~/youtubedl_bot.py &

# Note: The 'nohup' command lets you run the script in the background and it will keep running even after you've closed the SSH connection.
