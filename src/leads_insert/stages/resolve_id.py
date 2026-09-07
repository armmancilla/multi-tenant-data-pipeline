import psycopg2
from src.core.utils import SQL_DIR
from src.core.connection import DatabaseClient

ID_DIR = SQL_DIR / "identifiers"

def heal_leads_identifiers(client: DatabaseClient):
    """We use this query to send the raw leads info to the stagin table where we'll clean them"""
    
    client.execute_sql_file(
        filepath=ID_DIR / "heal_identifiers.sql"
    )


def match_client_uuid(client: DatabaseClient, target_table: str):
    """Attempts to find existing clients and append their UUID to the staging table."""
    client.execute_sql_file(
        filepath=ID_DIR / "resolve_ids.sql",
        dynamic_tables={"target_table": target_table}
    )