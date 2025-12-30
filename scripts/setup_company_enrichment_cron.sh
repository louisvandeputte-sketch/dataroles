#!/bin/bash
# Setup cron job for automatic company enrichment every 10 hours

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/auto_enrich_companies.py"
LOG_DIR="$PROJECT_DIR/logs"
VENV_PATH="$PROJECT_DIR/venv"  # Adjust if your venv is elsewhere

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create a wrapper script that sets up the environment
WRAPPER_SCRIPT="$PROJECT_DIR/scripts/run_company_enrichment.sh"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Wrapper script for company enrichment cron job

# Set working directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"

# Load environment variables if .env exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export \$(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Run the enrichment script
python3 "$SCRIPT_PATH" --batch-size 50 --max-total 200 >> "$LOG_DIR/company_enrichment_\$(date +\%Y\%m\%d_\%H\%M\%S).log" 2>&1

# Keep only last 30 days of logs
find "$LOG_DIR" -name "company_enrichment_*.log" -mtime +30 -delete
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "✅ Wrapper script created at: $WRAPPER_SCRIPT"
echo ""
echo "To set up the cron job, run:"
echo ""
echo "  crontab -e"
echo ""
echo "Then add this line (runs every 10 hours at :00):"
echo ""
echo "  0 */10 * * * $WRAPPER_SCRIPT"
echo ""
echo "Or use this alternative (runs at 00:00, 10:00, 20:00 daily):"
echo ""
echo "  0 0,10,20 * * * $WRAPPER_SCRIPT"
echo ""
echo "To verify the cron job is set up:"
echo ""
echo "  crontab -l"
echo ""
echo "Logs will be saved to: $LOG_DIR/company_enrichment_*.log"
echo ""
echo "To test the script manually:"
echo ""
echo "  $WRAPPER_SCRIPT"
