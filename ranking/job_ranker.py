"""
Job Ranking System voor Data Role Platform
==========================================

Dit systeem rankt job vacatures op basis van meerdere criteria:
- Versheid & Actualiteit (25%)
- Kwaliteit van Informatie (20%)
- Transparantie & Directheid (20%)
- Match met Data Roles (15%)
- Volledigheid Profiel (10%)
- Bedrijfsreputatie (10%)

Plus diversiteitsmodifiers om spreiding te garanderen.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
from loguru import logger
from dateutil import parser as date_parser

from database.client import db


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse datetime string handling various PostgreSQL formats"""
    if not date_string:
        return None
    try:
        # Use dateutil parser which handles more formats
        dt = date_parser.parse(date_string)
        # Convert to naive datetime (remove timezone info) to match datetime.now()
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{date_string}': {e}")
        return None


@dataclass
class JobData:
    """Simplified job data for ranking"""
    id: str
    title: str
    company_id: str
    company_name: str
    location_id: str
    posted_date: Optional[datetime]
    seniority_level: Optional[str]
    employment_type: Optional[str]
    function_areas: Optional[List[str]]
    base_salary_min: Optional[float]
    base_salary_max: Optional[float]
    apply_url: Optional[str]
    num_applicants: Optional[int]
    is_active: bool
    title_classification: Optional[str]  # 'Data', 'NIS', 'Other'
    
    # Company data
    company_industry: Optional[str]
    company_url: Optional[str]
    company_logo_data: Optional[bytes]
    company_employee_count_range: Optional[str]
    company_rating: Optional[float]
    company_reviews_count: Optional[int]
    hiring_model: Optional[str]  # 'recruitment', 'direct', or 'unknown' from company_master_data
    is_faang: bool
    
    # Location data
    location_city: Optional[str]
    
    # Enrichment data
    skills_must_have: Optional[List[str]]
    samenvatting_kort: Optional[str]
    samenvatting_lang: Optional[str]
    data_role_type: Optional[str]
    seniority: Optional[List[str]]
    enrichment_completed_at: Optional[datetime]
    
    # Scraping data
    scraped_at: Optional[datetime]  # When job was last scraped
    
    # Description data
    description_text: Optional[str]
    
    # Tech stack data (for bonus calculation) - with defaults, must come after non-default fields
    must_have_programmeertalen: Optional[List[str]] = None
    nice_to_have_programmeertalen: Optional[List[str]] = None
    must_have_ecosystemen: Optional[List[str]] = None
    nice_to_have_ecosystemen: Optional[List[str]] = None
    
    # Calculated scores
    freshness_score: float = 0.0
    quality_score: float = 0.0
    transparency_score: float = 0.0
    role_match_score: float = 0.0
    completeness_score: float = 0.0
    reputation_score: float = 0.0
    base_score: float = 0.0
    
    # Diversity metrics
    company_rank: int = 0
    role_type_rank: int = 0
    location_rank: int = 0
    seniority_rank: int = 0
    
    # Final score
    final_score: float = 0.0
    final_rank: int = 0


