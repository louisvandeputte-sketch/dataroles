-- Migration 079: Add spoken_languages master data table
-- Date: 2025-12-05
-- Description: Create master table for spoken languages with multilingual names

-- Create spoken_languages table
CREATE TABLE IF NOT EXISTS spoken_languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_en TEXT NOT NULL UNIQUE,  -- English name (canonical)
    name_nl TEXT NOT NULL,          -- Dutch name
    name_fr TEXT NOT NULL,          -- French name
    iso_639_1 TEXT,                 -- ISO 639-1 code (2 letters, e.g., 'en', 'nl')
    iso_639_2 TEXT,                 -- ISO 639-2 code (3 letters, e.g., 'eng', 'nld')
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_spoken_languages_name_en ON spoken_languages(name_en);
CREATE INDEX IF NOT EXISTS idx_spoken_languages_name_nl ON spoken_languages(name_nl);
CREATE INDEX IF NOT EXISTS idx_spoken_languages_iso_639_1 ON spoken_languages(iso_639_1);
CREATE INDEX IF NOT EXISTS idx_spoken_languages_active ON spoken_languages(is_active);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_spoken_languages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_spoken_languages_updated_at
    BEFORE UPDATE ON spoken_languages
    FOR EACH ROW
    EXECUTE FUNCTION update_spoken_languages_updated_at();

-- Add comments
COMMENT ON TABLE spoken_languages IS 'Master data for spoken/written languages with multilingual names';
COMMENT ON COLUMN spoken_languages.name_en IS 'English name (canonical, used in llm_enrichment)';
COMMENT ON COLUMN spoken_languages.name_nl IS 'Dutch name for frontend display';
COMMENT ON COLUMN spoken_languages.name_fr IS 'French name for frontend display';
COMMENT ON COLUMN spoken_languages.iso_639_1 IS 'ISO 639-1 language code (2 letters)';
COMMENT ON COLUMN spoken_languages.iso_639_2 IS 'ISO 639-2 language code (3 letters)';

