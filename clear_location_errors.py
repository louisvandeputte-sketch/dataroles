#!/usr/bin/env python3
"""Clear location enrichment errors to allow auto-retry."""

from database.client import db
from datetime import datetime, timedelta

print("🔧 Clearing Location Enrichment Errors")
print("=" * 80)

# Get locations with quota errors that are older than 1 day
# (assuming quota might have reset)
one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()

result = db.client.table("locations")\
    .select("id, city, ai_enrichment_error, ai_enriched_at")\
    .not_.is_("ai_enrichment_error", "null")\
    .lt("ai_enriched_at", one_day_ago)\
    .execute()

if result.data:
    print(f"\n📊 Found {len(result.data)} locations with old errors (>1 day)")
    
    quota_errors = [loc for loc in result.data if "quota" in loc.get("ai_enrichment_error", "").lower()]
    
    if quota_errors:
        print(f"   {len(quota_errors)} are quota-related errors")
        print("\n🔄 Clearing errors to allow auto-retry...")
        
        for location in quota_errors:
            city = location.get("city")
            
            # Clear the error
            db.client.table("locations")\
                .update({
                    "ai_enrichment_error": None,
                    "ai_enriched": False
                })\
                .eq("id", location.get("id"))\
                .execute()
            
            print(f"   ✅ Cleared error for: {city}")
        
        print(f"\n✅ Cleared {len(quota_errors)} location errors")
        print("   Auto-enrichment service will retry these locations automatically")
        print("   (every 60 seconds, 10 at a time)")
    else:
        print("   No quota-related errors found")
else:
    print("✅ No old errors found")

print("\n" + "=" * 80)
