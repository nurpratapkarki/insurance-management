#!/bin/bash

# Navigate to project directory
cd /home/nurpratapkarki/Office/Backend/insurance-management

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Log file location
log_file="logs/premium_system_update.log"
mkdir -p logs

# Current timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")

# Start logging
echo "====== Premium System Update: $timestamp ======" >> $log_file

# Update fine calculations
echo "Updating premium fines..." >> $log_file
python manage.py update_premium_fines >> $log_file 2>&1

# Check for policy expiry
echo "Checking for policy expiry..." >> $log_file
python manage.py check_policy_expiry >> $log_file 2>&1

# Update policy bonuses on anniversaries
echo "Updating policy bonuses..." >> $log_file
python manage.py update_bonuses >> $log_file 2>&1

# Complete
echo "Update completed successfully." >> $log_file
echo "=============================================" >> $log_file
echo "" >> $log_file 