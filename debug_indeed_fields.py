"""Debug script to show what fields Bright Data Actually returns."""

# Common field name mismatches between Bright Data and our model:

EXPECTED_FIELD_MAPPINGS = {
    # Our model field -> Bright Data API field
    "jobid": "job_id",  # ✅ Fixed
    "job_title": "job_title",  # Probably correct
    "company_name": "company_name",  # Might be "company"
    "location": "location",  # Probably correct
    "url": "url",  # Might be "job_url" or "link"
    "description_text": "description_text",  # Might be "description"
}

print("=" * 70)
print("INDEED FIELD NAME DEBUGGING")
print("=" * 70)

print("\n🔍 Common field name mismatches:\n")

for our_field, bd_field in EXPECTED_FIELD_MAPPINGS.items():
    if our_field == bd_field:
        print(f"   ✅ {our_field:20} → {bd_field}")
    else:
        print(f"   ⚠️  {our_field:20} → {bd_field} (DIFFERENT!)")

print("\n" + "=" * 70)
print("\n💡 To fix field name mismatches:")
print("   1. Add Field(alias='actual_name') to the field")
print("   2. Make sure Config.populate_by_name = True")
print("\n   Example:")
print("   company_name: str = Field(alias='company')")
print("\n" + "=" * 70)

print("\n📋 Possible field names from Bright Data Indeed API:")
print("\n   Job ID:")
print("      - job_id ✅ (fixed)")
print("      - id")
print("      - jobkey")
print("\n   Title:")
print("      - job_title")
print("      - title")
print("      - position")
print("\n   Company:")
print("      - company_name")
print("      - company")
print("      - employer")
print("\n   Location:")
print("      - location")
print("      - job_location")
print("      - formattedLocation")
print("\n   URL:")
print("      - url")
print("      - job_url")
print("      - link")
print("      - viewJobUrl")
print("\n   Description:")
print("      - description_text")
print("      - description")
print("      - snippet")
print("      - summary")

print("\n" + "=" * 70)
print("\n🔧 Next steps:")
print("   1. Run the SQL query to see the actual error")
print("   2. Identify which field is missing")
print("   3. Add the correct alias or make it optional")
print("=" * 70)
