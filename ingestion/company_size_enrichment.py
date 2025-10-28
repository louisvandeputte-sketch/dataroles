"""
Company size classification enrichment using OpenAI LLM.
Classifies companies into maturity stages: startup, scaleup, SME, etc.
"""

from openai import OpenAI
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json

from config import settings
from database.client import db


# Initialize OpenAI client
client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=300.0  # 5 minutes timeout for web search
)

# Prompt ID for company size classification
COMPANY_SIZE_PROMPT_ID = "pmpt_690071d7955c8197b884d85937a37d750f6a6bdab899a90d"
COMPANY_SIZE_PROMPT_VERSION = "3"


def enrich_company_size(company_id: str, company_name: str, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify company maturity stage using OpenAI LLM with web search.
    
    Args:
        company_id: UUID of the company
        company_name: Company name
        country: Optional country for better search context
        
    Returns:
        Dict with classification results or None if failed
    """
    try:
        logger.info(f"Classifying company size: {company_name}")
        
        # Build input context
        input_data = {
            "company_name": company_name
        }
        if country:
            input_data["country"] = country
        
        # Call OpenAI with prompt
        response = client.responses.create(
            prompt={
                "id": COMPANY_SIZE_PROMPT_ID,
                "version": COMPANY_SIZE_PROMPT_VERSION
            },
            input=input_data
        )
        
        # Parse response
        if not response or not response.output:
            logger.error(f"Empty response from OpenAI for {company_name}")
            save_enrichment_error(company_id, "Empty response from LLM")
            return None
        
        # Extract classification data
        classification = response.output
        
        # Validate required fields
        required_fields = ["category", "confidence", "summary"]
        if not all(field in classification for field in required_fields):
            logger.error(f"Missing required fields in response for {company_name}")
            save_enrichment_error(company_id, "Invalid response structure")
            return None
        
        # Validate category
        valid_categories = [
            "startup", "scaleup", "sme", "established_enterprise",
            "corporate", "public_company", "government", "unknown"
        ]
        if classification["category"] not in valid_categories:
            logger.error(f"Invalid category '{classification['category']}' for {company_name}")
            save_enrichment_error(company_id, f"Invalid category: {classification['category']}")
            return None
        
        # Save to database
        save_classification_to_db(company_id, classification)
        
        logger.success(f"✅ Classified {company_name} as {classification['category']} (confidence: {classification['confidence']})")
        return classification
        
    except Exception as e:
        logger.error(f"Failed to classify {company_name}: {e}")
        save_enrichment_error(company_id, str(e))
        return None


def save_classification_to_db(company_id: str, classification: Dict[str, Any]) -> None:
    """Save company size classification to database."""
    try:
        # Extract summary translations
        summary = classification.get("summary", {})
        
        # Prepare update data
        update_data = {
            "size_category": classification["category"],
            "size_confidence": float(classification["confidence"]),
            "size_summary_en": summary.get("en"),
            "size_summary_nl": summary.get("nl"),
            "size_summary_fr": summary.get("fr"),
            "size_key_arguments": json.dumps(classification.get("key_arguments", [])),
            "size_sources": json.dumps(classification.get("sources", [])),
            "size_enriched_at": datetime.utcnow().isoformat(),
            "size_enrichment_error": None
        }
        
        # Update database
        db.client.table("company_master_data")\
            .update(update_data)\
            .eq("id", company_id)\
            .execute()
        
        logger.debug(f"Saved classification for company {company_id}")
        
    except Exception as e:
        logger.error(f"Failed to save classification to database: {e}")
        raise


def save_enrichment_error(company_id: str, error_message: str) -> None:
    """Save enrichment error to database."""
    try:
        db.client.table("company_master_data")\
            .update({
                "size_enrichment_error": error_message,
                "size_enriched_at": datetime.utcnow().isoformat()
            })\
            .eq("id", company_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to save error to database: {e}")


def get_classification_stats() -> Dict[str, Any]:
    """Get statistics about company size classifications."""
    try:
        # Total companies
        total_result = db.client.table("company_master_data")\
            .select("id", count="exact")\
            .execute()
        total = total_result.count if total_result.count else 0
        
        # Classified companies
        classified_result = db.client.table("company_master_data")\
            .select("id", count="exact")\
            .not_.is_("size_category", "null")\
            .execute()
        classified = classified_result.count if classified_result.count else 0
        
        # Failed classifications
        failed_result = db.client.table("company_master_data")\
            .select("id", count="exact")\
            .not_.is_("size_enrichment_error", "null")\
            .execute()
        failed = failed_result.count if failed_result.count else 0
        
        # Breakdown by category
        categories_result = db.client.table("company_master_data")\
            .select("size_category", count="exact")\
            .not_.is_("size_category", "null")\
            .execute()
        
        category_counts = {}
        if categories_result.data:
            for row in categories_result.data:
                category = row.get("size_category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total": total,
            "classified": classified,
            "pending": total - classified - failed,
            "failed": failed,
            "categories": category_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get classification stats: {e}")
        return {
            "total": 0,
            "classified": 0,
            "pending": 0,
            "failed": 0,
            "categories": {}
        }


if __name__ == "__main__":
    # Test with a known company
    test_company_id = "test-id"
    test_company_name = "Deliverect"
    test_country = "Belgium"
    
    result = enrich_company_size(test_company_id, test_company_name, test_country)
    
    if result:
        print(f"\n✅ Classification successful!")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Summary (EN): {result['summary']['en']}")
        print(f"Summary (NL): {result['summary']['nl']}")
    else:
        print("\n❌ Classification failed")
