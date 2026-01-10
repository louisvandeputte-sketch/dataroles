#!/usr/bin/env python3
"""
Populate temporary sector columns in companies table using LLM parser.

Uses OpenAI prompt pmpt_6960de8c16ec81969f8abdb7de9d88ec0536ca0afb5799b9 to standardize
sector names in EN, NL, and FR.
"""

import sys
import time
import json
from typing import Optional, Dict, Any
from loguru import logger

sys.path.insert(0, "/Users/louisvandeputte/datarole")

from openai import OpenAI
from database.client import db
from config.settings import settings


# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def get_companies_needing_sector_update(limit: int = 100) -> list:
    """Get companies that need sector classification based on bedrijfsomschrijving_en and weetjes."""
    result = db.client.table("company_master_data").select(
        "id, company_id, bedrijfsomschrijving_en, weetjes, companies(name)"
    ).is_("sector_en_temporary", "null").limit(limit).execute()
    
    # Filter to only include records with at least one of the required fields
    return [r for r in (result.data or []) if r.get("bedrijfsomschrijving_en") or r.get("weetjes")]


def standardize_sector_with_llm(bedrijfsomschrijving_en: str, weetjes: str) -> Optional[Dict[str, str]]:
    """
    Call OpenAI LLM to determine sector based on company description and facts.
    
    Args:
        bedrijfsomschrijving_en: Company description in English
        weetjes: Company facts/tidbits
    
    Returns dict with keys: sector_en, sector_nl, sector_fr
    """
    import os
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY") or settings.openai_api_key,
        timeout=60.0
    )
    
    # Build input string from available data
    input_text = ""
    if bedrijfsomschrijving_en:
        input_text += f"Company description: {bedrijfsomschrijving_en}\n"
    if weetjes:
        input_text += f"Company facts: {weetjes}"
    
    try:
        response = client.responses.create(
            prompt={
                "id": "pmpt_6960de8c16ec81969f8abdb7de9d88ec0536ca0afb5799b9",
                "version": "1"
            },
            input=input_text.strip()
        )
        
        # Parse response - same pattern as company_enrichment.py
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message' and hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'type') and content.type == 'output_text':
                            text = content.text.strip()
                            try:
                                output = json.loads(text)
                                return {
                                    "sector_en": output.get("sector_en"),
                                    "sector_nl": output.get("sector_nl"),
                                    "sector_fr": output.get("sector_fr")
                                }
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON parse error: {e}")
                                return None
        
        return None
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return None


def update_company_sectors(master_data_id: str, sectors: Dict[str, str]) -> bool:
    """Update company_master_data with standardized sector values."""
    try:
        db.client.table("company_master_data").update({
            "sector_en_temporary": sectors.get("sector_en"),
            "sector_nl_temporary": sectors.get("sector_nl"),
            "sector_fr_temporary": sectors.get("sector_fr")
        }).eq("id", master_data_id).execute()
        
        return True
    except Exception as e:
        logger.error(f"Failed to update company_master_data {master_data_id}: {e}")
        return False


def main(batch_size: int = 100, delay: float = 0.5, dry_run: bool = False):
    """
    Main function to populate temporary sector columns.
    
    Args:
        batch_size: Number of companies to process per batch
        delay: Delay between LLM calls in seconds
        dry_run: If True, don't actually update the database
    """
    logger.info("=" * 60)
    logger.info("SECTOR STANDARDIZATION SCRIPT")
    logger.info("=" * 60)
    
    companies = get_companies_needing_sector_update(limit=batch_size)
    
    if not companies:
        logger.info("No companies need sector updates")
        return
    
    logger.info(f"Found {len(companies)} companies to process")
    
    success_count = 0
    error_count = 0
    
    for i, record in enumerate(companies, 1):
        master_data_id = record["id"]
        company_name = record.get("companies", {}).get("name", "Unknown") if record.get("companies") else "Unknown"
        bedrijfsomschrijving_en = record.get("bedrijfsomschrijving_en", "")
        weetjes = record.get("weetjes", "")
        
        logger.info(f"[{i}/{len(companies)}] Processing: {company_name}")
        
        # Call LLM to determine sector
        sectors = standardize_sector_with_llm(bedrijfsomschrijving_en, weetjes)
        
        if sectors:
            logger.info(f"  → EN: {sectors.get('sector_en')}")
            logger.info(f"  → NL: {sectors.get('sector_nl')}")
            logger.info(f"  → FR: {sectors.get('sector_fr')}")
            
            if not dry_run:
                if update_company_sectors(master_data_id, sectors):
                    success_count += 1
                    logger.success(f"  ✅ Updated")
                else:
                    error_count += 1
                    logger.error(f"  ❌ Failed to update")
            else:
                success_count += 1
                logger.info(f"  [DRY RUN] Would update")
        else:
            error_count += 1
            logger.warning(f"  ⚠️ No LLM response")
        
        # Rate limiting
        if i < len(companies):
            time.sleep(delay)
    
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(companies)}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"❌ Errors: {error_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate temporary sector columns using LLM")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of companies to process")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between LLM calls in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update the database")
    
    args = parser.parse_args()
    
    main(batch_size=args.batch_size, delay=args.delay, dry_run=args.dry_run)
