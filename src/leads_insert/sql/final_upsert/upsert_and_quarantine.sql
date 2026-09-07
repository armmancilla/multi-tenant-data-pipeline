-- STEP 1: Generate UUIDs for brand new clean leads
-- We do this IN the staging table so we can use the exact same UUID 
-- for both the `clientes` insert and the `clientes_info` insert.
UPDATE staging.working
SET client_uuid = gen_random_uuid()
WHERE client_uuid IS NULL
    AND (error_flags IS NULL OR CARDINALITY(error_flags) = 0);

-- STEP 2: Insert NEW clients into the main table
-- Using ON CONFLICT DO NOTHING means if a race condition happens or 
-- our UUID matcher missed something, we don't crash.
INSERT INTO public.{target_table} (
    id_client, first_lastname, second_lastname, nombre,
    best_curp, best_nss, nacimiento, genero
)
SELECT
    client_uuid,
    first_lastname_cleaned,
    second_lastname_cleaned,
    names_cleaned,
    curp_cleaned,
    nss_cleaned,
    birth_date::DATE,
    gender_cleaned
FROM staging.working
WHERE (error_flags IS NULL OR CARDINALITY(error_flags) = 0)
ON CONFLICT (id_client) DO NOTHING;

-- STEP 3: Upsert the Contact Info
-- Every clean row gets inserted here, linking back to the client_uuid.
INSERT INTO public.clientes_info (
    client_id, proveedor_id, proveedor, 
    phone_1, phone_2, email,
    calle, num_ext, num_int, colonia, ciudad, estado, cp,
    percepcion_real
)
SELECT
    client_uuid,
    nss_cleaned || provider_code AS proveedor_id, -- Concat NSS and Code safely
    provider_name AS proveedor,
    phone_1,
    phone_2,
    mail_cleaned,
    calle,
    num_ext,
    num_int,
    colonia_cleaned,
    city_cleaned,
    state_cleaned,
    zip_cleaned,
    income_cleaned::NUMERIC
FROM staging.working
WHERE (error_flags IS NULL OR CARDINALITY(error_flags) = 0)
-- This relies on your idx_cliente_proveedor unique index
ON CONFLICT (client_id, proveedor_id) DO NOTHING;

INSERT INTO public.gerencia_pertenencia (
    client_id, team_code, campaign
)
SELECT
    client_uuid,
    %(team_code)s,
    %(campaign)s
FROM staging.working
WHERE (error_flags IS NULL OR CARDINALITY(error_flags) = 0)
ON CONFLICT (client_id, team_code) DO NOTHING;

-- STEP 5: Route Dirty Rows to Quarantine
INSERT INTO quarantine.leads_errors (
    staging_id, ingest_id, nss, curp, first_lastname, second_lastname, names,
    gender, address, colonia, zip, city, state, main_phone, mail, income,
    additional_phones, nss_cleaned, curp_cleaned, client_uuid,
    first_lastname_cleaned, second_lastname_cleaned, names_cleaned,
    gender_cleaned, birth_date, calle, num_ext, num_int, colonia_cleaned,
    zip_cleaned, city_cleaned, state_cleaned, phone_1, phone_2,
    additional_phones_cleaned, mail_cleaned, income_cleaned,
    provider_code, provider_name, step_status, error_flags
)
SELECT
    id_staging, -- Assuming your staging table has an 'id' column mapped to staging_id
    ingest_id, nss, curp, first_lastname, second_lastname, names,
    gender, address, colonia, zip, city, state, main_phone, mail, income,
    additional_phones, nss_cleaned, curp_cleaned, client_uuid,
    first_lastname_cleaned, second_lastname_cleaned, names_cleaned,
    gender_cleaned, birth_date, calle, num_ext, num_int, colonia_cleaned,
    zip_cleaned, city_cleaned, state_cleaned, phone_1, phone_2,
    additional_phones_cleaned, mail_cleaned, income_cleaned,
    provider_code, provider_name, step_status, error_flags
FROM staging.working
WHERE CARDINALITY(error_flags) > 0
ON CONFLICT (ingest_id) DO NOTHING;

-- STEP 6: Clear the staging table for tomorrow's run
TRUNCATE staging.working;