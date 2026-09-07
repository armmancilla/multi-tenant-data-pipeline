import os
import psycopg2
import logging

from src.core.config import settings, ROOT_DIR
from src.core.logger import configure_logging

from yoyo import read_migrations, get_backend
from pathlib import Path

logger = logging.LoggerAdapter(logging.getLogger(__name__), extra={"stage": "MIGRATIONS"})

TENANTS = {
    "tenant_a": settings.database_a,
    "tenant_b": settings.database_b
}

def execute_tenant_migrations(db_url: str, tenant_name: str, database: str):
    """Updates the database with the corresponding migrations"""
    
    migration_dir = ROOT_DIR / "migrations" / tenant_name
    migration_dir_str = str(migration_dir.resolve())

    if not os.path.exists(migration_dir_str):
        logger.warning(f"--- [Yoyo] Warning: Path {migration_dir_str} does not exist ---")
        return

    logger.info(f"Looking for migrations in: {migration_dir_str}")
    for f in os.listdir(migration_dir_str):
        logger.info(f" - {f}")
    
    logger.info(f"--- [Yoyo] Checking for {database} database migrations... ---")
    try:
        backend = get_backend(db_url)
        migrations = read_migrations(migration_dir_str)
        logger.info(f"Total migrations found on disk: {len(migrations)}")
        for m in migrations:
            logger.info(f"  id={m.id}, path={m.path}")
        
        backend.init_database()

        try:
            with backend.lock():
                to_apply = backend.apply_migrations(backend.to_apply(migrations))
        except Exception as e:
            logger.info(f"--- [Yoyo] Error during migration apply: {type(e).__name__}: {e} ---")
            error_str = str(e).lower()
            if "lock" in error_str and ("locked" in error_str or "exists" in error_str):
                logger.info(f"--- [Yoyo] Lock detected ({e}). Breaking lock and retrying... ---")
                backend.break_lock() 
                with backend.lock():
                    backend.apply_migrations(backend.to_apply(migrations))
        logger.info(f"--- [Yoyo] Database {database} is up to date! ---")
        
    except Exception as e:
        logger.error(f"--- [Yoyo] MIGRATION FAILED: {e} ---")


def run_migrations():
    """Run all migrations for each tenant"""

    for tenant_name, db_name in TENANTS.items():

        logger.info(f"Starting Yoyo migrations for {tenant_name}...")
        
        db_url = f"postgresql://{settings.yoyo_user}:{settings.yoyo_password}@{settings.db_host}/{db_name}"

        execute_tenant_migrations(db_url=db_url, tenant_name=tenant_name, database=db_name)
        logger.info(f"[{tenant_name}] Yoyo migrations applied successfully")


if __name__ == "__main__":
    configure_logging()
    run_migrations()