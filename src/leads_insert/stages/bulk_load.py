import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import json
import hashlib

from src.core.connection import DatabaseClient
from src.core.utils import SQL_DIR

STAGING_DIR = SQL_DIR / "staging"

def get_file_hash(file_path: str) -> str:
    """Computes SHA256 hash of the file contents."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Split file in chunks to avoid memory issues with huge files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_and_register_file(conn, file_path: str, source_code: str, source_name: str, row_count: int) -> bool:
    """
    Checks if the file hash exists in load_manifest. If it does, returns False (meaning "skip this
    load"). If it doesn't, inserts the hash into the manifest and returns True.
    """
    file_hash = get_file_hash(file_path)
    
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM raw.load_manifest WHERE file_hash = %s", (file_hash,))
        exists = cur.fetchone()
        
        if exists:
            print(f"File {file_path} already loaded (hash: {file_hash[:8]}...). Skipping.")
            return None
        
        # Register this load
        cur.execute("""
            INSERT INTO raw.load_manifest (file_hash, file_name, provider_code, provider_name, row_count)
            VALUES (%s, %s, %s, %s, %s)
        """, (file_hash, file_path.split('/')[-1], source_code, source_name, row_count))
        
        conn.commit()
        print(f"Registered file {file_path} (hash: {file_hash[:8]}...) in manifest.")
        return file_hash


def bulk_load_raw(excel_path: str, conn: psycopg2.extensions.connection, source_code: str, source_name: str):
    """
    Reads the Excel, transforms variable phone columns into a JSONB array,
    and bulk inserts into raw.leads_ingest.
    """
    # 1. Read the Excel
    df = pd.read_csv(excel_path, dtype=str).replace({np.nan: None})
    row_count = len(df)
    
    # 2. Check manifest
    file_hash = check_and_register_file(conn, excel_path, source_code, source_name, row_count)
    if not file_hash:
        return
    
    # 3. We identify the additional phone columns dynamically
    #    We assume the main phone is 'phone_1', any 'phone_2' to 'phone_N' go into JSONB
    all_cols = df.columns.tolist()
    main_phone_col = 'phone_1' if 'phone_1' in all_cols else None
    extra_phone_cols = [col for col in all_cols if col.startswith('phone_') and col != main_phone_col]
    
    # 4. We build the tuples for insert
    rows = []
    for _, row in df.iterrows():
        # Join any other phone in a list, filtering None/NaN
        extra_phones = [str(row[col]) for col in extra_phone_cols if pd.notna(row[col])]
        
        # We build the tuple in the order of the raw table columns
        rows.append((
            row.get('nss'),
            row.get('curp'),
            row.get('first_lastname'),
            row.get('second_lastname'),
            row.get('names'),
            row.get('gender'),
            row.get('address'),
            row.get('colonia'),
            row.get('zip'),
            row.get('city'),
            row.get('state'),
            row.get(main_phone_col) if main_phone_col else None,
            row.get('mail'),
            row.get('income'),
            json.dumps(extra_phones) if extra_phones else None,
            excel_path.split('/')[-1],
            file_hash
        ))
    
    # 5. Execute the bulk insert
    insert_sql = """
        INSERT INTO raw.leads_ingest (
            nss, curp, first_lastname, second_lastname, names, 
            gender, address, colonia, zip, city, state,
            main_phone, mail, income, additional_phones, source_file, file_hash
        ) VALUES %s
    """
    
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, rows, page_size=1000)
        conn.commit()
    
    print(f"Bulk loaded {len(rows)} records into raw.leads_ingest")


def copy_raw_to_staging(client: DatabaseClient, provider_code: str):
    """We use this query to send the raw leads info to the stagin table where we'll clean them"""
    
    client.execute_sql_file(
        filepath=STAGING_DIR / "copy_raw_to_staging.sql",
        params={"code": provider_code}
    )