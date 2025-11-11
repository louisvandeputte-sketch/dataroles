"""
Auto-enrichment service for locations and job titles.
Automatically enriches new location records and classifies job titles in the background.
Includes automatic retry for quota errors after 24h.
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from database.client import db
from ingestion.location_enrichment import enrich_location
from ingestion.job_title_classifier import classify_job_title
from ingestion.relevance_scorer import score_programming_language, score_ecosystem


class AutoEnrichService:
    """Service to automatically enrich new location records, classify job titles, and score tech stack relevance."""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
    
    async def start(self):
        """Start the auto-enrichment service."""
        self.running = True
        logger.info("🤖 Auto-enrichment service started (locations + job titles + tech relevance)")
        
        # Wait before first check to avoid blocking startup
        logger.info(f"⏳ Waiting {self.check_interval}s before first enrichment check")
        await asyncio.sleep(self.check_interval)
        
        while self.running:
            try:
                # Process all enrichment tasks
                await self.process_pending_locations()
                await self.process_pending_job_titles()
                await self.process_pending_tech_scores()
            except Exception as e:
                logger.error(f"Error in auto-enrichment service: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the auto-enrichment service."""
        self.running = False
        logger.info("🛑 Auto-enrichment service stopped")
    
    async def process_pending_locations(self):
        """Process locations that need enrichment, including retry of old quota errors."""
        try:
            # Calculate retry cutoff (24 hours ago)
            retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Find locations that need enrichment:
            # 1. Never enriched (ai_enriched is null or false) AND no error
            # 2. Has error AND error is old enough to retry (>24h)
            result = db.client.table("locations")\
                .select("id, city, country_code, region, ai_enrichment_error, ai_enriched_at")\
                .or_(
                    f"and(ai_enriched.is.null,ai_enrichment_error.is.null),"
                    f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
                    f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
                )\
                .limit(10)\
                .execute()
            
            locations = result.data if result.data else []
            
            if not locations:
                return  # No pending locations
            
            # Count retries vs new
            retry_count = sum(1 for loc in locations if loc.get("ai_enrichment_error"))
            new_count = len(locations) - retry_count
            
            logger.info(f"🔄 Auto-enriching {len(locations)} locations ({new_count} new, {retry_count} retries)")
            
            # Enrich each location
            for location in locations:
                try:
                    location_id = location["id"]
                    city = location.get("city")
                    country_code = location.get("country_code")
                    region = location.get("region")
                    has_error = location.get("ai_enrichment_error")
                    
                    if has_error:
                        logger.info(f"Retrying: {city}, {country_code} (previous error)")
                    else:
                        logger.info(f"Enriching: {city}, {country_code}")
                    
                    # Enrich the location
                    enrichment_data = enrich_location(
                        location_id=location_id,
                        city=city,
                        country_code=country_code,
                        region=region
                    )
                    
                    if enrichment_data:
                        logger.success(f"✅ Auto-enriched: {city}")
                    else:
                        logger.warning(f"⚠️ Failed to auto-enrich: {city}")
                
                except Exception as e:
                    logger.error(f"Failed to enrich location {location.get('city')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending locations: {e}")
    
    async def process_pending_job_titles(self):
        """Process job titles that need classification."""
        try:
            # Find jobs that need title classification:
            # title_classification is null
            result = db.client.table("job_postings")\
                .select("id, title")\
                .is_("title_classification", "null")\
                .limit(20)\
                .execute()
            
            jobs = result.data if result.data else []
            
            if not jobs:
                return  # No pending jobs
            
            logger.info(f"🏷️  Auto-classifying {len(jobs)} job titles")
            
            # Classify each job title
            for job in jobs:
                try:
                    job_id = job["id"]
                    title = job.get("title")
                    
                    if not title:
                        logger.warning(f"Job {job_id} has no title, skipping")
                        continue
                    
                    logger.debug(f"Classifying: {title}")
                    
                    # Classify the title
                    classification, error = classify_job_title(title)
                    
                    if classification:
                        # Save classification to database
                        db.client.table("job_postings")\
                            .update({
                                "title_classification": classification
                            })\
                            .eq("id", job_id)\
                            .execute()
                        
                        logger.success(f"✅ Classified '{title}' as {classification}")
                    elif error:
                        # Save error (but don't retry - classification errors are usually permanent)
                        logger.warning(f"⚠️ Failed to classify '{title}': {error}")
                
                except Exception as e:
                    logger.error(f"Failed to classify job title '{job.get('title')}': {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending job titles: {e}")
    
    async def process_pending_tech_scores(self):
        """Process programming languages and ecosystems that need relevance scoring."""
        try:
            # Find programming languages without relevance_score
            languages_result = db.client.table("programming_languages")\
                .select("id, name")\
                .is_("relevance_score", "null")\
                .limit(10)\
                .execute()
            
            languages = languages_result.data if languages_result.data else []
            
            # Find ecosystems without relevance_score
            ecosystems_result = db.client.table("ecosystems")\
                .select("id, name")\
                .is_("relevance_score", "null")\
                .limit(10)\
                .execute()
            
            ecosystems = ecosystems_result.data if ecosystems_result.data else []
            
            total = len(languages) + len(ecosystems)
            
            if total == 0:
                return  # Nothing to score
            
            logger.info(f"📊 Auto-scoring {len(languages)} languages + {len(ecosystems)} ecosystems")
            
            # Score programming languages
            for lang in languages:
                try:
                    lang_id = lang["id"]
                    name = lang.get("name")
                    
                    if not name:
                        logger.warning(f"Language {lang_id} has no name, skipping")
                        continue
                    
                    logger.debug(f"Scoring language: {name}")
                    score_programming_language(lang_id, name)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to score language '{lang.get('name')}': {e}")
                    continue
            
            # Score ecosystems
            for eco in ecosystems:
                try:
                    eco_id = eco["id"]
                    name = eco.get("name")
                    
                    if not name:
                        logger.warning(f"Ecosystem {eco_id} has no name, skipping")
                        continue
                    
                    logger.debug(f"Scoring ecosystem: {name}")
                    score_ecosystem(eco_id, name)
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to score ecosystem '{eco.get('name')}': {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to fetch pending tech items: {e}")


# Global service instance
_auto_enrich_service: Optional[AutoEnrichService] = None


def get_auto_enrich_service() -> AutoEnrichService:
    """Get or create the auto-enrichment service instance."""
    global _auto_enrich_service
    if _auto_enrich_service is None:
        _auto_enrich_service = AutoEnrichService()
    return _auto_enrich_service
