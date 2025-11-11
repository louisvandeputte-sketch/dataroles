#!/usr/bin/env python3
"""Monitor enrichment progress in real-time."""

import time
from database.client import db
from datetime import datetime

def get_stats():
    """Get current enrichment stats."""
    # Total Data jobs
    total = db.client.table('job_postings')\
        .select('id', count='exact')\
        .eq('title_classification', 'Data')\
        .execute()
    
    # Enriched
    enriched = db.client.table('llm_enrichment')\
        .select('job_posting_id', count='exact')\
        .not_.is_('enrichment_completed_at', 'null')\
        .execute()
    
    # Errors
    errors = db.client.table('llm_enrichment')\
        .select('job_posting_id', count='exact')\
        .not_.is_('enrichment_error', 'null')\
        .execute()
    
    return {
        'total': total.count,
        'enriched': enriched.count,
        'errors': errors.count,
        'unenriched': total.count - enriched.count - errors.count
    }

print("Enrichment Progress Monitor")
print("=" * 80)
print("Press Ctrl+C to stop\n")

prev_enriched = 0
start_time = datetime.now()

try:
    while True:
        stats = get_stats()
        
        # Calculate rate
        if prev_enriched > 0:
            new_enriched = stats['enriched'] - prev_enriched
            rate_info = f" (+{new_enriched} since last check)"
        else:
            rate_info = ""
        
        prev_enriched = stats['enriched']
        
        # Display
        elapsed = (datetime.now() - start_time).total_seconds()
        progress_pct = (stats['enriched'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Enriched: {stats['enriched']}/{stats['total']} ({progress_pct:.1f}%) | "
              f"Errors: {stats['errors']} | "
              f"Remaining: {stats['unenriched']}{rate_info}",
              end='', flush=True)
        
        time.sleep(5)  # Check every 5 seconds
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
    final_stats = get_stats()
    print(f"\nFinal stats:")
    print(f"  Total: {final_stats['total']}")
    print(f"  Enriched: {final_stats['enriched']} ({final_stats['enriched']/final_stats['total']*100:.1f}%)")
    print(f"  Errors: {final_stats['errors']}")
    print(f"  Remaining: {final_stats['unenriched']}")
