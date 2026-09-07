UPDATE staging.working
SET
    nss_cleaned = LPAD(REGEXP_REPLACE(nss, '\D', '', 'g'),11, '0'),
    curp_cleaned = UPPER(TRIM(curp)),
    first_lastname_cleaned = UPPER(TRIM(first_lastname)),
    second_lastname_cleaned = UPPER(TRIM(second_lastname)),
    names_cleaned = UPPER(TRIM(names)),
    gender_cleaned = CASE WHEN UPPER(TRIM(gender)) = 'FEMENINO' THEN 'M' WHEN UPPER(TRIM(gender)) = 'MASCULINO' THEN 'H' END,
    step_status = 'IDENTITIES_CLEANED';

UPDATE staging.working
SET
    birth_date = CASE
        WHEN SUBSTRING(curp_cleaned,5,2)::INT <= TO_CHAR(CURRENT_DATE, 'YY')::INT THEN '20'||SUBSTRING(curp_cleaned,5,2)||'-'||SUBSTRING(curp_cleaned,7,2)||'-'||SUBSTRING(curp_cleaned,9,2)
        WHEN SUBSTRING(curp_cleaned,5,2)::INT > TO_CHAR(CURRENT_DATE, 'YY')::INT THEN '19'||SUBSTRING(curp_cleaned,5,2)||'-'||SUBSTRING(curp_cleaned,7,2)||'-'||SUBSTRING(curp_cleaned,9,2)
    END
WHERE LENGTH(curp_cleaned) >= 11
AND SUBSTRING(curp_cleaned, 5,6) ~ '^[0-9]{6}$'
AND step_status = 'IDENTITIES_CLEANED';

UPDATE staging.working
SET
    second_lastname_cleaned = NULL
WHERE second_lastname_cleaned IN ('N/A', 'Nombre(s):', 'NULL', '')
OR second_lastname_cleaned !~ '^[A-ZÑÁÉÍÓÚÄËÏÖÜ .-]+$';

-- Audit query
UPDATE staging.working w
SET
    error_flags = CASE
        WHEN birth_date IS NULL THEN array_append(error_flags, 'IDENTIFIERS:NO_BIRTH_DATE')
        WHEN birth_date IS NULL THEN array_append(error_flags, 'IDENTIFIERS:NO_GENDER_ASSIGNED')
        ELSE w.error_flags
    END;