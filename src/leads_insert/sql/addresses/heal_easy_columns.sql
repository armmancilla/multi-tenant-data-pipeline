WITH prep AS (
    SELECT 
        ingest_id,
        -- 1. Colonia: Basic clean
        TRIM(REGEXP_REPLACE(UPPER(colonia), '\s+', ' ', 'g')) AS cleaned_colonia,
        
        -- 2. City: Keep only letters and spaces, then trim/upper
        TRIM(
            REGEXP_REPLACE(
                UNACCENT(UPPER(REGEXP_REPLACE(city, '[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', 'g'))), 
                '\s+', ' ', 'g'
            )
        ) AS cleaned_city,
        
        -- 3. ZIP: Extract only the digits
        REGEXP_REPLACE(zip, '\D', '', 'g') AS raw_zip
    FROM staging.working
),
eval AS (
    SELECT 
        ingest_id,
        cleaned_colonia,
        cleaned_city,
        
        CASE 
            WHEN LENGTH(raw_zip) > 0 AND LENGTH(raw_zip) <= 5 THEN LPAD(raw_zip, 5, '0')
            ELSE raw_zip 
        END AS final_zip,
        
        -- Build an array of any errors that occurred in this stage
        ARRAY_REMOVE(ARRAY[
            CASE WHEN LENGTH(raw_zip) > 5 THEN 'ZIP:TOO_LONG' END,
            CASE WHEN LENGTH(raw_zip) = 0 OR raw_zip IS NULL THEN 'ZIP:MISSING_OR_INVALID' END,
            CASE WHEN cleaned_city IS NULL OR cleaned_city = '' THEN 'CITY:MISSING' END
        ], NULL) AS new_errors
        
    FROM prep
)
UPDATE staging.working w
SET 
    colonia_cleaned = e.cleaned_colonia,
    city_cleaned = e.cleaned_city,
    zip_cleaned = e.final_zip,
    
    error_flags = COALESCE(w.error_flags, ARRAY[]::TEXT[]) || e.new_errors,

    step_status = 'ADDRESS_CLEANSING'
FROM eval e
WHERE w.ingest_id = e.ingest_id;