"""Data ingestion, processing, and normalization."""

from ingestion.normalizer import (
    normalize_company,
    normalize_location,
    normalize_job_description,
    validate_url,
    parse_industries
)
from ingestion.deduplicator import (
    check_job_exists,
    fields_have_changed,
    calculate_data_hash,
    should_update_job,
    get_changed_fields
)
from ingestion.processor import (
    ProcessingResult,
    BatchResult,
    process_job_posting,
    process_jobs_batch
)

__all__ = [
    "normalize_company",
    "normalize_location",
    "normalize_job_description",
    "validate_url",
    "parse_industries",
    "check_job_exists",
    "fields_have_changed",
    "calculate_data_hash",
    "should_update_job",
    "get_changed_fields",
    "ProcessingResult",
    "BatchResult",
    "process_job_posting",
    "process_jobs_batch"
]
