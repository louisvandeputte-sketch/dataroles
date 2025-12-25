-- Standardize Microsoft Fabric ecosystem variants to canonical "Fabric"
-- This migration merges MS Fabric, Microsoft Data Fabric, and Data Fabric into Fabric

-- Step 1: Get the IDs we need
DO $$
DECLARE
    v_fabric_id UUID;
    v_ms_fabric_id UUID;
    v_microsoft_data_fabric_id UUID;
    v_data_fabric_id UUID;
BEGIN
    -- Find canonical Fabric entry
    SELECT id INTO v_fabric_id
    FROM ecosystems
    WHERE name = 'Fabric' AND is_active = true;
    
    -- Find variants to merge
    SELECT id INTO v_ms_fabric_id
    FROM ecosystems
    WHERE name = 'MS Fabric' AND is_active = true;
    
    SELECT id INTO v_microsoft_data_fabric_id
    FROM ecosystems
    WHERE name = 'Microsoft Data Fabric' AND is_active = true;
    
    SELECT id INTO v_data_fabric_id
    FROM ecosystems
    WHERE name = 'Data Fabric' AND is_active = true;
    
    RAISE NOTICE 'Fabric ID: %', v_fabric_id;
    RAISE NOTICE 'MS Fabric ID: %', v_ms_fabric_id;
    RAISE NOTICE 'Microsoft Data Fabric ID: %', v_microsoft_data_fabric_id;
    RAISE NOTICE 'Data Fabric ID: %', v_data_fabric_id;
    
    -- Step 2: Merge MS Fabric into Fabric
    IF v_ms_fabric_id IS NOT NULL AND v_fabric_id IS NOT NULL THEN
        -- Update job assignments, avoiding duplicates
        UPDATE job_ecosystems
        SET ecosystem_id = v_fabric_id
        WHERE ecosystem_id = v_ms_fabric_id
        AND NOT EXISTS (
            SELECT 1 FROM job_ecosystems je2
            WHERE je2.job_posting_id = job_ecosystems.job_posting_id
            AND je2.ecosystem_id = v_fabric_id
        );
        
        -- Delete duplicate assignments
        DELETE FROM job_ecosystems
        WHERE ecosystem_id = v_ms_fabric_id;
        
        -- Deactivate MS Fabric
        UPDATE ecosystems
        SET is_active = false
        WHERE id = v_ms_fabric_id;
        
        -- Create alias
        INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes)
        VALUES ('MS Fabric', 'Fabric', 'ecosystem', 'Microsoft Fabric standardization')
        ON CONFLICT (alias, type) DO NOTHING;
        
        RAISE NOTICE 'Merged MS Fabric into Fabric';
    END IF;
    
    -- Step 3: Merge Microsoft Data Fabric into Fabric
    IF v_microsoft_data_fabric_id IS NOT NULL AND v_fabric_id IS NOT NULL THEN
        -- Update job assignments, avoiding duplicates
        UPDATE job_ecosystems
        SET ecosystem_id = v_fabric_id
        WHERE ecosystem_id = v_microsoft_data_fabric_id
        AND NOT EXISTS (
            SELECT 1 FROM job_ecosystems je2
            WHERE je2.job_posting_id = job_ecosystems.job_posting_id
            AND je2.ecosystem_id = v_fabric_id
        );
        
        -- Delete duplicate assignments
        DELETE FROM job_ecosystems
        WHERE ecosystem_id = v_microsoft_data_fabric_id;
        
        -- Deactivate Microsoft Data Fabric
        UPDATE ecosystems
        SET is_active = false
        WHERE id = v_microsoft_data_fabric_id;
        
        -- Create alias
        INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes)
        VALUES ('Microsoft Data Fabric', 'Fabric', 'ecosystem', 'Microsoft Fabric standardization')
        ON CONFLICT (alias, type) DO NOTHING;
        
        RAISE NOTICE 'Merged Microsoft Data Fabric into Fabric';
    END IF;
    
    -- Step 4: Merge Data Fabric into Fabric
    IF v_data_fabric_id IS NOT NULL AND v_fabric_id IS NOT NULL THEN
        -- Update job assignments, avoiding duplicates
        UPDATE job_ecosystems
        SET ecosystem_id = v_fabric_id
        WHERE ecosystem_id = v_data_fabric_id
        AND NOT EXISTS (
            SELECT 1 FROM job_ecosystems je2
            WHERE je2.job_posting_id = job_ecosystems.job_posting_id
            AND je2.ecosystem_id = v_fabric_id
        );
        
        -- Delete duplicate assignments
        DELETE FROM job_ecosystems
        WHERE ecosystem_id = v_data_fabric_id;
        
        -- Deactivate Data Fabric
        UPDATE ecosystems
        SET is_active = false
        WHERE id = v_data_fabric_id;
        
        -- Create alias
        INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes)
        VALUES ('Data Fabric', 'Fabric', 'ecosystem', 'Microsoft Fabric standardization')
        ON CONFLICT (alias, type) DO NOTHING;
        
        RAISE NOTICE 'Merged Data Fabric into Fabric';
    END IF;
    
    -- Step 5: Update Fabric display name to be clear
    IF v_fabric_id IS NOT NULL THEN
        UPDATE ecosystems
        SET display_name = 'Microsoft Fabric'
        WHERE id = v_fabric_id;
        
        RAISE NOTICE 'Updated Fabric display name to Microsoft Fabric';
    END IF;
    
END $$;
