#!/bin/bash

# If requirements.txt changed, then install new requirements
if [ "$REQ_CHANGED" -eq "1" ]; then
    pip install -r ~/requirements.txt
fi

# Kill the currently running script
pkill -f youtubedl_bot.py

# Start the updated script
nohup python3 ~/youtubedl_bot.py > /dev/null 2>&1 < /dev/null &

# Exit gracefully
exit 0
