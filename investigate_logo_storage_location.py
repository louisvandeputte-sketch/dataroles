#!/usr/bin/env python3
"""Investigate where logos are stored for the admin UI table"""

from database.client import db
import json

print("\n🔍 Investigating logo storage for DAX...\n")

# Get DAX full record
dax = db.client.table("programming_languages")\
    .select("*")\
    .eq("name", "DAX")\
    .single()\
    .execute()

print("📊 DAX Full Record:")
print("="*80)
for key, value in dax.data.items():
    if key == 'logo_data':
        if value:
            print(f"   {key:25} : EXISTS (type: {type(value).__name__})")
            if isinstance(value, str):
                print(f"   {' '*25}   Length: {len(value)} chars")
                print(f"   {' '*25}   First 100 chars: {value[:100]}...")
        else:
            print(f"   {key:25} : NULL")
    else:
        print(f"   {key:25} : {value}")

print("\n" + "="*80)
print("🔍 How Admin UI Shows Logos:")
print("="*80)

# Check if there's a logo_url or if it's generated dynamically
if dax.data.get('logo_url'):
    print(f"\n✅ Static logo_url exists:")
    print(f"   {dax.data['logo_url']}")
elif dax.data.get('logo_data'):
    print(f"\n✅ Logo stored in logo_data (bytea)")
    print(f"   Admin UI generates URL: /api/programming-languages/{dax.data['id']}/logo")
    print(f"   This endpoint serves the logo from logo_data column")
else:
    print(f"\n❌ No logo found!")

print("\n" + "="*80)
print("🎯 Where Logo is Actually Stored:")
print("="*80)

print(f"""
For DAX (and other languages with logos in the admin UI):

1. 📦 Storage Location:
   - Database: Supabase PostgreSQL
   - Table: programming_languages
   - Column: logo_data (type: BYTEA)
   - Size: {len(dax.data.get('logo_data', '')) if dax.data.get('logo_data') else 0} bytes

2. 🔗 How Admin UI Displays It:
   - Admin UI calls: GET /api/programming-languages/{dax.data['id']}/logo
   - FastAPI endpoint reads logo_data from database
   - Converts BYTEA to image bytes
   - Returns as image/png with proper headers

3. 🌐 Full URL in Admin UI:
   - Relative: /api/programming-languages/{dax.data['id']}/logo
   - Absolute: http://localhost:8000/api/programming-languages/{dax.data['id']}/logo
   - Or: https://your-backend-domain.com/api/programming-languages/{dax.data['id']}/logo

4. ⚠️ Why Frontend Can't See It:
   - Frontend fetches tech_stack_lookup view
   - View returns: logo_url = "/api/programming-languages/{dax.data['id']}/logo"
   - This is a RELATIVE URL pointing to FastAPI backend
   - Frontend needs to know where FastAPI backend is!

5. ✅ Solution:
   - Option A: Add LOGO_API_BASE_URL to make URLs absolute
   - Option B: Migrate logos to Supabase Storage (better long-term)
""")

print("="*80)
print("🧪 Test the Logo Endpoint:")
print("="*80)
print(f"""
# If backend is running on localhost:8000:
curl http://localhost:8000/api/programming-languages/{dax.data['id']}/logo --output dax-test.png
open dax-test.png

# If backend is running on production:
curl https://your-backend-domain.com/api/programming-languages/{dax.data['id']}/logo --output dax-test.png
open dax-test.png
""")

# Check a few more languages to see the pattern
print("="*80)
print("📊 Other Languages with Logos:")
print("="*80)

other_langs = db.client.table("programming_languages")\
    .select("id, name, logo_data, logo_url")\
    .not_.is_("logo_data", "null")\
    .limit(5)\
    .execute()

for lang in other_langs.data:
    has_data = lang.get('logo_data') is not None
    has_url = lang.get('logo_url') is not None
    print(f"   {lang['name']:20} | logo_data: {str(has_data):5} | logo_url: {str(has_url):5}")
    if has_data:
        print(f"   {' '*20}   → Served via: /api/programming-languages/{lang['id']}/logo")
