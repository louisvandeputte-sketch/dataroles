-- Migration: Add hiring_model filter to vw_mini_job_cards
-- Excludes companies with hiring_model = 'Recruitment' from mini job cards
-- This ensures only direct hiring companies appear in the mini job cards

DROP VIEW IF EXISTS public.vw_mini_job_cards;

CREATE VIEW public.vw_mini_job_cards AS
SELECT
  e.job_posting_id,
  LEAST(js.first_seen_at, j.posted_date) as posted_date_corrected,
  c.logo_url,
  c.name as company_name,
  l.city_name_nl,
  e.type_datarol,
  e.seniority,
  e.rolniveau,
  e.contract,
  e.must_have_ecosystemen,
  e.must_have_programmeertalen,
  e.nice_to_have_ecosystemen,
  e.nice_to_have_programmeertalen,
  j.ranking_score
FROM
  llm_enrichment e
  JOIN job_postings j ON e.job_posting_id = j.id
  JOIN companies c ON j.company_id = c.id
  LEFT JOIN company_master_data cmd ON cmd.company_id = c.id
  LEFT JOIN locations l ON l.id = COALESCE(j.location_id_override, j.location_id)
  LEFT JOIN LATERAL (
    SELECT
      min(job_sources.first_seen_at) as first_seen_at
    FROM
      job_sources
    WHERE
      job_sources.job_posting_id = j.id
  ) js ON true
WHERE
  j.is_active = true
  AND j.title_classification = 'Data'::text
  AND (cmd.hiring_model IS NULL OR cmd.hiring_model != 'Recruitment')
ORDER BY
  j.ranking_score DESC
LIMIT
  8;
