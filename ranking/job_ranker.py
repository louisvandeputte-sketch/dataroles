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
        """Bereken versheid score (0-100) op basis van posted_date"""
        if not job.posted_date:
            return 20
        
        age = datetime.now() - job.posted_date
        
        if age <= timedelta(days=1):
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
        """Bereken data role match score (0-100) met EXTRA zware straffen voor NIS/Other"""
        role_type = job.data_role_type
        
        if not role_type:
            return 30  # Verlaagd van 50 naar 30
        
        # EXTRA ZWARE STRAF: NIS en Other roles (niet-data roles)
        if role_type == 'Other':
            return -50  # NIEUWE STRAF: -50 punten voor 'Other' (was 0)
        if role_type == 'NIS':
            return -30  # NIEUWE STRAF: -30 punten voor 'NIS' (was 0)
        
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
        Bereken kleine hourly variance voor freshness.
        - Recente jobs krijgen kleine boost die elk uur iets verandert
        - Stabiel binnen hetzelfde uur, verandert elk uur
        - Max impact: ~2-3 punten op final score
        """
        import hashlib
        
        variance = 0.0
        
        # 1. Time-based freshness boost (afneemt over tijd)
        if job.posted_date:
            hours_since_posted = (datetime.now() - job.posted_date).total_seconds() / 3600
            
            # Boost voor jobs < 48 uur oud
            if hours_since_posted < 48:
                freshness_boost = max(0, 3 - (hours_since_posted / 16))  # Max 3 punten
                variance += freshness_boost
        
        # 2. Hourly rotation factor (kleine variatie per uur)
        current_hour = datetime.now().hour
        hour_factor = (current_hour % 4) * 0.5  # 0, 0.5, 1.0, of 1.5 punten
        variance += hour_factor
        
        # 3. Daily tie-breaker (stabiel per dag, subtiele variatie)
        date_str = datetime.now().strftime('%Y-%m-%d')
        seed_str = f"{date_str}-{job.id}"
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        tiebreaker = (hash_val % 100) / 200  # -0.5 tot +0.5 punten
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
        for i, job in enumerate(ranked_jobs):
            job.final_rank = i + 1
        
        logger.info(f"✅ Ranking complete! {len(ranked_jobs)} jobs ranked.")
        
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
        # Query jobs in batches - join company_master_data for hiring_model
        query = db.client.table("job_postings")\
            .select("""
                *,
                companies(*),
                company_master_data!inner(hiring_model),
                locations(*),
                llm_enrichment(*),
                job_descriptions(description_text)
            """)\
            .eq("is_active", True)\
            .eq("title_classification", "Data")\
            .range(offset, offset + page_size - 1)
        
        # Optionally filter to only jobs that need ranking
        if only_needs_ranking:
            query = query.eq("needs_ranking", True)
        
        result = query.execute()
        
        if not result.data:
            break  # No more jobs
        
        logger.info(f"Loaded batch: {len(result.data)} jobs (offset {offset})")
        
        # Process this batch
        for row in result.data:
            company = row.get('companies', {})
            company_master = row.get('company_master_data', {})
            location = row.get('locations', {})
            enrichment = row.get('llm_enrichment', {})
            description = row.get('job_descriptions', {})
            
            # Get hiring_model from company_master_data
            hiring_model = company_master.get('hiring_model') if company_master else None
            
            # Check if FAANG
            faang_companies = ['google', 'microsoft', 'meta', 'amazon', 'apple', 'netflix', 'facebook', 'alphabet']
            is_faang = company.get('name', '').lower() in faang_companies
            
            # Use type_datarol column (English canonical value) for consistent matching
            # This ensures 'Other' matches correctly in penalty logic
            data_role_type = enrichment.get('type_datarol')
            
            # Parse labels JSON for seniority
            labels = enrichment.get('labels')
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
                        seniority = labels[lang].get('seniority')
                        if seniority:
                            break
            
            job = JobData(
                id=row['id'],
                title=row['title'],
                company_id=row['company_id'],
                company_name=company.get('name', ''),
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
                
                # Company data
                company_industry=company.get('industry'),
                company_url=company.get('company_url'),
                company_logo_data=company.get('logo_data'),
                company_employee_count_range=company.get('employee_count_range'),
                company_rating=company.get('rating'),
                company_reviews_count=company.get('reviews_count'),
                hiring_model=hiring_model,
                is_faang=is_faang,
                
                # Location data
                location_city=location.get('city'),
                
                # Enrichment data
                skills_must_have=enrichment.get('skills_must_have_nl'),
                samenvatting_kort=enrichment.get('samenvatting_kort_nl'),
                samenvatting_lang=enrichment.get('samenvatting_lang_nl'),
                data_role_type=data_role_type,
                seniority=seniority,
                enrichment_completed_at=parse_datetime(enrichment.get('enrichment_completed_at')),
                
                # Tech stack data
                must_have_programmeertalen=enrichment.get('must_have_programmeertalen', []),
                nice_to_have_programmeertalen=enrichment.get('nice_to_have_programmeertalen', []),
                must_have_ecosystemen=enrichment.get('must_have_ecosystemen', []),
                nice_to_have_ecosystemen=enrichment.get('nice_to_have_ecosystemen', []),
                
                # Description data
                description_text=description.get('description_text') if description else None
            )
            
            jobs.append(job)
        
        # Check if we got less than page_size (last page)
        if len(result.data) < page_size:
            break
        
        # Move to next page
        offset += page_size
    
    logger.info(f"Loaded {len(jobs)} jobs from database")
    return jobs


def save_rankings_to_database(ranked_jobs: List[JobData]):
    """Save ranking scores back to database"""
    logger.info(f"Saving rankings for {len(ranked_jobs)} jobs...")
    
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
        
        # Update database
        db.client.table("job_postings").update({
            'ranking_score': round(job.final_score, 2),
            'ranking_position': job.final_rank,
            'ranking_updated_at': datetime.now().isoformat(),
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
