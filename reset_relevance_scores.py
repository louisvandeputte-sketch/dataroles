#!/usr/bin/env python3
"""Reset all relevance scores to trigger re-scoring with updated prompt."""

from database.client import db
from loguru import logger

logger.info("🔄 Resetting all relevance scores...")

# Reset programming languages
result_langs = db.client.table("programming_languages")\
    .update({"relevance_score": None})\
    .not_.is_("relevance_score", "null")\
    .execute()

langs_count = len(result_langs.data) if result_langs.data else 0
logger.info(f"✅ Reset {langs_count} programming language scores")

# Reset ecosystems
result_ecos = db.client.table("ecosystems")\
    .update({"relevance_score": None})\
    .not_.is_("relevance_score", "null")\
    .execute()

ecos_count = len(result_ecos.data) if result_ecos.data else 0
logger.info(f"✅ Reset {ecos_count} ecosystem scores")

total = langs_count + ecos_count
logger.success(f"🎉 Reset complete! {total} items will be re-scored automatically")
logger.info("⏳ Auto-enrichment service will re-score them within a few minutes")
