from src.core.connection import DatabaseClient
from src.core.utils import SQL_DIR

INCOME_DIR = SQL_DIR / "income"

def heal_income(client: DatabaseClient):
    """A superficial income cleaning"""
    
    client.execute_sql_file(
        filepath=INCOME_DIR / "income_cleaning.sql"
    )