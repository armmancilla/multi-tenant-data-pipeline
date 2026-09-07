-- Step 1: Match exactly by CURP (Strongest Identifier)
UPDATE staging.working w
SET client_uuid = c.id_client
FROM public.{target_table} c
WHERE w.curp_cleaned = c.best_curp
    AND w.curp_cleaned IS NOT NULL 
    AND w.curp_cleaned != ''
    AND w.client_uuid IS NULL;

-- Step 2: Match by NSS (For leads that didn't have a CURP match)
UPDATE staging.working w
SET client_uuid = c.id_client
FROM public.{target_table} c
WHERE w.nss_cleaned = c.best_nss
    AND w.nss_cleaned IS NOT NULL 
    AND w.nss_cleaned != ''
    AND w.client_uuid IS NULL;

-- Step 3: Match by Full Name + Birth Date (Last Resort)
UPDATE staging.working w
SET client_uuid = c.id_client
FROM public.{target_table} c
WHERE w.names_cleaned = c.nombre
    AND w.first_lastname_cleaned = c.first_lastname
    AND COALESCE(w.second_lastname_cleaned, '') = COALESCE(c.second_lastname, '')
    AND w.birth_date = c.nacimiento::TEXT
    AND w.birth_date IS NOT NULL
    AND w.client_uuid IS NULL;