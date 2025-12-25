"""Standardize Power Query ecosystem variants to canonical 'Power Query'."""

from loguru import logger
from database.client import db

def standardize_power_query():
    """Merge Excel Power Query and PowerQuery into Power Query."""
    
    logger.info("Starting Power Query standardization...")
    
    # Get all Power Query variants
    ecosystems = db.get_all_ecosystems(active_only=True)
    
    power_query_variants = {}
    for eco in ecosystems:
        name = eco['name']
        if name in ['Power Query', 'Excel Power Query', 'PowerQuery']:
            power_query_variants[name] = eco
            logger.info(f"Found: {name} (ID: {eco['id']}, relevance: {eco.get('relevance_score')})")
    
    if 'Power Query' not in power_query_variants:
        logger.error("Canonical 'Power Query' entry not found!")
        return
    
    canonical = power_query_variants['Power Query']
    canonical_id = canonical['id']
    
    logger.info(f"\nCanonical entry: Power Query (ID: {canonical_id})")
    
    # Merge each variant
    variants_to_merge = ['Excel Power Query', 'PowerQuery']
    
    for variant_name in variants_to_merge:
        if variant_name not in power_query_variants:
            logger.warning(f"Variant '{variant_name}' not found, skipping")
            continue
        
        variant = power_query_variants[variant_name]
        variant_id = variant['id']
        
        logger.info(f"\nMerging {variant_name} → Power Query")
        
        # Get job assignments
        result = db.client.table("job_ecosystems")\
            .select("*")\
            .eq("ecosystem_id", variant_id)\
            .execute()
        
        assignments = result.data if result.data else []
        logger.info(f"  Found {len(assignments)} job assignments")
        
        updated = 0
        deleted = 0
        
        # Update or delete assignments
        for assignment in assignments:
            job_id = assignment['job_posting_id']
            
            # Check if canonical already assigned
            existing = db.client.table("job_ecosystems")\
                .select("id")\
                .eq("job_posting_id", job_id)\
                .eq("ecosystem_id", canonical_id)\
                .maybe_single()\
                .execute()
            
            if existing and existing.data:
                # Delete duplicate
                db.client.table("job_ecosystems")\
                    .delete()\
                    .eq("id", assignment['id'])\
                    .execute()
                deleted += 1
            else:
                # Update to canonical
                db.client.table("job_ecosystems")\
                    .update({"ecosystem_id": canonical_id})\
                    .eq("id", assignment['id'])\
                    .execute()
                updated += 1
        
        logger.info(f"  Updated: {updated}, Deleted: {deleted}")
        
        # Deactivate variant
        db.client.table("ecosystems")\
            .update({"is_active": False})\
            .eq("id", variant_id)\
            .execute()
        
        logger.info(f"  Deactivated {variant_name}")
        
        # Create alias
        try:
            db.client.table("tech_stack_aliases")\
                .insert({
                    "alias": variant_name,
                    "canonical_name": "Power Query",
                    "type": "ecosystem",
                    "notes": "Power Query standardization"
                })\
                .execute()
            logger.info(f"  Created alias: {variant_name} → Power Query")
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.info(f"  Alias already exists: {variant_name}")
            else:
                logger.error(f"  Failed to create alias: {e}")
    
    # Update Power Query display name to be clear
    db.client.table("ecosystems")\
        .update({"display_name": "Power Query"})\
        .eq("id", canonical_id)\
        .execute()
    
    logger.success("\n✅ Power Query standardization complete!")
    logger.info("Display name set to 'Power Query'")

if __name__ == "__main__":
    standardize_power_query()
