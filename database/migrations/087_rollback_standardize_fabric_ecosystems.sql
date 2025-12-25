-- Rollback for migration 087: Restore Microsoft Fabric ecosystem variants
-- This migration reverses the standardization and restores MS Fabric, Microsoft Data Fabric, and Data Fabric

DO $$
DECLARE
    v_fabric_id UUID;
    v_ms_fabric_id UUID;
    v_microsoft_data_fabric_id UUID;
    v_data_fabric_id UUID;
    v_job_count INTEGER;
BEGIN
    -- Find canonical Fabric entry
    SELECT id INTO v_fabric_id
    FROM ecosystems
    WHERE name = 'Fabric' AND is_active = true;
    
    -- Find deactivated variants
    SELECT id INTO v_ms_fabric_id
    FROM ecosystems
    WHERE name = 'MS Fabric';
    
    SELECT id INTO v_microsoft_data_fabric_id
    FROM ecosystems
    WHERE name = 'Microsoft Data Fabric';
    
    SELECT id INTO v_data_fabric_id
    FROM ecosystems
    WHERE name = 'Data Fabric';
    
    RAISE NOTICE 'Fabric ID: %', v_fabric_id;
    RAISE NOTICE 'MS Fabric ID: %', v_ms_fabric_id;
    RAISE NOTICE 'Microsoft Data Fabric ID: %', v_microsoft_data_fabric_id;
    RAISE NOTICE 'Data Fabric ID: %', v_data_fabric_id;
    
    -- Count current Fabric assignments
    SELECT COUNT(*) INTO v_job_count
    FROM job_ecosystems
    WHERE ecosystem_id = v_fabric_id;
    
    RAISE NOTICE 'Current Fabric job assignments: %', v_job_count;
    
    -- Step 1: Reactivate MS Fabric
    IF v_ms_fabric_id IS NOT NULL THEN
        UPDATE ecosystems
        SET is_active = true
        WHERE id = v_ms_fabric_id;
        
        RAISE NOTICE 'Reactivated MS Fabric';
    END IF;
    
    -- Step 2: Reactivate Microsoft Data Fabric
    IF v_microsoft_data_fabric_id IS NOT NULL THEN
        UPDATE ecosystems
        SET is_active = true
        WHERE id = v_microsoft_data_fabric_id;
        
        RAISE NOTICE 'Reactivated Microsoft Data Fabric';
    END IF;
    
    -- Step 3: Reactivate Data Fabric
    IF v_data_fabric_id IS NOT NULL THEN
        UPDATE ecosystems
        SET is_active = true
        WHERE id = v_data_fabric_id;
        
        RAISE NOTICE 'Reactivated Data Fabric';
    END IF;
    
    -- Step 4: Remove aliases created during standardization
    DELETE FROM tech_stack_aliases
    WHERE alias IN ('MS Fabric', 'Microsoft Data Fabric', 'Data Fabric')
    AND type = 'ecosystem'
    AND canonical_name = 'Fabric';
    
    RAISE NOTICE 'Removed Fabric standardization aliases';
    
    -- Step 5: Restore original Fabric display name
    IF v_fabric_id IS NOT NULL THEN
        UPDATE ecosystems
        SET display_name = 'Fabric'
        WHERE id = v_fabric_id;
        
        RAISE NOTICE 'Restored Fabric display name';
    END IF;
    
    -- Note: We do NOT redistribute job_ecosystems assignments back to the variants
    -- because we don't have historical data about which jobs originally had which variant.
    -- All jobs will remain assigned to canonical "Fabric".
    -- If you need to manually redistribute assignments, you'll need to do that separately.
    
    RAISE NOTICE 'Rollback complete. Note: Job assignments remain with canonical Fabric.';
    RAISE NOTICE 'To redistribute assignments, you will need to manually update job_ecosystems table.';
    
END $$;
