#!/usr/bin/env python3
"""Check how logos are stored in the database"""

from database.client import db

print("\n🔍 Checking logo storage in database...\n")

# Check programming_languages
print("📊 Programming Languages:")
langs = db.client.table("programming_languages")\
    .select("id, name, logo_url, logo_data, logo_filename")\
    .limit(5)\
    .execute()

for lang in langs.data:
    has_data = lang.get('logo_data') is not None
    has_url = lang.get('logo_url') is not None
    print(f"   {lang['name']:20} | logo_url: {str(has_url):5} | logo_data: {str(has_data):5} | filename: {lang.get('logo_filename')}")

# Check ecosystems
print("\n📊 Ecosystems:")
ecos = db.client.table("ecosystems")\
    .select("id, name, logo_url, logo_data, logo_filename")\
    .limit(5)\
    .execute()

for eco in ecos.data:
    has_data = eco.get('logo_data') is not None
    has_url = eco.get('logo_url') is not None
    print(f"   {eco['name']:20} | logo_url: {str(has_url):5} | logo_data: {str(has_data):5} | filename: {eco.get('logo_filename')}")

# Check if any have logo_data but no logo_url
print("\n🔍 Items with logo_data but no logo_url:")

langs_with_data = db.client.table("programming_languages")\
    .select("id, name")\
    .not_.is_("logo_data", "null")\
    .is_("logo_url", "null")\
    .execute()

ecos_with_data = db.client.table("ecosystems")\
    .select("id, name")\
    .not_.is_("logo_data", "null")\
    .is_("logo_url", "null")\
    .execute()

print(f"   Languages: {len(langs_with_data.data)}")
print(f"   Ecosystems: {len(ecos_with_data.data)}")

if langs_with_data.data or ecos_with_data.data:
    print("\n   ⚠️ These items have logo_data but logo_url is NULL!")
    print("   ⚠️ The view will return NULL for logo_url even though logos exist!")
