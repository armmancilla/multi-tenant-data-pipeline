from src.core.connection import DatabaseClient
from src.core.utils import SQL_DIR

UPSERT_DIR = SQL_DIR / "final_upsert"

def push_to_production_and_quarantine(client: DatabaseClient, target_table: str, team_code: str, campaign: str):
    """
    Routes clean records to production tables and dirty records to quarantine,
    then empties the staging table.
    """
    
    # We pass the dynamic table names as a dictionary
    dynamic_tables = {
        "target_table": target_table
    }
    
    params = {
        "team_code": team_code,
        "campaign": campaign
    }
    
    client.execute_sql_file(
        filepath=UPSERT_DIR / "upsert_and_quarantine.sql",
        dynamic_tables=dynamic_tables,
        params=params
    )