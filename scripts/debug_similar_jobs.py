#!/usr/bin/env python3
"""Debug script for similar jobs computation with verbose logging."""

import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure verbose logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
)


def test_database_connection():
    """Test basic database connectivity."""
    logger.info("🔌 Testing database connection...")
    try:
        from database.client import db
        
        result = db.client.table("job_postings").select("id").limit(1).execute()
        logger.success(f"✅ Database connected! Found {len(result.data or [])} test record(s)")
        return True
    except Exception as exc:
        logger.error(f"❌ Database connection failed: {exc}")
        return False


def test_load_single_job(job_id: str):
    """Load and display context for a single job."""
    logger.info(f"📦 Loading context for job {job_id}...")
    
    try:
        from services.similar_jobs import get_similar_jobs_service
        
        service = get_similar_jobs_service()
        contexts = service.load_job_contexts_by_ids([job_id])
        
        if not contexts:
            logger.warning(f"⚠️ No context found for job {job_id}")
            return None
        
        ctx = contexts[0]
        logger.info(f"📋 Job Context for {job_id}:")
        logger.info(f"   Title: {ctx.title}")
        logger.info(f"   Type: {ctx.type_datarol}")
        logger.info(f"   Region: {ctx.region} ({ctx.country_code})")
        logger.info(f"   Contract: {ctx.contract}")
        logger.info(f"   Languages: {list(ctx.languages.keys())}")
        logger.info(f"   Ecosystems: {list(ctx.ecosystems.keys())}")
        logger.info(f"   Skill map size: {len(ctx.skill_map())}")
        
        return ctx
    except Exception as exc:
        logger.error(f"❌ Failed to load job context: {exc}")
        import traceback
        traceback.print_exc()
        return None


def test_load_batch():
    """Load a small batch of active jobs."""
    logger.info("📦 Loading batch of active jobs...")
    
    try:
        from services.similar_jobs import get_similar_jobs_service
        
        service = get_similar_jobs_service()
        
        # Get first batch
        for batch in service.iter_active_job_contexts():
            logger.success(f"✅ Loaded batch of {len(batch)} jobs")
            
            # Show first 3
            for i, ctx in enumerate(batch[:3]):
                logger.info(f"   [{i+1}] {ctx.id[:8]}... - {ctx.title}")
            
            return batch
        
        logger.warning("⚠️ No active jobs found")
        return []
    except Exception as exc:
        logger.error(f"❌ Failed to load batch: {exc}")
        import traceback
        traceback.print_exc()
        return []


def test_compute_similarity(job_id: str, limit: int = 5):
    """Compute similar jobs for a single job."""
    logger.info(f"🧮 Computing similar jobs for {job_id}...")
    
    try:
        from services.similar_jobs import get_similar_jobs_service
        
        service = get_similar_jobs_service()
        
        # Load target job
        logger.debug("Loading target job context...")
        target_contexts = service.load_job_contexts_by_ids([job_id])
        if not target_contexts:
            logger.error(f"❌ Job {job_id} not found")
            return
        
        target = target_contexts[0]
        logger.success(f"✅ Target job loaded: {target.title}")
        
        # Load candidates (first batch)
        logger.debug("Loading candidate jobs...")
        candidates = []
        for batch in service.iter_active_job_contexts():
            candidates.extend(batch)
            break  # Just first batch for debugging
        
        logger.success(f"✅ Loaded {len(candidates)} candidate jobs")
        
        # Compute similarities
        logger.debug("Computing similarity scores...")
        results = service.find_similar_jobs(target, candidates, limit=limit)
        
        logger.success(f"✅ Found {len(results)} similar jobs:")
        for i, result in enumerate(results, 1):
            # Get candidate title
            candidate = next((c for c in candidates if c.id == result.job_id), None)
            title = candidate.title if candidate else "Unknown"
            
            logger.info(f"   [{i}] Score: {result.score:.3f} - {result.job_id[:8]}... - {title}")
            logger.debug(f"       Breakdown: skill={result.breakdown.skill:.3f}, role={result.breakdown.role:.3f}, region={result.breakdown.region:.3f}, contract={result.breakdown.contract:.3f}")
        
        return results
    except Exception as exc:
        logger.error(f"❌ Failed to compute similarities: {exc}")
        import traceback
        traceback.print_exc()
        return []


def test_persist(job_id: str, dry_run: bool = True):
    """Test persisting similar job IDs."""
    logger.info(f"💾 Testing persist for {job_id} (dry_run={dry_run})...")
    
    try:
        from services.similar_jobs import get_similar_jobs_service
        
        service = get_similar_jobs_service()
        
        # Load and compute
        contexts = service.load_job_contexts_by_ids([job_id])
        if not contexts:
            logger.error(f"❌ Job {job_id} not found")
            return
        
        # Load candidates
        candidates = []
        for batch in service.iter_active_job_contexts():
            candidates.extend(batch)
            break
        
        # Compute
        results = service.find_similar_jobs(contexts[0], candidates, limit=10)
        similar_ids = [r.job_id for r in results]
        
        logger.info(f"📝 Would persist {len(similar_ids)} similar job IDs:")
        for sid in similar_ids[:5]:
            logger.info(f"   - {sid}")
        if len(similar_ids) > 5:
            logger.info(f"   ... and {len(similar_ids) - 5} more")
        
        if not dry_run:
            logger.warning("⚠️ Actually persisting to database...")
            service.update_similar_job_ids(job_id, similar_ids)
            logger.success("✅ Persisted successfully!")
        else:
            logger.info("ℹ️ Dry run - not persisting")
        
    except Exception as exc:
        logger.error(f"❌ Failed to persist: {exc}")
        import traceback
        traceback.print_exc()


def main():
    """Run all debug tests."""
    logger.info("=" * 80)
    logger.info("🐛 SIMILAR JOBS DEBUG SCRIPT")
    logger.info("=" * 80)
    
    # Test 1: Database connection
    if not test_database_connection():
        logger.error("❌ Database connection failed - stopping")
        return
    
    logger.info("")
    
    # Test 2: Load batch
    batch = test_load_batch()
    if not batch:
        logger.error("❌ No jobs found - stopping")
        return
    
    logger.info("")
    
    # Test 3: Load single job
    test_job_id = "a0fe9090-2aa2-4c76-be7c-994a3a034513"
    ctx = test_load_single_job(test_job_id)
    
    logger.info("")
    
    # Test 4: Compute similarities
    if ctx:
        test_compute_similarity(test_job_id, limit=5)
    
    logger.info("")
    
    # Test 5: Test persist (dry run)
    if ctx:
        test_persist(test_job_id, dry_run=True)
    
    logger.info("")
    logger.info("=" * 80)
    logger.success("✅ Debug script completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
