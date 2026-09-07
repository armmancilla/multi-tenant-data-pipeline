from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

CURRENT_FILE = Path(__file__).resolve()
ROOT_DIR = CURRENT_FILE.parent.parent.parent

ENV_FILE_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):

    project_name: str = "Leads ELT"

    # Data path
    leads_tenant_a_path: str = "../../data/tenant_a/sample_leads.csv"
    leads_tenant_b_path: str = "../../data/tenant_b/sample_leads.csv"

    # Database Config
    database_a: str = "tenant_a"
    database_b: str = "tenant_b"

    yoyo_user: str = "db_superuser"
    yoyo_password: str = "db_superuser_password"

    db_user: str = "pipeline_user"
    db_password: str = "pipeline_password"
    db_host: str = "database"
    db_port: int = 5432

    # This tells Pydantic to read from the .env file in the root folder
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore")

# Creates a global instance of settings to use everywhere
settings = Settings()