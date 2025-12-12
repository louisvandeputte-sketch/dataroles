"""Service for computing and persisting similar jobs recommendations.

Centralizes the logic for:
    1. Loading the contextual attributes that define similarity between jobs
       (skills, role type, region, contract)
    2. Scoring pairs of jobs using weighted components
    3. Writing the resulting top candidates back to the ``job_postings`` table

This module can be reused by a nightly scheduler as well as ad-hoc CLI scripts.
The actual scheduler/CLI wrappers will live elsewhere; this file purely focuses on
data fetching, scoring, and persistence helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from loguru import logger

from database.client import db


# ==================== CONFIGURATION ====================


DEFAULT_REQUIREMENT_WEIGHT = 0.5
REQUIREMENT_LEVEL_WEIGHTS: Dict[str, float] = {
    "must": 1.0,
    "must_have": 1.0,
    "required": 1.0,
    "preferred": 0.5,
    "nice": 0.5,
    "nice_to_have": 0.5,
    "optional": 0.3,
}


@dataclass(frozen=True)
class SimilarityConfig:
    """Runtime configuration for similarity scoring."""

    skill_weight: float = 0.40
    role_weight: float = 0.30
    region_weight: float = 0.15
    contract_weight: float = 0.15
    min_score: float = 0.20
    limit: int = 10
    batch_size: int = 250

    def __post_init__(self):  # type: ignore[misc]
        total = self.skill_weight + self.role_weight + self.region_weight + self.contract_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                "Similarity weights must sum to 1.0 "
                f"(got {total:.2f}). Adjust SimilarityConfig."
            )


@dataclass
class JobContext:
    """Normalized view of the job attributes needed for similarity checks."""

    id: str
    title: Optional[str]
    type_datarol: Optional[str]
    region: Optional[str]
    country_code: Optional[str]
    contract: Optional[str]
    employment_type: Optional[str]
    languages: Dict[str, float] = field(default_factory=dict)
    ecosystems: Dict[str, float] = field(default_factory=dict)

    def skill_map(self) -> Dict[str, float]:
        """Return a combined skill dictionary for weighted overlap calculations."""

        combined: Dict[str, float] = {}

        for name, weight in self.languages.items():
            if not name:
                continue
            key = f"lang::{name.lower()}"
            combined[key] = max(weight, combined.get(key, 0.0))

        for name, weight in self.ecosystems.items():
            if not name:
                continue
            key = f"eco::{name.lower()}"
            combined[key] = max(weight, combined.get(key, 0.0))

        return combined


@dataclass
class SimilarityBreakdown:
    """Debug information per similarity match."""

    skill: float
    role: float
    region: float
    contract: float

    @property
    def total(self) -> float:
        return self.skill + self.role + self.region + self.contract


@dataclass
class SimilarJobResult:
    job_id: str
    score: float
    breakdown: SimilarityBreakdown


# ==================== SERVICE ====================


class SimilarJobsService:
    """Loads job contexts, scores similar jobs, and persists results."""

    SELECT_FIELDS = (
        "id, title, employment_type, title_classification, "
        "locations!job_postings_location_id_fkey(subdivision_name_en, country_code), "
        "llm_enrichment(type_datarol, contract, rolniveau), "
        "job_programming_languages(requirement_level, programming_languages(name)), "
        "job_ecosystems(requirement_level, ecosystems(name))"
    )

    def __init__(self, config: Optional[SimilarityConfig] = None):
        self.config = config or SimilarityConfig()

    # -------- Job loading --------

    def iter_active_job_contexts(self) -> Iterator[List[JobContext]]:
        """Yield active jobs in batches as :class:`JobContext` objects."""

        offset = 0
        batch_size = self.config.batch_size

        while True:
            query = (
                db.client.table("job_postings")
                .select(self.SELECT_FIELDS)
                .eq("is_active", True)
                .order("posted_date", desc=True)
                .range(offset, offset + batch_size - 1)
            )

            result = query.execute()
            rows = result.data or []
            if not rows:
                break

            contexts = [self._hydrate_job_context(row) for row in rows]
            logger.debug(f"Loaded {len(contexts)} job contexts (offset={offset}).")
            yield contexts

            if len(rows) < batch_size:
                break
            offset += batch_size

    def load_all_active_job_contexts(self) -> List[JobContext]:
        """Load all active job contexts into memory."""

        contexts: List[JobContext] = []
        for batch in self.iter_active_job_contexts():
            contexts.extend(batch)
        return contexts

    def load_job_contexts_by_ids(self, job_ids: Sequence[str]) -> List[JobContext]:
        """Load contexts for a specific set of job IDs."""

        ids = [jid for jid in job_ids if jid]
        if not ids:
            return []

        contexts: List[JobContext] = []
        chunk_size = self.config.batch_size
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i:i + chunk_size]
            result = (
                db.client.table("job_postings")
                .select(self.SELECT_FIELDS)
                .in_("id", chunk)
                .execute()
            )
            rows = result.data or []
            contexts.extend(self._hydrate_job_context(row) for row in rows)

        return contexts

    def _hydrate_job_context(self, row: Dict[str, Any]) -> JobContext:
        location = row.get("locations") or {}
        enrichment = row.get("llm_enrichment") or {}

        languages = self._extract_weighted_skills(row.get("job_programming_languages") or [], "programming_languages")
        ecosystems = self._extract_weighted_skills(row.get("job_ecosystems") or [], "ecosystems")

        contract = enrichment.get("contract") or row.get("employment_type")

        return JobContext(
            id=row["id"],
            title=row.get("title"),
            type_datarol=enrichment.get("type_datarol") or row.get("title_classification"),
            region=location.get("subdivision_name_en"),
            country_code=location.get("country_code"),
            contract=contract,
            employment_type=row.get("employment_type"),
            languages=languages,
            ecosystems=ecosystems,
        )

    def _extract_weighted_skills(self, assignments: Sequence[Dict[str, Any]], nested_key: str) -> Dict[str, float]:
        weighted: Dict[str, float] = {}

        for assignment in assignments:
            obj = assignment.get(nested_key) or {}
            name = obj.get("name")
            if not name:
                continue

            level = (assignment.get("requirement_level") or "").lower()
            weight = REQUIREMENT_LEVEL_WEIGHTS.get(level, DEFAULT_REQUIREMENT_WEIGHT)

            key = name.lower()
            weighted[key] = max(weight, weighted.get(key, 0.0))

        return weighted

    # -------- Similarity scoring --------

    def compute_similarity(self, job_a: JobContext, job_b: JobContext) -> SimilarityBreakdown:
        skill_score = self._weighted_jaccard(job_a.skill_map(), job_b.skill_map()) * self.config.skill_weight
        role_score = self._categorical_match(job_a.type_datarol, job_b.type_datarol) * self.config.role_weight
        region_score = self._region_match(job_a, job_b) * self.config.region_weight
        contract_score = self._categorical_match(
            job_a.contract or job_a.employment_type,
            job_b.contract or job_b.employment_type,
        ) * self.config.contract_weight

        return SimilarityBreakdown(
            skill=skill_score,
            role=role_score,
            region=region_score,
            contract=contract_score,
        )

    def _weighted_jaccard(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0

        keys = set(a.keys()) | set(b.keys())
        intersection = 0.0
        union = 0.0

        for key in keys:
            wa = a.get(key, 0.0)
            wb = b.get(key, 0.0)
            intersection += min(wa, wb)
            union += max(wa, wb)

        if union == 0:
            return 0.0
        return intersection / union

    def _categorical_match(self, a: Optional[str], b: Optional[str]) -> float:
        if not a or not b:
            return 0.0
        if a.lower() == b.lower():
            return 1.0
        return 0.0

    def _region_match(self, job_a: JobContext, job_b: JobContext) -> float:
        if job_a.region and job_b.region and job_a.region.lower() == job_b.region.lower():
            return 1.0
        if job_a.country_code and job_b.country_code and job_a.country_code.lower() == job_b.country_code.lower():
            return 0.5
        return 0.0

    # -------- Ranking helpers --------

    def find_similar_jobs(
        self,
        target: JobContext,
        candidates: Iterable[JobContext],
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[SimilarJobResult]:
        max_items = limit if limit is not None else self.config.limit
        threshold = min_score if min_score is not None else self.config.min_score

        results: List[SimilarJobResult] = []

        for candidate in candidates:
            if candidate.id == target.id:
                continue

            breakdown = self.compute_similarity(target, candidate)
            score = breakdown.total
            if score < threshold:
                continue

            results.append(SimilarJobResult(job_id=candidate.id, score=score, breakdown=breakdown))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:max_items]

    def build_similarity_map(
        self,
        contexts: Sequence[JobContext],
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}

        for job in contexts:
            matches = self.find_similar_jobs(job, contexts, limit=limit, min_score=min_score)
            mapping[job.id] = [match.job_id for match in matches]

        return mapping

    # -------- Persistence --------

    def update_similar_job_ids(self, job_id: str, similar_ids: Sequence[str]) -> None:
        try:
            (
                db.client.table("job_postings")
                .update({"similar_job_ids": list(similar_ids)})
                .eq("id", job_id)
                .execute()
            )
        except Exception as exc:  # pragma: no cover
            logger.error(f"Failed to update similar_job_ids for {job_id}: {exc}")
            raise

    # -------- Batch operations --------

    def recompute_for_contexts(
        self,
        contexts: Sequence[JobContext],
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
        persist: bool = True,
    ) -> Dict[str, List[str]]:
        """Compute (and optionally persist) similar jobs for provided contexts."""

        mapping = self.build_similarity_map(contexts, limit=limit, min_score=min_score)

        if persist:
            for job_id, similar_ids in mapping.items():
                self.update_similar_job_ids(job_id, similar_ids)

        return mapping

    def recompute_all_active_jobs(self, persist: bool = True) -> Tuple[int, float]:
        """Convenience helper for nightly jobs that processes all active jobs.
        
        Loads all active job contexts into memory (lightweight: ~0.5-1MB for 1500 jobs)
        and compares each job against ALL other jobs to find similar matches.
        """

        start = perf_counter()
        
        logger.info("Loading all active job contexts into memory...")
        all_contexts = self.load_all_active_job_contexts()
        total_jobs = len(all_contexts)
        logger.info(f"Loaded {total_jobs} job contexts. Computing similarities...")

        # Compute similarities for all jobs against all candidates
        mapping = self.build_similarity_map(all_contexts)
        
        if persist:
            logger.info(f"Persisting similar_job_ids for {total_jobs} jobs...")
            for job_id, similar_ids in mapping.items():
                self.update_similar_job_ids(job_id, similar_ids)

        duration = perf_counter() - start
        logger.success(f"✅ Similar jobs recomputed for {total_jobs} jobs in {duration:.2f}s")
        return total_jobs, duration


_similar_jobs_service: Optional[SimilarJobsService] = None


def get_similar_jobs_service() -> SimilarJobsService:
    global _similar_jobs_service
    if _similar_jobs_service is None:
        _similar_jobs_service = SimilarJobsService()
    return _similar_jobs_service

