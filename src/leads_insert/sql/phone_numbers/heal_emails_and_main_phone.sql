WITH prep AS (
    SELECT 
        ingest_id,
        
        -- 1. Phone: Remove everything that is not a digit
        REGEXP_REPLACE(main_phone, '\D', '', 'g') AS raw_phone,
        
        -- 2. Email: Standardize to lowercase and remove surrounding spaces
        TRIM(LOWER(mail)) AS raw_email
    FROM staging.working
),
eval AS (
    SELECT 
        ingest_id,
        raw_phone AS phone_1,
        raw_email AS mail_cleaned,
        
        -- Evaluate rules and build the error array
        ARRAY_REMOVE(ARRAY[
            -- Phone Errors
            CASE 
                WHEN raw_phone IS NULL OR raw_phone = '' THEN 'PHONE:MISSING'
                WHEN LENGTH(raw_phone) != 10 THEN 'PHONE:INVALID_LENGTH' 
            END,
            
            -- Email Errors
            CASE 
                WHEN raw_email IS NOT NULL AND raw_email != '' 
                -- Standard email validation RegEx
                AND raw_email !~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$' 
                THEN 'EMAIL:INVALID_FORMAT' 
            END
        ], NULL) AS new_errors
        
    FROM prep
)
UPDATE staging.working w
SET 
    phone_1 = e.phone_1,
    mail_cleaned = e.mail_cleaned,
    
    -- Append to the error_flags array
    error_flags = COALESCE(w.error_flags, ARRAY[]::TEXT[]) || e.new_errors
FROM eval e
WHERE w.ingest_id = e.ingest_id;