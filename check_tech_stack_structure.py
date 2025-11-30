#!/usr/bin/env python3
"""Check current tech stack data structure"""

from database.client import db
import json

# Get a sample job with tech stack
result = db.client.table("vw_job_listings")\
    .select("job_posting_id, title, must_have_programmeertalen, nice_to_have_programmeertalen, must_have_ecosystemen, nice_to_have_ecosystemen")\
    .not_.is_("must_have_programmeertalen", "null")\
    .limit(3)\
    .execute()

print("\n📊 Current Tech Stack Structure in vw_job_listings:\n")

for job in result.data:
    print(f"Job: {job['title'][:60]}")
    print(f"   Must-have languages: {job.get('must_have_programmeertalen')}")
    print(f"   Nice-to-have languages: {job.get('nice_to_have_programmeertalen')}")
    print(f"   Must-have ecosystems: {job.get('must_have_ecosystemen')}")
    print(f"   Nice-to-have ecosystems: {job.get('nice_to_have_ecosystemen')}")
    print()

# Check programming_languages table
print("\n📊 Programming Languages Table Sample:\n")
langs = db.client.table("programming_languages")\
    .select("name, display_name, logo_url")\
    .limit(5)\
    .execute()

for lang in langs.data:
    print(f"   {lang['name']}: logo_url = {lang.get('logo_url')}")

# Check ecosystems table
print("\n📊 Ecosystems Table Sample:\n")
ecos = db.client.table("ecosystems")\
    .select("name, display_name, logo_url")\
    .limit(5)\
    .execute()

for eco in ecos.data:
    print(f"   {eco['name']}: logo_url = {eco.get('logo_url')}")

# Count total
lang_count = db.client.table("programming_languages").select("id", count="exact").execute()
eco_count = db.client.table("ecosystems").select("id", count="exact").execute()

print(f"\n📊 Totals:")
print(f"   Programming languages: {lang_count.count}")
print(f"   Ecosystems: {eco_count.count}")
