#!/bin/bash
#
# ONE-TIME SCHEDULER STARTUP SCRIPT
# ==================================
# 
# This script starts the one-time size_category inference scheduler.
# The scheduler will run the inference script tomorrow at 11:00 AM.
#
# ⚠️  IMPORTANT: This is a ONE-TIME scheduler!
# ⚠️  After successful execution, REMOVE this file and the scheduler!
#
# Usage:
#   ./start_one_time_scheduler.sh
#
# Or run in background:
#   nohup ./start_one_time_scheduler.sh > logs/scheduler_startup.log 2>&1 &
#

cd /Users/louisvandeputte/datarole

# Activate virtual environment if needed
# source venv/bin/activate  # Uncomment if using venv

# Start the scheduler in the background
echo "Starting one-time size_category scheduler..."
echo "Scheduled to run at: 11:00 AM tomorrow (2025-12-18)"
echo "Log file: logs/one_time_size_category_scheduler.log"

nohup python3 one_time_size_category_scheduler.py > logs/scheduler_startup.log 2>&1 &

echo "Scheduler started with PID: $!"
echo "To check status: tail -f logs/one_time_size_category_scheduler.log"
echo "To stop: kill $!"
echo ""
echo "⚠️  REMINDER: This is a ONE-TIME scheduler."
echo "⚠️  After successful run, remove these files:"
echo "    - one_time_size_category_scheduler.py"
echo "    - start_one_time_scheduler.sh"
