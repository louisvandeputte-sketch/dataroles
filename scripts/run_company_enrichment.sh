#!/bin/bash
# Wrapper script for company enrichment cron job

# Set working directory
cd "/Users/louisvandeputte/datarole"

# Activate virtual environment if it exists
if [ -d "/Users/louisvandeputte/datarole/venv" ]; then
    source "/Users/louisvandeputte/datarole/venv/bin/activate"
fi

# Set PYTHONPATH
export PYTHONPATH="/Users/louisvandeputte/datarole:$PYTHONPATH"

# Load environment variables if .env exists
if [ -f "/Users/louisvandeputte/datarole/.env" ]; then
    export $(cat "/Users/louisvandeputte/datarole/.env" | grep -v '^#' | xargs)
fi

# Run the enrichment script
python3 "/Users/louisvandeputte/datarole/scripts/auto_enrich_companies.py" --batch-size 50 --max-total 200 >> "/Users/louisvandeputte/datarole/logs/company_enrichment_$(date +\%Y\%m\%d_\%H\%M\%S).log" 2>&1

# Keep only last 30 days of logs
find "/Users/louisvandeputte/datarole/logs" -name "company_enrichment_*.log" -mtime +30 -delete
