WITH state_prep AS (
    SELECT 
        ingest_id,
        state AS original_state,
        TRIM(
            REGEXP_REPLACE(
                UNACCENT(UPPER(REGEXP_REPLACE(state, '[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', 'g'))), 
                '\s+', ' ', 'g'
            )
        ) AS cleaned_input
    FROM staging.working
)
UPDATE staging.working w
SET 
    -- If the join succeeds, use the standard name. If not, leave it NULL or keep the cleaned input
    state_cleaned = ref.standard_name,
    error_flags = CASE 
        WHEN ref.standard_name IS NULL THEN array_append(w.error_flags, 'STATE:UNRECOGNIZED_STATE')
        ELSE w.error_flags
    END
FROM state_prep sp
LEFT JOIN reference.states_aliases ref 
    ON sp.cleaned_input = ref.input_value
WHERE w.ingest_id = sp.ingest_id;