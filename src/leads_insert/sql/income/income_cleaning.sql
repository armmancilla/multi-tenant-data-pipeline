WITH prep AS (
    SELECT 
        ingest_id,
        -- Remove everything EXCEPT digits and the decimal point
        REGEXP_REPLACE(income, '[^0-9.]', '', 'g') AS numeric_string
    FROM staging.working
),
eval AS (
    SELECT 
        ingest_id,
        numeric_string AS income_cleaned,
        
        ARRAY_REMOVE(ARRAY[
            -- 1. Check if it's missing
            CASE WHEN numeric_string IS NULL OR numeric_string = '' THEN 'INCOME:MISSING' END,
            
            -- 2. Check if it's a valid number format (allows one optional decimal point)
            CASE WHEN numeric_string != '' AND numeric_string !~ '^[0-9]+(\.[0-9]+)?$' THEN 'INCOME:INVALID_FORMAT' END,
            
            -- 3. Bounds checking (Must be > 0 and let's cap it at $10,000,000 to catch typos)
            CASE 
                WHEN numeric_string ~ '^[0-9]+(\.[0-9]+)?$' 
                AND (numeric_string::NUMERIC <= 0 OR numeric_string::NUMERIC > 10000000) 
                THEN 'INCOME:OUT_OF_RANGE' 
            END
        ], NULL) AS new_errors
        
    FROM prep
)
UPDATE staging.working w
SET 
    income_cleaned = e.income_cleaned,
    error_flags = COALESCE(w.error_flags, ARRAY[]::TEXT[]) || e.new_errors
FROM eval e
WHERE w.ingest_id = e.ingest_id;