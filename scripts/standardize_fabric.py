"""Standardize Microsoft Fabric ecosystem variants to canonical 'Fabric'."""

from loguru import logger
from database.client import db

def standardize_fabric():
    """Merge MS Fabric, Microsoft Data Fabric, and Data Fabric into Fabric."""
    
    logger.info("Starting Fabric standardization...")
    
    # Get all Fabric variants
    ecosystems = db.get_all_ecosystems(active_only=True)
    
    fabric_variants = {}
    for eco in ecosystems:
        name = eco['name']
        if name in ['Fabric', 'MS Fabric', 'Microsoft Data Fabric', 'Data Fabric']:
            fabric_variants[name] = eco
            logger.info(f"Found: {name} (ID: {eco['id']}, relevance: {eco.get('relevance_score')})")
    
    if 'Fabric' not in fabric_variants:
        logger.error("Canonical 'Fabric' entry not found!")
        return
    
    canonical = fabric_variants['Fabric']
    canonical_id = canonical['id']
    
    logger.info(f"\nCanonical entry: Fabric (ID: {canonical_id})")
    
    # Merge each variant
    variants_to_merge = ['MS Fabric', 'Microsoft Data Fabric', 'Data Fabric']
    
    for variant_name in variants_to_merge:
        if variant_name not in fabric_variants:
            logger.warning(f"Variant '{variant_name}' not found, skipping")
            continue
        
        variant = fabric_variants[variant_name]
        variant_id = variant['id']
        
        logger.info(f"\nMerging {variant_name} → Fabric")
        
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
                    "canonical_name": "Fabric",
                    "type": "ecosystem",
                    "notes": "Microsoft Fabric standardization"
                })\
                .execute()
            logger.info(f"  Created alias: {variant_name} → Fabric")
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.info(f"  Alias already exists: {variant_name}")
            else:
                logger.error(f"  Failed to create alias: {e}")
    
    # Update Fabric display name
    db.client.table("ecosystems")\
        .update({"display_name": "Microsoft Fabric"})\
        .eq("id", canonical_id)\
        .execute()
    
    logger.success("\n✅ Fabric standardization complete!")
    logger.info("Display name updated to 'Microsoft Fabric'")

if __name__ == "__main__":
    standardize_fabric()
