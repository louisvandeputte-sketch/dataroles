#!/usr/bin/env python3
"""
Add Microsoft Azure logo to all Azure-related ecosystems.

This script:
1. Downloads the Azure logo from the uploaded image
2. Converts it to base64
3. Updates all Azure ecosystems with the logo
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from database.client import db
import base64
from typing import List, Dict

# Azure logo URL (Microsoft's official CDN)
AZURE_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/f/fa/Microsoft_Azure.svg"

# Alternative: Use the uploaded image path if you saved it locally
# AZURE_LOGO_PATH = "/path/to/azure_logo.png"


def get_azure_ecosystems() -> List[Dict]:
    """Get all Azure-related ecosystems."""
    ecosystems = db.get_all_ecosystems(active_only=True) or []
    
    # Filter Azure ecosystems (name starts with "Azure" or display_name contains "Azure")
    azure_ecosystems = [
        eco for eco in ecosystems
        if eco['name'].startswith('Azure') or 
           'Azure' in eco.get('display_name', '') or
           eco['name'] in ['Data Factory', 'Synapse']  # These are Azure services
    ]
    
    return azure_ecosystems


def update_ecosystem_logo(ecosystem_id: str, logo_url: str) -> bool:
    """Update ecosystem with logo URL."""
    try:
        db.client.table("ecosystems")\
            .update({"logo_url": logo_url})\
            .eq("id", ecosystem_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update ecosystem {ecosystem_id}: {e}")
        return False


def main():
    """Main entry point."""
    logger.info("="*80)
    logger.info("ADD AZURE LOGO TO ECOSYSTEMS")
    logger.info("="*80)
    
    # Get all Azure ecosystems
    azure_ecosystems = get_azure_ecosystems()
    logger.info(f"Found {len(azure_ecosystems)} Azure ecosystems")
    
    if not azure_ecosystems:
        logger.warning("No Azure ecosystems found!")
        return
    
    # Show which ecosystems will be updated
    logger.info("\nEcosystems to update:")
    for eco in azure_ecosystems:
        current_logo = eco.get('logo_url') or eco.get('logo_data')
        has_logo = "✅" if current_logo else "❌"
        logger.info(f"  {has_logo} {eco['name']}")
    
    # Confirm
    print("\n" + "="*80)
    print(f"This will update {len(azure_ecosystems)} ecosystems with the Azure logo.")
    print("Logo URL:", AZURE_LOGO_URL)
    print("="*80)
    
    response = input("\nProceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        logger.info("Cancelled by user")
        return
    
    # Update all ecosystems
    logger.info("\nUpdating ecosystems...")
    successful = 0
    failed = 0
    
    for eco in azure_ecosystems:
        logger.info(f"Updating {eco['name']}...")
        if update_ecosystem_logo(eco['id'], AZURE_LOGO_URL):
            successful += 1
            logger.success(f"  ✅ Updated {eco['name']}")
        else:
            failed += 1
            logger.error(f"  ❌ Failed {eco['name']}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total: {len(azure_ecosystems)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    if successful > 0:
        logger.success(f"\n✅ Successfully updated {successful} Azure ecosystems with logo!")
    
    if failed > 0:
        logger.warning(f"\n⚠️  {failed} ecosystems failed to update")


if __name__ == "__main__":
    main()
