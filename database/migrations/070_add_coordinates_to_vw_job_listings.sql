-- Migration 070: Add geographic coordinates to vw_job_listings
-- Date: 2025-11-28
-- Description: Add longitude/latitude from locations table to job listings view for map visualization

DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    
    -- Job info from job_postings (for convenience)
    j.title,                   -- Job title
    j.posted_date,             -- Job posting date (from platform)
    j.ranking_position,        -- Ranking position (1 = best)
    j.base_score,              -- Base score (stable, nightly calculation)
    j.ranking_score,           -- Final score (base × hourly_multiplier, hourly)
    j.hourly_multiplier,       -- Hourly random multiplier (0.8-1.2)
    j.ranking_metadata,        -- Score breakdown (F/Q/T/R scores)
    j.title_classification,    -- Title classification (Data, NIS, Other)
    
    -- First seen date (earliest scrape from any source)
    js.first_seen_at,          -- When job was first scraped (may differ from posted_date)
    
    -- Corrected posted date (minimum of first_seen_at and posted_date)
    LEAST(js.first_seen_at, j.posted_date) AS posted_date_corrected,  -- Most accurate job age
    
    -- Company info from companies (for convenience)
    c.logo_url,                -- Company logo URL
    c.name AS company_name,    -- Company name
    
    -- Company sector (multilingual) from company_master_data
    cmd.sector_nl,             -- Company sector in Dutch
    cmd.sector_en,             -- Company sector in English
    cmd.sector_fr,             -- Company sector in French
    
    -- Company size category (multilingual) from company_master_data
    cmd.size_category,         -- Size category enum (startup, scaleup, sme, etc.)
    cmd.category_nl,           -- Category in Dutch (startup, scaleup, kmo, etc.)
    cmd.category_en,           -- Category in English (startup, scaleup, sme, etc.)
    cmd.category_fr,           -- Category in French (startup, scaleup, pme, etc.)
    cmd.size_summary_nl,       -- Dutch size summary
    cmd.size_summary_en,       -- English size summary
    cmd.size_summary_fr,       -- French size summary
    cmd.size_confidence,       -- Confidence score for size classification
    
    -- Additional company metadata
    cmd.aantal_werknemers,     -- Number of employees
    cmd.founded_year,          -- Company founding year
    cmd.industry,              -- Industry (from original data)
    
    -- Location info (multilingual) - WITH OVERRIDE SUPPORT
    COALESCE(j.location_id_override, j.location_id) AS location_id,
    
    -- City names (multilingual)
    l.city_name_nl,            -- City name in Dutch (e.g., "Brussel")
    l.city_name_en,            -- City name in English (e.g., "Brussels")
    l.city_name_fr,            -- City name in French (e.g., "Bruxelles")
    
    -- Subdivision/Region names (multilingual)
    l.subdivision_name_nl,     -- Province/region in Dutch (e.g., "Vlaams-Brabant")
    l.subdivision_name_en,     -- Province/region in English (e.g., "Flemish Brabant")
    l.subdivision_name_fr,     -- Province/region in French (e.g., "Brabant flamand")
    
    -- Country names (multilingual)
    l.country_name_nl,         -- Country in Dutch (e.g., "België")
    l.country_name_en,         -- Country in English (e.g., "Belgium")
    l.country_name_fr,         -- Country in French (e.g., "Belgique")
    
    -- Geographic coordinates (for map visualization)
    l.longitude,               -- Longitude coordinate (WGS84, -180 to 180)
    l.latitude,                -- Latitude coordinate (WGS84, -90 to 90)
    
    -- Additional location metadata
    l.country_code_3,          -- ISO 3166-1 alpha-3 country code (e.g., "BEL")
    l.timezone,                -- IANA timezone (e.g., "Europe/Brussels")
    l.city_official_name,      -- Official city name (AI enriched)
    l.country_name,            -- Country name in local language (AI enriched)
    
    -- Core classification fields (ACTIVE - used for filtering)
    e.type_datarol,            -- Data role type (Data Engineer, Data Analyst, etc.)
    e.rolniveau,               -- Role level array (Technical, Lead, Managerial)
    e.seniority,               -- Seniority array (Junior, Medior, Senior, Expert)
    e.contract,                -- Contract type array (Permanent, Freelance, Intern)
    e.sourcing_type,           -- Sourcing type (Direct, Agency)
    
    -- Multilingual labels (ACTIVE - contains all translations + section headers)
    e.labels,                  -- JSONB with NL/EN/FR translations for all fields + section headers
    
    -- Short summaries in 3 languages (ACTIVE)
    e.samenvatting_kort_en,
    e.samenvatting_kort_nl,
    e.samenvatting_kort_fr,
    
    -- Legacy short summary field (ACTIVE - for backward compatibility)
    e.samenvatting_kort,       -- Legacy: English summary
    
    -- DEPRECATED: Long summaries (no longer populated in v20, kept for backwards compatibility)
    e.samenvatting_lang_en,
    e.samenvatting_lang_nl,
    e.samenvatting_lang_fr,
    e.samenvatting_lang,       -- Legacy: English summary
    
    -- NEW: Structured sections in 3 languages (v20)
    e.responsibilities,        -- Array of responsibility bullets (EN)
    e.responsibilities_nl,     -- Array of responsibility bullets (NL)
    e.responsibilities_fr,     -- Array of responsibility bullets (FR)
    e.requirements,            -- Array of requirement bullets (EN)
    e.requirements_nl,         -- Array of requirement bullets (NL)
    e.requirements_fr,         -- Array of requirement bullets (FR)
    e.offerings,               -- Array of offering bullets (EN)
    e.offerings_nl,            -- Array of offering bullets (NL)
    e.offerings_fr,            -- Array of offering bullets (FR)
    
    -- Tech stack (ACTIVE)
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    
    -- Spoken/written languages (ACTIVE)
    e.must_have_talen,
    e.nice_to_have_talen,
    
    -- Metadata (ACTIVE)
    e.created_at

FROM llm_enrichment e
JOIN job_postings j ON e.job_posting_id = j.id
JOIN companies c ON j.company_id = c.id
LEFT JOIN locations l ON l.id = COALESCE(j.location_id_override, j.location_id)
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN LATERAL (
    -- Get earliest first_seen_at from all sources for this job
    SELECT MIN(first_seen_at) as first_seen_at
    FROM job_sources
    WHERE job_posting_id = j.id
) js ON true
WHERE j.is_active = TRUE
  AND j.title_classification = 'Data';

COMMENT ON VIEW vw_job_listings IS 'View of enriched job listings with structured sections (v20), first_seen_at, and geographic coordinates. Includes responsibilities/requirements/offerings arrays instead of summary_long. Section headers in labels JSONB. first_seen_at shows when job was first scraped. posted_date_corrected is minimum of first_seen_at and posted_date. Coordinates (longitude/latitude) enable map visualization and proximity-based features.';