-- Insert common languages
INSERT INTO spoken_languages (name_en, name_nl, name_fr, iso_639_1, iso_639_2) VALUES
    -- Most common European languages
    ('Dutch', 'Nederlands', 'Néerlandais', 'nl', 'nld'),
    ('English', 'Engels', 'Anglais', 'en', 'eng'),
    ('French', 'Frans', 'Français', 'fr', 'fra'),
    ('German', 'Duits', 'Allemand', 'de', 'deu'),
    ('Spanish', 'Spaans', 'Espagnol', 'es', 'spa'),
    ('Italian', 'Italiaans', 'Italien', 'it', 'ita'),
    ('Portuguese', 'Portugees', 'Portugais', 'pt', 'por'),
    ('Polish', 'Pools', 'Polonais', 'pl', 'pol'),
    ('Romanian', 'Roemeens', 'Roumain', 'ro', 'ron'),
    ('Greek', 'Grieks', 'Grec', 'el', 'ell'),
    
    -- Nordic languages
    ('Swedish', 'Zweeds', 'Suédois', 'sv', 'swe'),
    ('Danish', 'Deens', 'Danois', 'da', 'dan'),
    ('Norwegian', 'Noors', 'Norvégien', 'no', 'nor'),
    ('Finnish', 'Fins', 'Finnois', 'fi', 'fin'),
    ('Icelandic', 'IJslands', 'Islandais', 'is', 'isl'),
    
    -- Eastern European languages
    ('Russian', 'Russisch', 'Russe', 'ru', 'rus'),
    ('Ukrainian', 'Oekraïens', 'Ukrainien', 'uk', 'ukr'),
    ('Czech', 'Tsjechisch', 'Tchèque', 'cs', 'ces'),
    ('Slovak', 'Slowaaks', 'Slovaque', 'sk', 'slk'),
    ('Hungarian', 'Hongaars', 'Hongrois', 'hu', 'hun'),
    ('Bulgarian', 'Bulgaars', 'Bulgare', 'bg', 'bul'),
    ('Croatian', 'Kroatisch', 'Croate', 'hr', 'hrv'),
    ('Serbian', 'Servisch', 'Serbe', 'sr', 'srp'),
    ('Slovenian', 'Sloveens', 'Slovène', 'sl', 'slv'),
    
    -- Asian languages
    ('Chinese', 'Chinees', 'Chinois', 'zh', 'zho'),
    ('Mandarin', 'Mandarijn', 'Mandarin', 'zh', 'cmn'),
    ('Cantonese', 'Kantonees', 'Cantonais', 'zh', 'yue'),
    ('Japanese', 'Japans', 'Japonais', 'ja', 'jpn'),
    ('Korean', 'Koreaans', 'Coréen', 'ko', 'kor'),
    ('Hindi', 'Hindi', 'Hindi', 'hi', 'hin'),
    ('Bengali', 'Bengaals', 'Bengali', 'bn', 'ben'),
    ('Urdu', 'Urdu', 'Ourdou', 'ur', 'urd'),
    ('Vietnamese', 'Vietnamees', 'Vietnamien', 'vi', 'vie'),
    ('Thai', 'Thais', 'Thaï', 'th', 'tha'),
    ('Indonesian', 'Indonesisch', 'Indonésien', 'id', 'ind'),
    ('Malay', 'Maleis', 'Malais', 'ms', 'msa'),
    ('Tagalog', 'Tagalog', 'Tagalog', 'tl', 'tgl'),
    
    -- Middle Eastern languages
    ('Arabic', 'Arabisch', 'Arabe', 'ar', 'ara'),
    ('Hebrew', 'Hebreeuws', 'Hébreu', 'he', 'heb'),
    ('Turkish', 'Turks', 'Turc', 'tr', 'tur'),
    ('Persian', 'Perzisch', 'Persan', 'fa', 'fas'),
    
    -- African languages
    ('Swahili', 'Swahili', 'Swahili', 'sw', 'swa'),
    ('Afrikaans', 'Afrikaans', 'Afrikaans', 'af', 'afr'),
    ('Zulu', 'Zoeloe', 'Zoulou', 'zu', 'zul'),
    
    -- Other European languages
    ('Albanian', 'Albanees', 'Albanais', 'sq', 'sqi'),
    ('Armenian', 'Armeens', 'Arménien', 'hy', 'hye'),
    ('Basque', 'Baskisch', 'Basque', 'eu', 'eus'),
    ('Catalan', 'Catalaans', 'Catalan', 'ca', 'cat'),
    ('Estonian', 'Estisch', 'Estonien', 'et', 'est'),
    ('Latvian', 'Lets', 'Letton', 'lv', 'lav'),
    ('Lithuanian', 'Litouws', 'Lituanien', 'lt', 'lit'),
    ('Macedonian', 'Macedonisch', 'Macédonien', 'mk', 'mkd'),
    ('Maltese', 'Maltees', 'Maltais', 'mt', 'mlt'),
    ('Welsh', 'Welsh', 'Gallois', 'cy', 'cym'),
    ('Irish', 'Iers', 'Irlandais', 'ga', 'gle'),
    ('Scottish Gaelic', 'Schots-Gaelisch', 'Gaélique écossais', 'gd', 'gla'),
    
    -- Sign languages
    ('Sign Language', 'Gebarentaal', 'Langue des signes', NULL, NULL),
    ('Belgian Sign Language', 'Vlaamse Gebarentaal', 'Langue des signes belge', NULL, NULL),
    ('American Sign Language', 'Amerikaanse Gebarentaal', 'Langue des signes américaine', NULL, NULL)
ON CONFLICT (name_en) DO NOTHING;

-- Create helper function to get language name in specific language
CREATE OR REPLACE FUNCTION get_language_name(
    english_name TEXT,
    target_language TEXT DEFAULT 'nl'
)
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    CASE target_language
        WHEN 'nl' THEN
            SELECT name_nl INTO result FROM spoken_languages WHERE name_en = english_name AND is_active = TRUE;
        WHEN 'fr' THEN
            SELECT name_fr INTO result FROM spoken_languages WHERE name_en = english_name AND is_active = TRUE;
        WHEN 'en' THEN
            SELECT name_en INTO result FROM spoken_languages WHERE name_en = english_name AND is_active = TRUE;
        ELSE
            SELECT name_en INTO result FROM spoken_languages WHERE name_en = english_name AND is_active = TRUE;
    END CASE;
    
    -- Return original if not found
    RETURN COALESCE(result, english_name);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_language_name IS 'Get language name in specified language (nl, fr, en). Returns original if not found.';

-- Create helper function to translate array of language names
CREATE OR REPLACE FUNCTION translate_language_array(
    language_array TEXT[],
    target_language TEXT DEFAULT 'nl'
)
RETURNS TEXT[] AS $$
DECLARE
    result TEXT[];
    lang TEXT;
BEGIN
    IF language_array IS NULL THEN
        RETURN NULL;
    END IF;
    
    result := ARRAY[]::TEXT[];
    
    FOREACH lang IN ARRAY language_array
    LOOP
        result := array_append(result, get_language_name(lang, target_language));
    END LOOP;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION translate_language_array IS 'Translate array of language names to specified language (nl, fr, en)';
