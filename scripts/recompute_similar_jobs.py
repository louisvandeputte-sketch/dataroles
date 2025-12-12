#!/usr/bin/env python3
"""Recompute similar job IDs either for all jobs or a subset."""

import argparse
import sys
from pathlib import Path
from typing import List

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.similar_jobs import get_similar_jobs_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recompute similar job IDs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Recompute for all active jobs")
    group.add_argument("--job-ids", nargs="+", help="Specific job IDs to recompute")
    parser.add_argument("--dry-run", action="store_true", help="Compute only, do not persist")
    parser.add_argument("--min-score", type=float, default=None, help="Override default min score")
    parser.add_argument("--limit", type=int, default=None, help="Override default max matches")
    return parser.parse_args()


def recompute_for_job_ids(job_ids: List[str], dry_run: bool = False, min_score=None, limit=None):
    service = get_similar_jobs_service()
    contexts = service.load_job_contexts_by_ids(job_ids)
    if not contexts:
        logger.warning("No job contexts found for given IDs")
        return

    mapping = service.recompute_for_contexts(
        contexts, persist=not dry_run, min_score=min_score, limit=limit
    )

    for job_id, similar_ids in mapping.items():
        logger.info(f"{job_id} -> {similar_ids}")


def main():
    args = parse_args()
    service = get_similar_jobs_service()

    if args.all:
        count, duration = service.recompute_all_active_jobs(persist=not args.dry_run)
        logger.success(f"Processed {count} jobs in {duration:.2f}s")
    else:
        recompute_for_job_ids(
            args.job_ids,
            dry_run=args.dry_run,
            min_score=args.min_score,
            limit=args.limit,
        )


if __name__ == "__main__":
    main()

