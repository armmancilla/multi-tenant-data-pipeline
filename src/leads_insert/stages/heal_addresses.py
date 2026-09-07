from src.core.connection import DatabaseClient
from src.core.utils import SQL_DIR

ADDRESSES_DIR = SQL_DIR / "addresses"

def heal_easy_address_columns(client: DatabaseClient):
    """Used for the stage to clean the 'easy' columns of the address"""
    
    client.execute_sql_file(
        filepath=ADDRESSES_DIR / "heal_easy_columns.sql"
    )

def find_state_name_by_alias(client: DatabaseClient):
    """Uses the reference.states_aliases to find the standard state name, otherwise, will 'throw an error'"""
    
    client.execute_sql_file(
        filepath=ADDRESSES_DIR / "resolve_state.sql"
    )

def split_addresses(client: DatabaseClient):
    """This function executes the address spliting"""
    
    client.execute_sql_file(
        filepath=ADDRESSES_DIR / "split_addresses.sql"
    )