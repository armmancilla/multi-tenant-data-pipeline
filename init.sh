#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE tenant_b;
    CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASSWORD';
EOSQL