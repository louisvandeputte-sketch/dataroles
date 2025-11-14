#!/usr/bin/env python3
"""Test ranking directly"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from ranking.job_ranker import calculate_and_save_rankings

print("Starting ranking test...")
try:
    result = calculate_and_save_rankings()
    print(f"✅ Success! Ranked {result} jobs")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
