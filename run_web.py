#!/usr/bin/env python3
"""Run the DataRoles web application locally (monitoring only, no scraping)."""

import os
import uvicorn

# Disable background services for local development
# This prevents scheduler and auto-enrich from running locally
# Railway will handle all scraping and enrichment
os.environ["DISABLE_BACKGROUND_SERVICES"] = "true"

if __name__ == "__main__":
    print("🖥️  Starting LOCAL web interface (monitoring only)")
    print("⏸️  Scheduler and auto-enrich DISABLED")
    print("🌐 Railway handles all scraping and enrichment")
    print("📊 You can monitor runs at: http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        timeout_keep_alive=300  # 5 minutes keep-alive timeout for long-running requests
    )

