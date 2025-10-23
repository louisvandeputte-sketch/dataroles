"""Test enrichment with mock data to debug database save."""

from loguru import logger
from ingestion.llm_enrichment import save_enrichment_to_db

# Mock enrichment data in v18 format
mock_enrichment = {
    "data_role_type": "Data Engineer",
    "role_level": ["Technical", "Lead"],
    "seniority": ["Medior", "Senior"],
    "contract": ["Permanent", "Freelance"],
    "sourcing_type": "Direct",
    "summary_short": "As a Data Engineer you will build scalable data pipelines.",
    "summary_long": "As a Data Engineer you are part of the data engineering team.",
    "must_have_languages": ["Python", "SQL"],
    "nice_to_have_languages": ["Scala"],
    "must_have_ecosystems": ["Azure", "Databricks"],
    "nice_to_have_ecosystems": ["Kafka"],
    "must_have_spoken_languages": ["Dutch"],
    "nice_to_have_spoken_languages": ["French"],
    "i18n": {
        "nl": {
            "data_role_type": "Data Engineer",
            "role_level": ["Technisch", "Leidend"],
            "seniority": ["Medior", "Senior"],
            "contract": ["Vast", "Freelance"],
            "sourcing_type": "Rechtstreeks",
            "summary_short": "Als Data Engineer bouw je schaalbare data pipelines.",
            "summary_long": "Als Data Engineer maak je deel uit van het data engineering team."
        },
        "fr": {
            "data_role_type": "Ingénieur Data",
            "role_level": ["Technique", "Lead"],
            "seniority": ["Intermédiaire", "Senior"],
            "contract": ["CDI", "Freelance"],
            "sourcing_type": "Direct",
            "summary_short": "En tant qu'Ingénieur Data, vous construisez des pipelines de données évolutifs.",
            "summary_long": "En tant qu'Ingénieur Data, vous faites partie de l'équipe d'ingénierie des données."
        }
    }
}

if __name__ == "__main__":
    # Test with a real job ID from your database
    test_job_id = input("Enter a job ID to test: ")
    
    logger.info(f"Testing enrichment save for job {test_job_id}")
    logger.info(f"Mock data: {mock_enrichment}")
    
    try:
        result = save_enrichment_to_db(test_job_id, mock_enrichment)
        if result:
            logger.success("✅ Enrichment saved successfully!")
        else:
            logger.error("❌ Failed to save enrichment")
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
