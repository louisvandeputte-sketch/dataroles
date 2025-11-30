#!/usr/bin/env python3
"""Test logo URLs after migration 075"""

from database.client import db

print("\n🧪 Testing logo URLs after migration 075...\n")

# First, let's check which languages have logo_data
langs_with_logos = db.client.table("programming_languages")\
    .select("id, name, logo_data")\
    .not_.is_("logo_data", "null")\
    .limit(5)\
    .execute()

print(f"📊 Found {len(langs_with_logos.data)} languages with logo_data\n")

if langs_with_logos.data:
    print("Expected URLs after migration 075:")
    for lang in langs_with_logos.data:
        expected_url = f"/api/programming-languages/{lang['id']}/logo"
        print(f"   {lang['name']:20} -> {expected_url}")

print("\n" + "="*80)
print("⚠️  TO APPLY THIS FIX:")
print("="*80)
print("\n1. Run migration 075 in Supabase SQL Editor:")
print("   /database/migrations/075_fix_tech_stack_lookup_logo_urls.sql")
print("\n2. After migration, test with:")
print("   SELECT name, logo_url FROM tech_stack_lookup WHERE logo_url IS NOT NULL LIMIT 10;")
print("\n3. Frontend will automatically pick up the new URLs!")
print("\n" + "="*80)
