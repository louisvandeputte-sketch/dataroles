#!/bin/bash
# Setup launchd (macOS native scheduler) for company enrichment every 10 hours

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_FILE="$HOME/Library/LaunchAgents/com.datarole.company-enrichment.plist"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.datarole.company-enrichment</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/scripts/run_company_enrichment.sh</string>
    </array>
    
    <key>StartInterval</key>
    <integer>36000</integer>  <!-- 10 hours in seconds -->
    
    <key>RunAtLoad</key>
    <true/>  <!-- Run immediately when loaded -->
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/company_enrichment_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/company_enrichment_stderr.log</string>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent plist created at: $PLIST_FILE"
echo ""
echo "Loading the LaunchAgent..."

# Unload if already loaded (ignore errors)
launchctl unload "$PLIST_FILE" 2>/dev/null

# Load the LaunchAgent
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ LaunchAgent loaded successfully!"
    echo ""
    echo "The company enrichment will now run:"
    echo "  - Immediately (on first load)"
    echo "  - Every 10 hours after that"
    echo ""
    echo "To check status:"
    echo "  launchctl list | grep datarole"
    echo ""
    echo "To stop the scheduler:"
    echo "  launchctl unload $PLIST_FILE"
    echo ""
    echo "To restart the scheduler:"
    echo "  launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
    echo ""
    echo "Logs are saved to:"
    echo "  $PROJECT_DIR/logs/company_enrichment_*.log"
else
    echo "❌ Failed to load LaunchAgent"
    echo "You may need to grant Terminal 'Full Disk Access' in System Preferences > Security & Privacy"
fi
