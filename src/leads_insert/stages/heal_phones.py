from src.core.connection import DatabaseClient
from src.core.utils import SQL_DIR

PHONES_DIR = SQL_DIR / "phone_numbers"

def heal_main_phone_and_email(client: DatabaseClient):
    """Cleans the main phone and cheks it's not empty. Standardizes the email"""
    
    client.execute_sql_file(
        filepath=PHONES_DIR / "heal_emails_and_main_phone.sql"
    )