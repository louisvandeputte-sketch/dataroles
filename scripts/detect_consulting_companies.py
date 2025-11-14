#!/usr/bin/env python3
"""Detect and mark consulting companies using AI"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from openai import OpenAI
from database.client import db
from loguru import logger
import json
import time

client = OpenAI()

PROMPT = """You receive ONE short company summary.

Task: decide if the company is primarily a consulting firm.

If the main activity is advice/consulting (e.g. strategy, management, business, IT, process, advisory services), then label as Consulting = TRUE, otherwise FALSE.

Output ONLY a JSON object with EXACTLY these fields, in this order:
{
"reasoning": "...short explanation of why it is or is not consulting...",
"Consulting": true/false
}

- "reasoning": 1 korte zin met je redenering, altijd eerst.
- "Consulting": true if mainly consulting, false otherwise.

Company summary:
{summary}
"""

def classify_company(company_id: str, company_name: str, summary: str) -> dict:
    """Classify if a company is consulting using AI"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a business classifier. Output only valid JSON."},
                {"role": "user", "content": PROMPT.format(summary=summary)}
            ],
            temperature=0.1,
            max_tokens=150
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        is_consulting = result.get("Consulting", False)
        reasoning = result.get("reasoning", "")
        
        logger.info(f"{'✅ CONSULTING' if is_consulting else '❌ NOT consulting'}: {company_name}")
        logger.info(f"   Reasoning: {reasoning}")
        
        return {
            "is_consulting": is_consulting,
            "reasoning": reasoning
        }
        
    except Exception as e:
        logger.error(f"Error classifying {company_name}: {e}")
        return None


def main():
    """Main function to detect consulting companies"""
    
    # Get all companies with master data that have a description
    logger.info("Fetching companies with descriptions...")
    
    result = db.client.table("company_master_data")\
        .select("company_id, bedrijfsomschrijving_en, companies(name)")\
        .not_.is_("bedrijfsomschrijving_en", "null")\
        .execute()
    
    companies = result.data
    logger.info(f"Found {len(companies)} companies with descriptions")
    
    stats = {
        "total": len(companies),
        "consulting": 0,
        "not_consulting": 0,
        "errors": 0
    }
    
    for i, company_data in enumerate(companies, 1):
        company_id = company_data["company_id"]
        company_name = company_data["companies"]["name"] if company_data.get("companies") else "Unknown"
        summary = company_data["bedrijfsomschrijving_en"]
        
        logger.info(f"\n[{i}/{len(companies)}] Processing: {company_name}")
        
        # Classify
        classification = classify_company(company_id, company_name, summary)
        
        if classification:
            is_consulting = classification["is_consulting"]
            
            # Update database
            db.client.table("company_master_data")\
                .update({"is_consulting": is_consulting})\
                .eq("company_id", company_id)\
                .execute()
            
            if is_consulting:
                stats["consulting"] += 1
            else:
                stats["not_consulting"] += 1
        else:
            stats["errors"] += 1
        
        # Rate limiting
        time.sleep(0.5)
    
    logger.info("\n" + "="*60)
    logger.info("FINAL STATS:")
    logger.info(f"  Total processed: {stats['total']}")
    logger.info(f"  Consulting: {stats['consulting']}")
    logger.info(f"  Not consulting: {stats['not_consulting']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