class JobRankingSystem:
    """
    Hoofdklasse voor het ranken van job vacatures
    
    Weights:
    - Versheid: 25%
    - Kwaliteit: 20%
    - Transparantie: 20%
    - Role Match: 15%
    - Volledigheid: 10%
    - Reputatie: 10%
    """
    
    # Weights voor verschillende categorieën
    WEIGHT_FRESHNESS = 0.25
    WEIGHT_QUALITY = 0.20
    WEIGHT_TRANSPARENCY = 0.20
    WEIGHT_ROLE_MATCH = 0.15
    WEIGHT_COMPLETENESS = 0.10
    WEIGHT_REPUTATION = 0.10
    
    # Diversity penalties
    COMPANY_PENALTY_PER_EXTRA = 0.15
    ROLE_PENALTY_PER_EXTRA = 0.10
    SENIORITY_PENALTY_PER_EXTRA = 0.05
    LOCATION_BOOST_FIRST = 1.05
    
    # Diversity limits
    MAX_COMPANY_IN_TOP_20 = 3
    MAX_COMPANY_IN_TOP_50 = 5
    MAX_CONSECUTIVE_SAME_ROLE = 2
    
    def calculate_freshness_score(self, job: JobData) -> float:
        """
        Bereken versheid score (0-100) op basis van posted_date
        MEGA BOOST: Jobs <= 30 uur oud krijgen 150 punten (50% extra!)
        """
        if not job.posted_date:
            return 20
        
        age = datetime.now() - job.posted_date
        hours_old = age.total_seconds() / 3600
        
        # MEGA BOOST: <= 30 uur = 150 punten (50% extra!)
        if hours_old <= 30:
            return 150
        elif age <= timedelta(days=1):
            return 100
        elif age <= timedelta(days=3):
            return 90
        elif age <= timedelta(days=7):
            return 75
        elif age <= timedelta(days=14):
            return 60
        elif age <= timedelta(days=30):
            return 40
        else:
            return 20
    
    def calculate_quality_score(self, job: JobData) -> float:
        """Bereken kwaliteit score (0-100) met tech stack bonus en zware straf voor geen skills"""
        score = 0
        
        # Skills: 20 punten - ZWARE STRAF als geen skills
        if job.skills_must_have and len(job.skills_must_have) >= 3:
            score += 20
        elif not job.skills_must_have or len(job.skills_must_have) == 0:
            score -= 30  # NIEUWE STRAF: -30 punten voor geen skills
        
        # Salaris: 25 punten
        if job.base_salary_min is not None and job.base_salary_max is not None:
            score += 25
        
        # Seniority: 15 punten
        if job.seniority_level:
            score += 15
        
        # Employment type: 10 punten
        if job.employment_type:
            score += 10
        
        # Lange samenvatting: 15 punten
        if job.samenvatting_lang:
            score += 15
        
        # Gedetailleerde beschrijving: 10 punten
        if job.description_text and len(job.description_text) > 500:
            score += 10
        
        # Tech stack bonus: max 15 punten (NEW!)
        # Hoe meer tech stack items, hoe beter (toont expertise en specificiteit)
        tech_count = 0
        if job.must_have_programmeertalen:
            tech_count += len(job.must_have_programmeertalen)
        if job.nice_to_have_programmeertalen:
            tech_count += len(job.nice_to_have_programmeertalen)
        if job.must_have_ecosystemen:
            tech_count += len(job.must_have_ecosystemen)
        if job.nice_to_have_ecosystemen:
            tech_count += len(job.nice_to_have_ecosystemen)
        
        # Scale: 0-5 items = 0-5 punten, 6-10 items = 6-10 punten, 11+ items = 11-15 punten
        if tech_count > 0:
            tech_bonus = min(15, tech_count)  # Cap at 15 points
            score += tech_bonus
        
        return min(100, score)  # Cap at 100
    
    def calculate_transparency_score(self, job: JobData) -> float:
        """Bereken transparantie score (0-100)"""
        score = 0
        
        # Direct werkgever: 60 punten (recruitment agencies krijgen 0)
        if job.hiring_model == 'direct':
            score += 60
        
        # Apply URL: 20 punten
        if job.apply_url:
            score += 20
        
        # Aantal applicants: 10 punten
        if job.num_applicants is not None:
            score += 10
        
        # Company logo: 10 punten
        if job.company_logo_data:
            score += 10
        
        return score
    
    def calculate_role_match_score(self, job: JobData) -> float:
        """Bereken data role match score (0-100) met EXTREME straffen voor NIS/Other"""
        role_type = job.data_role_type
        
        if not role_type:
            return 10  # Verlaagd van 30 naar 10 - geen enrichment is zeer slecht
        
        # EXTREME STRAF: NIS en Other roles (niet-data roles)
        # Deze moeten ALTIJD onderaan komen, zelfs met perfecte andere scores
        if role_type == 'Other':
            return -200  # VERHOOGD: -200 punten voor 'Other' (was -50)
        if role_type == 'NIS':
            return -99999  # MASSIVE PENALTY: NIS jobs always at absolute bottom
        
        # Tier 1: Top data roles
        if role_type in ['Data Engineer', 'Data Scientist']:
            return 100
        
        # Tier 2: Core data roles
        if role_type in ['Data Analyst', 'Analytics Engineer']:
            return 90
        
        # Tier 3: Specialized data roles
        if role_type in ['ML Engineer', 'BI Developer', 'Machine Learning Engineer']:
            return 85
        
        # Tier 4: Andere data-gerelateerde roles
        return 70
    
    def calculate_completeness_score(self, job: JobData) -> float:
        """Bereken volledigheid score (0-100)"""
        score = 0
        
        # Company info
        if job.company_employee_count_range:
            score += 15
        
        if job.company_industry:
            score += 15
        
        if job.company_url:
            score += 15
        
        # Location info
        if job.location_city:
            score += 15
        
        # Function areas
        if job.function_areas and len(job.function_areas) > 0:
            score += 20
        
        # AI enrichment completed
        if job.enrichment_completed_at:
            score += 20
        
        return score
    
    def calculate_reputation_score(self, job: JobData) -> float:
        """Bereken reputatie score (0-100) met zware straf voor recruitment agencies"""
        score = 0
        
        # ZWARE STRAF: Recruitment agencies krijgen maximaal 20 punten (was 100)
        if job.hiring_model == 'recruitment':
            # Alleen basis rating, geen size of FAANG bonus
            rating = job.company_rating
            if rating is not None and rating >= 4.0:
                score += 20  # Max 20 punten voor recruitment
            else:
                score += 10  # Minimale score
            return score  # Early return, geen verdere bonussen
        
        # Voor directe werkgevers: normale scoring
        # Rating score (max 40)
        rating = job.company_rating
        if rating is not None:
            if rating >= 4.5:
                score += 40
            elif rating >= 4.0:
                score += 30
            elif rating >= 3.5:
                score += 20
            else:
                score += 10
        else:
            score += 10
        
        # Size score (max 30)
        size_range = job.company_employee_count_range
        if size_range:
            large_companies = ['1001-5000', '5001-10000', '10000+']
            medium_companies = ['201-500', '501-1000']
            
            if size_range in large_companies:
                score += 30
            elif size_range in medium_companies:
                score += 20
            else:
                score += 10
        else:
            score += 10
        
        # FAANG bonus (max 30)
        if job.is_faang:
            score += 30
        
        return score
    
    def calculate_base_scores(self, jobs: List[JobData]) -> List[JobData]:
        """Bereken alle basis scores"""
        for job in jobs:
            job.freshness_score = self.calculate_freshness_score(job)
            job.quality_score = self.calculate_quality_score(job)
            job.transparency_score = self.calculate_transparency_score(job)
            job.role_match_score = self.calculate_role_match_score(job)
            job.completeness_score = self.calculate_completeness_score(job)
            job.reputation_score = self.calculate_reputation_score(job)
            
            job.base_score = (
                job.freshness_score * self.WEIGHT_FRESHNESS +
                job.quality_score * self.WEIGHT_QUALITY +
                job.transparency_score * self.WEIGHT_TRANSPARENCY +
                job.role_match_score * self.WEIGHT_ROLE_MATCH +
                job.completeness_score * self.WEIGHT_COMPLETENESS +
                job.reputation_score * self.WEIGHT_REPUTATION
            )
            
            # EXTREME PENALTY for non-enriched jobs (no AI enrichment)
            # These should ALWAYS rank at the bottom, even with perfect other scores
            # and recent scrape bonus (+15 max)
            if not job.enrichment_completed_at:
                job.base_score = -9999  # Set to very negative - guarantees bottom rank
        
        return jobs
    
    def calculate_diversity_ranks(self, jobs: List[JobData]) -> List[JobData]:
        """Bereken diversity ranks"""
        sorted_jobs = sorted(jobs, key=lambda j: j.base_score, reverse=True)
        
        company_counts = defaultdict(int)
        role_counts = defaultdict(int)
        location_counts = defaultdict(int)
        seniority_counts = defaultdict(int)
        
        for job in sorted_jobs:
            company_counts[job.company_id] += 1
            job.company_rank = company_counts[job.company_id]
            
            role_counts[job.data_role_type] += 1
            job.role_type_rank = role_counts[job.data_role_type]
            
            location_counts[job.location_id] += 1
            job.location_rank = location_counts[job.location_id]
            
            seniority_counts[job.seniority] += 1
            job.seniority_rank = seniority_counts[job.seniority]
        
        return sorted_jobs
    
    def calculate_hourly_variance(self, job: JobData) -> float:
        """
        Bereken hourly variance voor dynamische rankings.
        - Elk uur verandert de ranking door nieuwe variance
        - Recente jobs krijgen extra boost
        - Recent gescrapete jobs krijgen GROTE bonus (binnen 26u)
        - Max impact: ~10-15 punten op final score
        """
        import hashlib
        
        variance = 0.0
        
        # 1. Recent scrape bonus (NIEUW - binnen 26 uur)
        if job.scraped_at:
            hours_since_scraped = (datetime.now() - job.scraped_at).total_seconds() / 3600
            
            # GROTE BONUS voor recent gescrapete jobs (< 26 uur)
            if hours_since_scraped < 26:
                # Linear decay: 10 punten bij 0u, 0 punten bij 26u
                scrape_bonus = max(0, 10 * (1 - hours_since_scraped / 26))
                variance += scrape_bonus
                # Extra boost voor zeer recente scrapes (< 6 uur)
                if hours_since_scraped < 6:
                    variance += 5  # Extra 5 punten voor super fresh scrapes
        
        # 2. Time-based freshness boost (afneemt over tijd)
        if job.posted_date:
            hours_since_posted = (datetime.now() - job.posted_date).total_seconds() / 3600
            
            # Boost voor jobs < 48 uur oud
            if hours_since_posted < 48:
                freshness_boost = max(0, 5 - (hours_since_posted / 10))  # Max 5 punten
                variance += freshness_boost
        
        # 3. Hourly rotation factor (VERHOOGD voor meer variatie)
        current_hour = datetime.now().hour
        hour_factor = (current_hour % 6) * 0.8  # 0, 0.8, 1.6, 2.4, 3.2, 4.0 punten
        variance += hour_factor
        
        # 4. Hourly tie-breaker (verandert elk uur, stabiel binnen uur)
        hour_str = datetime.now().strftime('%Y-%m-%d-%H')  # Include hour for hourly change
        seed_str = f"{hour_str}-{job.id}"
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        tiebreaker = (hash_val % 200) / 100  # -1.0 tot +1.0 punten
        variance += tiebreaker
        
        return variance
    
    def apply_diversity_modifiers(self, jobs: List[JobData]) -> List[JobData]:
        """Pas diversity modifiers en hourly variance toe"""
        for job in jobs:
            score = job.base_score
            
            # Company diversity penalty
            company_modifier = 1 - (job.company_rank - 1) * self.COMPANY_PENALTY_PER_EXTRA
            company_modifier = max(0.1, company_modifier)
            score *= company_modifier
            
            # Role type diversity penalty
            role_modifier = 1 - (job.role_type_rank - 1) * self.ROLE_PENALTY_PER_EXTRA
            role_modifier = max(0.3, role_modifier)
            score *= role_modifier
            
            # Location diversity boost
            if job.location_rank == 1:
                score *= self.LOCATION_BOOST_FIRST
            
            # Seniority diversity penalty
            seniority_modifier = 1 - (job.seniority_rank - 1) * self.SENIORITY_PENALTY_PER_EXTRA
            seniority_modifier = max(0.5, seniority_modifier)
            score *= seniority_modifier
            
            # Add hourly variance for freshness
            hourly_variance = self.calculate_hourly_variance(job)
            score += hourly_variance
            
            job.final_score = score
        
        return jobs
    
    def rank_jobs(self, jobs: List[JobData]) -> List[JobData]:
        """Volledige ranking pipeline"""
        # Filter alleen actieve jobs
        active_jobs = [job for job in jobs if job.is_active]
        
        logger.info(f"📊 Ranking {len(active_jobs)} active jobs...")
        
        # Bereken base scores
        jobs_with_scores = self.calculate_base_scores(active_jobs)
        
        # Bereken diversity ranks
        jobs_with_ranks = self.calculate_diversity_ranks(jobs_with_scores)
        
        # Pas diversity modifiers toe
        jobs_with_final_scores = self.apply_diversity_modifiers(jobs_with_ranks)
        
        # Sorteer op final_score (DESC), dan op job ID (ASC) voor consistentie bij gelijke scores
        ranked_jobs = sorted(
            jobs_with_final_scores, 
            key=lambda j: (-j.final_score, j.id)  # Negative score for DESC, ID for ASC
        )
        
        # Bepaal final ranks
        # NIS (Not In Scope) jobs krijgen rank 999999 om ze onderaan te plaatsen
        data_jobs_count = 0
        for i, job in enumerate(ranked_jobs):
            if job.title_classification == 'NIS':
                job.final_rank = 999999  # NIS jobs always at the bottom
            else:
                data_jobs_count += 1
                job.final_rank = data_jobs_count  # Normal ranking for Data jobs
        
        nis_count = len(ranked_jobs) - data_jobs_count
        logger.info(f"✅ Ranking complete! {data_jobs_count} Data jobs ranked, {nis_count} NIS jobs set to rank 999999.")
        
        return ranked_jobs


