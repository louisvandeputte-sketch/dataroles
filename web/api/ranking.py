"""API endpoints for job ranking."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from ranking.job_ranker import calculate_and_save_rankings
import os
import shutil

router = APIRouter()


def calculate_and_clear_cache():
    """Calculate rankings and automatically clear cache when done"""
    try:
        # Run ranking
        calculate_and_save_rankings()
        
        # Clear cache silently after successful ranking
        cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', '.cache')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            logger.info("✅ Cache cleared automatically after ranking completion")
    except Exception as e:
        logger.error(f"Error in ranking or cache clear: {e}")
        raise


class RankingStatus(BaseModel):
    """Ranking status response"""
    status: str
    message: str
    last_updated: str = None
    jobs_ranked: int = None


@router.post("/calculate")
async def trigger_ranking_calculation(background_tasks: BackgroundTasks):
    """
    Manually trigger ranking calculation
    
    This will run in the background and update all job rankings.
    """
    logger.info("🎯 Manual ranking calculation triggered via API")
    
    # Run in background with auto-cache clear
    background_tasks.add_task(calculate_and_clear_cache)
    
    return RankingStatus(
        status="started",
        message="Ranking calculation started in background"
    )


@router.get("/status")
async def get_ranking_status():
    """
    Get status of last ranking calculation
    
    Returns when rankings were last updated and how many jobs were ranked.
    """
    from database.client import db
    
    try:
        # Get most recent ranking update
        result = db.client.table("job_postings")\
            .select("ranking_updated_at, ranking_position")\
            .not_.is_("ranking_updated_at", "null")\
            .order("ranking_updated_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            last_updated = result.data[0]['ranking_updated_at']
            
            # Count ranked jobs
            count_result = db.client.table("job_postings")\
                .select("id", count="exact")\
                .not_.is_("ranking_score", "null")\
                .execute()
            
            return RankingStatus(
                status="completed",
                message="Rankings are up to date",
                last_updated=last_updated,
                jobs_ranked=count_result.count
            )
        else:
            return RankingStatus(
                status="never_run",
                message="Rankings have never been calculated"
            )
            
    except Exception as e:
        logger.error(f"Error getting ranking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
