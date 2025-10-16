#!/usr/bin/env python3
"""Debug import issue with specific LinkedIn IDs."""

from database.client import get_supabase_client
import csv
import io

client = get_supabase_client()

# Simulate the CSV data from the screenshot
csv_data = """LinkedIn Company ID,Company Name,Company Number (KBO/VAT),Description,Industry,Employee Count,Revenue (EUR),Growth Trend,Jobs Page URL,Contact Email,Verified
48256,'s Heeren Loo,,Test,,,,,,,No
76595890,4CEE,,,,,,,,No
500621,4PS,,,,,,,,No
481244,9altitudes Belgium,,,,,,,,No
5004290,A&T Prefab,,,,,,,,No
12009057,aaff,,,,,,,,No"""

print("Testing CSV import with your data...\n")
print("=" * 80)

# Parse CSV
csv_reader = csv.reader(io.StringIO(csv_data))
headers = next(csv_reader)

print(f"Headers: {headers}\n")

for row_num, row in enumerate(csv_reader, start=2):
    linkedin_id = row[0].strip() if row[0] else ''
    company_name = row[1] if len(row) > 1 else 'Unknown'
    
    # Convert to string and remove decimal points
    linkedin_id = str(linkedin_id).split('.')[0]
    
    print(f"Row {row_num}: Checking LinkedIn ID '{linkedin_id}' ({company_name})")
    
    # Try to find in database
    result = client.table("companies")\
        .select("id, name, linkedin_company_id")\
        .eq("linkedin_company_id", linkedin_id)\
        .execute()
    
    if result.data:
        print(f"  ✓ FOUND: {result.data[0]['name']}")
    else:
        print(f"  ✗ NOT FOUND in database")
        
        # Try to find similar IDs
        print(f"  Searching for similar IDs...")
        
        # Search with LIKE
        similar = client.table("companies")\
            .select("id, name, linkedin_company_id")\
            .ilike("linkedin_company_id", f"%{linkedin_id}%")\
            .limit(3)\
            .execute()
        
        if similar.data:
            print(f"  Similar IDs found:")
            for s in similar.data:
                print(f"    - {s['linkedin_company_id']} -> {s['name']}")
        else:
            print(f"  No similar IDs found")
    
    print()

print("=" * 80)
