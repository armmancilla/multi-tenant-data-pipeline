-- BE AWARE! This is not pure SQL syntax. It depends on Psycopg unmentionable string objects inputs

TRUNCATE staging.working;

INSERT INTO staging.working (
    ingest_id, nss, curp, first_lastname, second_lastname, names, gender,
    address, colonia, zip, city, state,
    main_phone, mail, income, additional_phones,
    provider_code, provider_name, step_status
)
SELECT 
    raw.ingest_id, raw.nss, raw.curp, raw.first_lastname, raw.second_lastname, raw.names, raw.gender,
    raw.address, raw.colonia, raw.zip, raw.city, raw.state,
    raw.main_phone, raw.mail, raw.income, raw.additional_phones,
    manifest.provider_code,
    manifest.provider_name,
    'BULK_LOAD'
FROM raw.leads_ingest raw
INNER JOIN raw.load_manifest manifest 
ON raw.file_hash = manifest.file_hash
WHERE manifest.provider_code = %(code)s
AND manifest.loaded_at = (
    SELECT MAX(loaded_at)
    FROM raw.load_manifest 
    WHERE provider_code = %(code)s
)
ON CONFLICT(ingest_id) DO NOTHING;  -- Only copy the latest batch for that provider