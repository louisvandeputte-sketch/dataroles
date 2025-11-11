"""Mark all active jobs for re-ranking after algorithm changes."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database.client import db


def main():
    """Mark all active jobs for re-ranking"""
    logger.info("Marking all active jobs for re-ranking...")
    
    try:
        result = db.client.table("job_postings")\
            .update({"needs_ranking": True})\
            .eq("is_active", True)\
            .execute()
        
        logger.success(f"✅ Marked all active jobs for re-ranking")
        logger.info("Run auto_calculate_rankings.py to recalculate rankings with new algorithm")
        
    except Exception as e:
        logger.error(f"❌ Error marking jobs: {e}")
        raise


if __name__ == "__main__":
    main()
