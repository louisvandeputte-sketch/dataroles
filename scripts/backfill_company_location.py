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

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
        query = db.client.table("companies")\
            .select("""
                id, 
                name,
                company_master_data!inner(
                    bedrijfswebsite,
                    bedrijfsomschrijving_nl,
                    bedrijfsomschrijving_en,
                    sector_en,
                    ai_enriched,
                    locatie_belgie
                )
            """)\
            .eq("company_master_data.ai_enriched", True)\
            .is_("company_master_data.locatie_belgie", "null")
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        
        companies = []
        for row in result.data:
            # Flatten structure
            company = {
                "id": row["id"],
                "name": row["name"],
                **row["company_master_data"]
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
    
    # Description (prefer Dutch, fallback to English)
    description = company.get('bedrijfsomschrijving_nl') or company.get('bedrijfsomschrijving_en')
    if description:
        parts.append(f"Description: {description}")
    
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
