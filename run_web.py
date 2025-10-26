#!/usr/bin/env python3
"""Run the DataRoles web application."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        timeout_keep_alive=300  # 5 minutes keep-alive timeout for long-running requests
    )

