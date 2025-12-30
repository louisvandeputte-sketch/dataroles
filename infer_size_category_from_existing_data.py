"""
Infer size_category from existing company_master_data using LLM.
This is an ad-hoc script to extract size_category from already enriched company data.
"""

import json
import time
import os
from openai import OpenAI
from database import db
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key)

def get_companies_without_size_category():
    """Get all enriched companies that don't have size_category yet."""
    # Get companies that are enriched but missing size_category
    # This should be ~1622 companies (1797 total - 175 with size_category)
    result = db.client.table("company_master_data")\
        .select("*")\
        .eq("ai_enriched", True)\
        .is_("size_category", "null")\
        .execute()
    
    return result.data

def format_company_data_for_llm(company_data):
    """Format all company data as unstructured text for LLM input."""
    
    # Build unstructured text with all available info
    text_parts = []
    
    # Company info
    if company_data.get("bedrijfswebsite"):
        text_parts.append(f"Website: {company_data['bedrijfswebsite']}")
    
    if company_data.get("jobspagina"):
        text_parts.append(f"Jobs page: {company_data['jobspagina']}")
    
    # Descriptions
    if company_data.get("bedrijfsomschrijving_nl"):
        text_parts.append(f"\nBedrijfsomschrijving (NL):\n{company_data['bedrijfsomschrijving_nl']}")
    
    if company_data.get("bedrijfsomschrijving_en"):
        text_parts.append(f"\nCompany description (EN):\n{company_data['bedrijfsomschrijving_en']}")
    
    if company_data.get("bedrijfsomschrijving_fr"):
        text_parts.append(f"\nDescription de l'entreprise (FR):\n{company_data['bedrijfsomschrijving_fr']}")
    
    # Sector info
    sectors = []
    if company_data.get("sector_nl"):
        sectors.append(f"NL: {company_data['sector_nl']}")
    if company_data.get("sector_en"):
        sectors.append(f"EN: {company_data['sector_en']}")
    if company_data.get("sector_fr"):
        sectors.append(f"FR: {company_data['sector_fr']}")
    if sectors:
        text_parts.append(f"\nSector: {', '.join(sectors)}")
    
    # Employee count
    if company_data.get("aantal_werknemers"):
        text_parts.append(f"\nEmployee count: {company_data['aantal_werknemers']}")
    
    # Location
    if company_data.get("locatie_belgie"):
        text_parts.append(f"Belgian location: {company_data['locatie_belgie']}")
    
    # Hiring model
    if company_data.get("hiring_model"):
        text_parts.append(f"Hiring model: {company_data['hiring_model']}")
    
    # Factlets (weetjes)
    if company_data.get("weetjes"):
        weetjes = company_data["weetjes"]
        if isinstance(weetjes, list) and len(weetjes) > 0:
            text_parts.append("\nFactlets:")
            for i, factlet in enumerate(weetjes, 1):
                if isinstance(factlet, dict):
                    category = factlet.get("category", "")
                    text_en = factlet.get("text_en", "")
                    if text_en:
                        text_parts.append(f"  {i}. [{category}] {text_en}")
    
    # Email info
    if company_data.get("email_hr"):
        text_parts.append(f"\nHR email: {company_data['email_hr']}")
    if company_data.get("email_algemeen"):
        text_parts.append(f"General email: {company_data['email_algemeen']}")
    
    return "\n".join(text_parts)

def infer_size_category(company_text):
    """Call OpenAI API to infer size_category from company data."""
    try:
        response = client.responses.create(
            prompt={
                "id": "pmpt_69431995db5c8193b1978e898ae5a62209c78f31e39e9acf",
                "version": "3"
            },
            input=company_text
        )
        
        # Extract the response from the new OpenAI response format
        # The output is in response.output[1].content[0].text (after reasoning)
        if hasattr(response, 'output') and isinstance(response.output, list):
            # Find the message output (skip reasoning items)
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    if hasattr(item, 'content') and isinstance(item.content, list):
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                text = content_item.text
                                # Try to parse as JSON
                                try:
                                    result = json.loads(text)
                                    return result.get("size_category")
                                except json.JSONDecodeError:
                                    logger.warning(f"Could not parse LLM output as JSON: {text}")
                                    return None
        
        logger.warning(f"Unexpected response format")
        return None
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None

def update_size_category(company_id, size_category):
    """Update company_master_data with inferred size_category."""
    try:
        db.client.table("company_master_data")\
            .update({
                "size_category": size_category,
                "size_enriched_at": "now()"
            })\
            .eq("id", company_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update company {company_id}: {e}")
        return False

def main():
    """Main function to process all companies."""
    logger.info("="*80)
    logger.info("INFERRING SIZE_CATEGORY FROM EXISTING COMPANY DATA")
    logger.info("="*80)
    
    # Get companies without size_category
    companies = get_companies_without_size_category()
    total = len(companies)
    
    logger.info(f"\nFound {total} enriched companies without size_category")
    
    if total == 0:
        logger.info("✅ All companies already have size_category!")
        return
    
    # Process each company
    successful = 0
    failed = 0
    
    for i, company in enumerate(companies, 1):
        company_id = company["id"]
        
        # Get company name from companies table
        try:
            company_info = db.client.table("companies")\
                .select("name")\
                .eq("id", company["company_id"])\
                .single()\
                .execute()
            company_name = company_info.data["name"]
        except:
            company_name = "Unknown"
        
        logger.info(f"\n[{i}/{total}] Processing: {company_name}")
        
        # Format company data
        company_text = format_company_data_for_llm(company)
        
        # Infer size_category
        size_category = infer_size_category(company_text)
        
        if size_category:
            logger.info(f"  ✅ Inferred size_category: {size_category}")
            
            # Update database
            if update_size_category(company_id, size_category):
                successful += 1
                logger.success(f"  💾 Updated database")
            else:
                failed += 1
                logger.error(f"  ❌ Failed to update database")
        else:
            failed += 1
            logger.warning(f"  ⚠️  Could not infer size_category")
        
        # Rate limiting: wait 1 second between requests
        if i < total:
            time.sleep(1)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total companies processed: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {(successful/total*100):.1f}%")

if __name__ == "__main__":
    main()