def load_jobs_from_database(only_needs_ranking: bool = False) -> List[JobData]:
    """
    Load jobs from database with necessary joins using pagination
    
    Args:
        only_needs_ranking: If True, only load jobs where needs_ranking = TRUE
    """
    logger.info("Loading jobs from database with pagination...")
    
    jobs = []
    page_size = 1000  # Supabase limit
    offset = 0
    
    while True:
        # Use denormalized view for efficient data loading
        # This avoids Supabase/PostgREST join limitations
        query = db.client.table("job_ranking_view")\
            .select("*")\
            .range(offset, offset + page_size - 1)
        
        # Optionally filter to only jobs that need ranking
        # Note: needs_ranking is on job_postings table, not in view
        # So we need to join or filter differently if this is needed
        # For now, we load all active Data jobs
        
        result = query.execute()
        
        if not result.data:
            break  # No more jobs
        
        logger.info(f"Loaded batch: {len(result.data)} jobs (offset {offset})")
        
        # Process this batch
        for row in result.data:
            # All data is already denormalized in the view
            # Check if FAANG
            faang_companies = ['google', 'microsoft', 'meta', 'amazon', 'apple', 'netflix', 'facebook', 'alphabet']
            is_faang = row.get('company_name', '').lower() in faang_companies
            
            # Parse labels JSON for seniority
            labels = row.get('labels')
            if isinstance(labels, str):
                import json
                try:
                    labels = json.loads(labels)
                except:
                    labels = {}
            
            seniority = None
            if labels:
                # Try different language keys for seniority
                for lang in ['nl', 'en', 'fr']:
                    if lang in labels:
                        seniority_value = labels[lang].get('seniority')
                        if seniority_value:
                            # Handle both string and list
                            if isinstance(seniority_value, list):
                                seniority = seniority_value[0] if seniority_value else None
                            else:
                                seniority = seniority_value
                            break
            
            job = JobData(
                id=row['id'],
                title=row['title'],
                company_id=row['company_id'],
                company_name=row.get('company_name', ''),
                location_id=row['location_id'],
                posted_date=parse_datetime(row.get('posted_date')),
                seniority_level=row.get('seniority_level'),
                employment_type=row.get('employment_type'),
                function_areas=row.get('function_areas'),
                base_salary_min=row.get('base_salary_min'),
                base_salary_max=row.get('base_salary_max'),
                apply_url=row.get('apply_url'),
                num_applicants=row.get('num_applicants'),
                is_active=row.get('is_active', True),
                title_classification=row.get('title_classification', 'Data'),  # Default to 'Data' if missing
                
                # Company data (from view)
                company_industry=row.get('company_industry'),
                company_url=row.get('company_url'),
                company_logo_data=row.get('company_logo_data'),
                company_employee_count_range=row.get('company_employee_count_range'),
                company_rating=row.get('company_rating'),
                company_reviews_count=row.get('company_reviews_count'),
                hiring_model=row.get('hiring_model'),
                is_faang=is_faang,
                
                # Location data (from view)
                location_city=row.get('location_city'),
                
                # Enrichment data (from view)
                skills_must_have=row.get('skills_must_have'),
                samenvatting_kort=row.get('samenvatting_kort'),
                samenvatting_lang=row.get('samenvatting_lang'),
                data_role_type=row.get('data_role_type'),
                seniority=seniority,
                enrichment_completed_at=parse_datetime(row.get('enrichment_completed_at')),
                
                # Scraping data - will be populated in next step
                scraped_at=None,
                
                # Tech stack data (from view)
                must_have_programmeertalen=row.get('must_have_programmeertalen', []),
                nice_to_have_programmeertalen=row.get('nice_to_have_programmeertalen', []),
                must_have_ecosystemen=row.get('must_have_ecosystemen', []),
                nice_to_have_ecosystemen=row.get('nice_to_have_ecosystemen', []),
                
                # Description data (from view)
                description_text=row.get('description_text')
            )
            
            jobs.append(job)
        
        # Check if we got less than page_size (last page)
        if len(result.data) < page_size:
            break
        
        # Move to next page
        offset += page_size
    
    # Now fetch most recent scrape times for all jobs in one query
    logger.info(f"Fetching most recent scrape times for {len(jobs)} jobs...")
    if jobs:
        job_ids = [job.id for job in jobs]
        
        # Get most recent detected_at for each job from job_scrape_history
        # We'll do this in batches to avoid query size limits
        batch_size = 100
        job_scrape_times = {}
        
        for i in range(0, len(job_ids), batch_size):
            batch_ids = job_ids[i:i + batch_size]
            
            # Query for this batch
            scrape_result = db.client.table("job_scrape_history")\
                .select("job_posting_id, detected_at")\
                .in_("job_posting_id", batch_ids)\
                .order("detected_at", desc=True)\
                .execute()
            
            # Get most recent scrape for each job
            for row in scrape_result.data:
                job_id = row['job_posting_id']
                if job_id not in job_scrape_times:
                    # First (most recent) entry for this job
                    job_scrape_times[job_id] = parse_datetime(row['detected_at'])
        
        # Update jobs with scrape times
        for job in jobs:
            if job.id in job_scrape_times:
                job.scraped_at = job_scrape_times[job.id]
        
        logger.info(f"Found scrape times for {len(job_scrape_times)} jobs")
        
        # Note: Enrichment data is already loaded from the view, no need to fetch separately
    
    logger.info(f"Loaded {len(jobs)} jobs from database")
    return jobs


