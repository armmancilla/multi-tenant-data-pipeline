WITH address_prep AS (
	SELECT
		ingest_id,
		address,
		-- Step 1: Clean prefix
		regexp_replace(
			regexp_replace(
				address,
				'^(?:C\.(?!\s)|(CALLE|C\.?\,?|AV\.?\,?|AVE\.?\,?|AVENIDA|PRIVADA|PRIV\.?|PV\.?)\s+)',
				'',
				'gi'
			),
			'\y(NUM|NO)\.?\s*|#\s*(?=\d)',
			'',
			'gi'
		) AS cleaned_address
	FROM staging.working
	WHERE address IS NOT NULL
),
address_split AS (
    SELECT
        ingest_id,
        cleaned_address,
        -- Step 2: Split into street and numbers using non-greedy match
        COALESCE(
            (regexp_match(cleaned_address, '^(?:([\d\s/]+)\s+(\d+.*)|(.*?[a-zA-Z.])\s*(\d+.*))$'))[1],
            (regexp_match(cleaned_address, '^(?:([\d\s/]+)\s+(\d+.*)|(.*?[a-zA-Z.])\s*(\d+.*))$'))[3],
			cleaned_address
		) AS raw_street,
		COALESCE(
            (regexp_match(cleaned_address, '^(?:([\d\s/]+)\s+(\d+.*)|(.*?[a-zA-Z.])\s*(\d+.*))$'))[2],
            (regexp_match(cleaned_address, '^(?:([\d\s/]+)\s+(\d+.*)|(.*?[a-zA-Z.])\s*(\d+.*))$'))[4]
		) AS raw_numbers
    FROM address_prep
),
numbers_split AS (
    SELECT
        ingest_id,
        cleaned_address,
        -- If split succeeded, use the extracted parts; otherwise, use the whole address as street
        COALESCE(raw_street, cleaned_address) AS street,
        raw_numbers,
        -- Step 3: Split numbers into exterior and interior
        (regexp_match(raw_numbers, '(\d+)\s*(.*)'))[1] AS num_ext,
        (regexp_match(raw_numbers, '(\d+)\s*(.*)'))[2] AS num_int
    FROM address_split
)
UPDATE staging.working w
SET
    calle = ns.street,
    num_ext = ns.num_ext,
    -- If num_int is an empty string (captured but no interior), set to NULL
    num_int = NULLIF(TRIM(ns.num_int), ''),
    step_status = CASE
        WHEN ns.num_ext IS NOT NULL THEN 'ADDRESS_SPLIT'
        ELSE 'ERROR_ADDRESS_SPLIT'
    END,
    error_flags = CASE 
        WHEN ns.num_ext IS NULL THEN array_append(error_flags, 'ADDRESS:NO_NUMBER_FOUND')
		WHEN (LENGTH(ns.num_ext) >= 10 OR LENGTH(ns.num_int) >= 10) IS NULL THEN array_append(error_flags, 'ADDRESS:NUMBER_TOO_LONG')
        ELSE error_flags
    END
FROM numbers_split ns
WHERE w.ingest_id = ns.ingest_id;