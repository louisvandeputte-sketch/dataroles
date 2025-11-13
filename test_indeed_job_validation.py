"""Test Indeed job validation to see what's failing."""

from models.indeed import IndeedJobPosting
from pydantic import ValidationError
import json

# Sample Indeed job data (minimal required fields)
sample_job = {
    "jobid": "test123",
    "job_title": "BI Developer",
    "company_name": "Test Company",
    "location": "Belgium",
    "url": "https://be.indeed.com/viewjob?jk=test123",
    "description_text": "Test description"
}

print("Testing Indeed job validation...\n")
print("=" * 60)

# Test 1: Valid job
print("\n1. Testing VALID job:")
print(json.dumps(sample_job, indent=2))
try:
    job = IndeedJobPosting(**sample_job)
    print("✅ Validation PASSED")
except ValidationError as e:
    print(f"❌ Validation FAILED: {e}")

# Test 2: Missing required field
print("\n" + "=" * 60)
print("\n2. Testing job with MISSING job_title:")
invalid_job = sample_job.copy()
del invalid_job["job_title"]
print(json.dumps(invalid_job, indent=2))
try:
    job = IndeedJobPosting(**invalid_job)
    print("✅ Validation PASSED")
except ValidationError as e:
    print(f"❌ Validation FAILED:")
    for error in e.errors():
        field = error.get('loc', ['unknown'])[0]
        msg = error.get('msg', 'unknown')
        print(f"   Field '{field}': {msg}")

# Test 3: Check what fields are REQUIRED
print("\n" + "=" * 60)
print("\n3. Required fields in IndeedJobPosting model:")
from models.indeed import IndeedJobPosting
import inspect

# Get model fields
model_fields = IndeedJobPosting.model_fields
required_fields = []
optional_fields = []

for field_name, field_info in model_fields.items():
    if field_info.is_required():
        required_fields.append(field_name)
    else:
        optional_fields.append(field_name)

print(f"\n✅ REQUIRED fields ({len(required_fields)}):")
for field in sorted(required_fields):
    print(f"   - {field}")

print(f"\n⚪ OPTIONAL fields ({len(optional_fields)}):")
for field in sorted(optional_fields):
    print(f"   - {field}")

print("\n" + "=" * 60)
print("\nIf a job from Bright Data is missing ANY of the required fields,")
print("it will fail validation and show up in jobs_error.")
print("\nTo fix: Make more fields optional in models/indeed.py")