def save_rankings_to_database(ranked_jobs: List[JobData]):
    """Save ranking scores back to database"""
    logger.info(f"Saving rankings for {len(ranked_jobs)} jobs...")
    
    # Use SINGLE timestamp for ALL jobs in this ranking run
    # This is critical for queries that filter by latest ranking_updated_at
    ranking_timestamp = datetime.now().isoformat()
    
    for job in ranked_jobs:
        # Create metadata JSON
        metadata = {
            'freshness_score': round(job.freshness_score, 2),
            'quality_score': round(job.quality_score, 2),
            'transparency_score': round(job.transparency_score, 2),
            'role_match_score': round(job.role_match_score, 2),
            'completeness_score': round(job.completeness_score, 2),
            'reputation_score': round(job.reputation_score, 2),
            'base_score': round(job.base_score, 2),
            'company_rank': job.company_rank,
            'role_type_rank': job.role_type_rank,
            'location_rank': job.location_rank,
            'seniority_rank': job.seniority_rank
        }
        
        # Update database - use SAME timestamp for all jobs
        db.client.table("job_postings").update({
            'ranking_score': round(job.final_score, 2),
            'ranking_position': job.final_rank,
            'ranking_updated_at': ranking_timestamp,  # Same for all jobs!
            'ranking_metadata': metadata,
            'needs_ranking': False  # Mark as ranked
        }).eq('id', job.id).execute()
    
    logger.info("✅ Rankings saved to database")


def calculate_and_save_rankings():
    """Main function to calculate and save rankings"""
    logger.info("🚀 Starting job ranking calculation...")
    
    try:
        # Load jobs
        jobs = load_jobs_from_database()
        
        # Rank jobs
        ranker = JobRankingSystem()
        ranked_jobs = ranker.rank_jobs(jobs)
        
        # Save to database
        save_rankings_to_database(ranked_jobs)
        
        logger.info("✅ Job ranking calculation complete!")
        return len(ranked_jobs)
        
    except Exception as e:
        logger.error(f"❌ Error calculating rankings: {e}")
        raise
