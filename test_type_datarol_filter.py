#!/usr/bin/env python3
"""
Test script for type_datarol filtering
Tests the new filter parameter in database client and API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.client import DatabaseClient

def test_type_datarol_filter():
    """Test filtering jobs by type_datarol"""
    
    print("🧪 Testing type_datarol filter\n")
    print("=" * 60)
    
    db = DatabaseClient()
    
    # Test 1: Get all data role types
    print("\n📊 Test 1: Available data role types")
    print("-" * 60)
    
    result = db.client.table("llm_enrichment")\
        .select("type_datarol", count="exact")\
        .not_.is_("type_datarol", "null")\
        .execute()
    
    # Count by type
    type_counts = {}
    for row in result.data:
        role_type = row.get("type_datarol")
        if role_type:
            type_counts[role_type] = type_counts.get(role_type, 0) + 1
    
    print(f"\nTotal enriched jobs: {result.count}")
    print("\nBreakdown by type:")
    for role_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {role_type:20s}: {count:4d} jobs")
    
    # Test 2: Filter by Data Engineer
    print("\n\n🔍 Test 2: Filter by 'Data Engineer'")
    print("-" * 60)
    
    jobs, total = db.search_jobs(
        type_datarol="Data Engineer",
        limit=5
    )
    
    print(f"\nFound {total} Data Engineer jobs")
    print(f"Showing first {len(jobs)} jobs:\n")
    
    for i, job in enumerate(jobs, 1):
        enrichment = job.get("llm_enrichment", {})
        if isinstance(enrichment, list) and len(enrichment) > 0:
            enrichment = enrichment[0]
        
        print(f"{i}. {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('companies', {}).get('name', 'N/A')}")
        print(f"   Type: {enrichment.get('type_datarol', 'N/A')}")
        print(f"   Seniority: {enrichment.get('seniority', 'N/A')}")
        print()
    
    # Test 3: Filter by Data Analyst
    print("\n🔍 Test 3: Filter by 'Data Analyst'")
    print("-" * 60)
    
    jobs, total = db.search_jobs(
        type_datarol="Data Analyst",
        limit=5
    )
    
    print(f"\nFound {total} Data Analyst jobs")
    print(f"Showing first {len(jobs)} jobs:\n")
    
    for i, job in enumerate(jobs, 1):
        enrichment = job.get("llm_enrichment", {})
        if isinstance(enrichment, list) and len(enrichment) > 0:
            enrichment = enrichment[0]
        
        print(f"{i}. {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('companies', {}).get('name', 'N/A')}")
        print(f"   Type: {enrichment.get('type_datarol', 'N/A')}")
        print()
    
    # Test 4: Combine with other filters
    print("\n🔍 Test 4: Combine type_datarol with title_classification")
    print("-" * 60)
    
    jobs, total = db.search_jobs(
        type_datarol="Data Scientist",
        title_classification="Data",
        limit=3
    )
    
    print(f"\nFound {total} Data Scientist jobs (title_classification=Data)")
    print(f"Showing first {len(jobs)} jobs:\n")
    
    for i, job in enumerate(jobs, 1):
        enrichment = job.get("llm_enrichment", {})
        if isinstance(enrichment, list) and len(enrichment) > 0:
            enrichment = enrichment[0]
        
        print(f"{i}. {job.get('title', 'N/A')}")
        print(f"   Classification: {job.get('title_classification', 'N/A')}")
        print(f"   Type: {enrichment.get('type_datarol', 'N/A')}")
        print()
    
    # Test 5: Check index usage (performance)
    print("\n⚡ Test 5: Index usage check")
    print("-" * 60)
    
    # Direct SQL query to check explain plan
    result = db.client.rpc("explain_query", {
        "query_text": """
        SELECT COUNT(*) 
        FROM llm_enrichment 
        WHERE type_datarol = 'Data Engineer'
        """
    }).execute()
    
    print("\nQuery plan (should use idx_llm_type_datarol):")
    if result.data:
        for line in result.data:
            print(f"  {line}")
    else:
        print("  ℹ️  RPC function not available (expected in production)")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\n💡 Frontend can now use: /api/jobs/?type_datarol=Data Engineer")
    print("   Available types:", ", ".join(sorted(type_counts.keys())))

if __name__ == "__main__":
    test_type_datarol_filter()
