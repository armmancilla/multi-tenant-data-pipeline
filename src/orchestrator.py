import logging
import psycopg2
import os

from src.core.connection import DatabaseClient
from core.config import settings
from core.logger import configure_logging

from src.leads_insert.stages.bulk_load import bulk_load_raw, copy_raw_to_staging
from src.leads_insert.stages.resolve_id import heal_leads_identifiers, match_client_uuid
from src.leads_insert.stages.heal_addresses import heal_easy_address_columns, find_state_name_by_alias, split_addresses
from src.leads_insert.stages.heal_phones import heal_main_phone_and_email
from src.leads_insert.stages.heal_incomes import heal_income

from src.leads_insert.stages.final_upsert import push_to_production_and_quarantine

configure_logging()

logger = logging.LoggerAdapter(logging.getLogger(__name__), extra={"stage": "INIT"})

# Build the configuration for each database
config_company_a = {
    'database': settings.database_a,
    'user': settings.db_user,
    'password': settings.db_password,
    'host': settings.db_host,
    'port': settings.db_port
}

config_company_b = {
    'database': settings.database_b,
    'user': settings.db_user,
    'password': settings.db_password,
    'host': settings.db_host,
    'port': settings.db_port
}

# Instantiate the clients
client_a = DatabaseClient(config_company_a)
client_b = DatabaseClient(config_company_b)

# --- Main Pipeline ---
def run_pipeline():
    """
    Main Pipeline. All the stages are contained here. We split the execution by tenant, allowing
    the script to skip one of them in case the source file is missing
    """
    try:
        with client_a as ca, client_b as cb:
            
            # Skip if file doesn't exist
            if os.path.isfile(settings.leads_tenant_a_path):
                
                logger.extra["stage"] = "BULK_LOAD"
                logger.info("Starting bulk load for Client A")
                
                # Step 1: Bulk load into both
                bulk_load_raw(settings.leads_tenant_a_path, ca.conn, settings.provider_code, settings.provider_name)
                copy_raw_to_staging(ca, settings.provider_code)
                
                logger.extra["stage"] = "HEALING_DATA"
                
                # Step 2: Heal & Clean Data
                logger.info("Healing Identifiers")
                #   1. Identifiers
                heal_leads_identifiers(ca)
                
                logger.info("Healing Addresses")
                #   2. Addresses
                heal_easy_address_columns(ca)
                find_state_name_by_alias(ca)
                split_addresses(ca)
                
                logger.info("Healing Phones")
                #   3. Phones & Emails
                heal_main_phone_and_email(ca)
                
                logger.info("Healing Incomes")
                #   4. Incomes
                heal_income(ca)
                
                logger.extra["stage"] = "IDENTITY_RESOLUTION"
                logger.info("Matching existing clients")
                
                # Step 3: Identity Resolution
                match_client_uuid(ca, target_table="clients")
                
                logger.extra["stage"] = "FINAL_UPSERT"
                logger.info("Upserting valid information")
                
                # Step 4: Final Split (Production & Quarantine)
                push_to_production_and_quarantine(ca, target_table="clients", team_code="TEAM:A", campaign="NEW_CLIENT")
            
            if os.path.isfile(settings.leads_tenant_b_path):
                
                logger.extra["stage"] = "BULK_LOAD"
                logger.info("Starting bulk load for Client B")
                
                # Step 1: Bulk load into both
                bulk_load_raw(settings.leads_tenant_b_path, cb.conn, settings.provider_code, settings.provider_name)
                copy_raw_to_staging(cb, settings.provider_code)
                
                logger.extra["stage"] = "HEALING_DATA"
                
                # Step 2: Heal & Clean Data
                logger.info("Healing Identifiers")
                #   1. Identifiers
                heal_leads_identifiers(cb)
                
                logger.info("Healing Addresses")
                #   2. Addresses
                heal_easy_address_columns(cb)
                find_state_name_by_alias(cb)
                split_addresses(cb)
                
                logger.info("Healing Phones")
                #   3. Phones & Emails
                heal_main_phone_and_email(cb)
                
                logger.info("Healing Incomes")
                #   4. Incomes
                heal_income(cb)
                
                logger.extra["stage"] = "IDENTITY_RESOLUTION"
                logger.info("Matching existing clients")
                
                # Step 3: Identity Resolution
                match_client_uuid(cb, target_table="clientes")
                
                logger.extra["stage"] = "FINAL_UPSERT"
                logger.info("Upserting valid information")
                
                # Step 4: Final Split (Production & Quarantine)
                push_to_production_and_quarantine(cb, target_table="clientes", team_code="TEAM:B", campaign="NEW_CLIENT")
            
            print("It's All Good, Man!")
            
    except psycopg2.DatabaseError as db_err:
        logger.error(f"Database operation failed: {db_err.pgerror}")
        raise
        
    except Exception as e:
        logger.error(f"Pipeline failed unexpectedly: {e}", exc_info=True)
        raise

    logger.extra["stage"] = "COMPLETE"
    logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    run_pipeline()