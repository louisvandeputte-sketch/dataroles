"""
Backfill locatie_belgie for already enriched companies using LLM parser.

This script:
1. Finds enriched companies without locatie_belgie
2. Constructs input text from company data (description, website, etc.)
3. Calls OpenAI parser to extract Belgian city
4. Updates locatie_belgie column

Usage:
    python scripts/backfill_company_location.py [--dry-run] [--limit N]
"""

import sys
import os
import json
import time
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from loguru import logger
from database.client import db
from config.settings import settings

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or settings.openai_api_key)

# Parser prompt ID
LOCATION_PARSER_PROMPT_ID = "pmpt_692050bb9ac48193bbe40d1fcfcd67de07f0d791b20ce220"
LOCATION_PARSER_PROMPT_VERSION = "1"


def get_companies_without_location(limit: Optional[int] = None) -> list:
    """
    Get enriched companies that don't have locatie_belgie set.
    
    Args:
        limit: Maximum number of companies to return
        
    Returns:
        List of company records with master data
    """
    try:
        # Get companies with master data (including weetjes for location hints)
        query = db.client.table("company_master_data")\
            .select("company_id, bedrijfswebsite, bedrijfsomschrijving_nl, bedrijfsomschrijving_en, sector_en, aantal_werknemers, weetjes, size_key_arguments, locatie_belgie, companies!inner(id, name)")\
            .eq("ai_enriched", True)\
            .is_("locatie_belgie", "null")
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        
        companies = []
        for row in result.data:
            # Flatten structure
            company_info = row.get("companies", {})
            company = {
                "id": row["company_id"],
                "name": company_info.get("name", "Unknown"),
                "bedrijfswebsite": row.get("bedrijfswebsite"),
                "bedrijfsomschrijving_nl": row.get("bedrijfsomschrijving_nl"),
                "bedrijfsomschrijving_en": row.get("bedrijfsomschrijving_en"),
                "sector_en": row.get("sector_en"),
                "aantal_werknemers": row.get("aantal_werknemers"),
                "weetjes": row.get("weetjes"),
                "size_key_arguments": row.get("size_key_arguments")
            }
            companies.append(company)
        
        logger.info(f"Found {len(companies)} enriched companies without locatie_belgie")
        return companies
        
    except Exception as e:
        logger.error(f"Failed to fetch companies: {e}")
        return []


def construct_input_text(company: Dict[str, Any]) -> str:
    """
    Construct input text for location parser from company data.
    Uses all available enriched data including factlets and size arguments.
    
    Args:
        company: Company record with master data
        
    Returns:
        Input text for parser
    """
    parts = []
    
    # Company name
    parts.append(f"Company: {company['name']}")
    
    # Website
    if company.get('bedrijfswebsite'):
        parts.append(f"Website: {company['bedrijfswebsite']}")
    
    # Sector
    if company.get('sector_en'):
        parts.append(f"Sector: {company['sector_en']}")
    
    # Employee count
    if company.get('aantal_werknemers'):
        parts.append(f"Employees: {company['aantal_werknemers']}")
    
    # Description (prefer Dutch, fallback to English)
    description = company.get('bedrijfsomschrijving_nl') or company.get('bedrijfsomschrijving_en')
    if description:
        parts.append(f"Description: {description}")
    
    # Factlets (weetjes) - may contain hq_location category with city info
    weetjes = company.get('weetjes')
    if weetjes and isinstance(weetjes, list):
        factlet_texts = []
        for weetje in weetjes:
            if isinstance(weetje, dict):
                # Prefer Dutch text, fallback to English
                text = weetje.get('text_nl') or weetje.get('text_en')
                category = weetje.get('category', '')
                if text:
                    factlet_texts.append(f"[{category}] {text}")
        
        if factlet_texts:
            parts.append(f"Facts: {' | '.join(factlet_texts)}")
    
    # Size key arguments - may mention headquarters or office locations
    size_args = company.get('size_key_arguments')
    if size_args and isinstance(size_args, list):
        parts.append(f"Key facts: {' | '.join(size_args)}")
    
    return "\n".join(parts)


def parse_location(input_text: str) -> Optional[str]:
    """
    Call OpenAI parser to extract Belgian city from input text.
    
    Args:
        input_text: Unstructured text about the company
        
    Returns:
        City name or None if not found
    """
    try:
        response = client.responses.create(
            prompt={
                "id": LOCATION_PARSER_PROMPT_ID,
                "version": LOCATION_PARSER_PROMPT_VERSION
            },
            input=input_text
        )
        
        # Extract JSON output
        city = None
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'type') and content.type == 'output_text':
                            result = json.loads(content.text)
                            city = result.get('city', '').strip()
                            break
                if city:
                    break
        
        return city if city else None
        
    except Exception as e:
        logger.error(f"Failed to parse location: {e}")
        return None


def update_company_location(company_id: str, city: str, dry_run: bool = False) -> bool:
    """
    Update locatie_belgie for a company.
    
    Args:
        company_id: Company UUID
        city: City name
        dry_run: If True, don't actually update
        
    Returns:
        True if successful
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would update company {company_id} with city: {city}")
        return True
    
    try:
        db.client.table("company_master_data")\
            .update({"locatie_belgie": city})\
            .eq("company_id", company_id)\
            .execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update company {company_id}: {e}")
        return False


def main():
    """Main backfill process."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill locatie_belgie for enriched companies")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update database")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between API calls (seconds)")
    
    args = parser.parse_args()
    
    logger.info("Starting location backfill process")
    if args.dry_run:
        logger.warning("DRY RUN MODE - No database updates will be made")
    
    # Get companies
    companies = get_companies_without_location(limit=args.limit)
    
    if not companies:
        logger.info("No companies to process")
        return
    
    # Process each company
    stats = {
        "total": len(companies),
        "success": 0,
        "failed": 0,
        "no_location": 0
    }
    
    for i, company in enumerate(companies, 1):
        try:
            logger.info(f"[{i}/{len(companies)}] Processing: {company['name']}")
            
            # Construct input
            input_text = construct_input_text(company)
            logger.debug(f"Input text: {input_text[:200]}...")
            
            # Parse location
            city = parse_location(input_text)
            
            if city:
                logger.info(f"✅ Found city: {city}")
                
                # Update database
                if update_company_location(company['id'], city, dry_run=args.dry_run):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            else:
                logger.warning(f"⚠️ No city found for {company['name']}")
                stats["no_location"] += 1
            
            # Rate limiting delay
            if i < len(companies):
                time.sleep(args.delay)
        
        except Exception as e:
            logger.error(f"Error processing {company['name']}: {e}")
            stats["failed"] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("BACKFILL COMPLETE")
    logger.info(f"Total companies: {stats['total']}")
    logger.info(f"✅ Successfully updated: {stats['success']}")
    logger.info(f"⚠️ No location found: {stats['no_location']}")
    logger.info(f"❌ Failed: {stats['failed']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
