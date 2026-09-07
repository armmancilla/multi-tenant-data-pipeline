# Multi-Tenant Data Pipeline Architecture

**Status: Active Development (Infrastructure Phase)**

### Note for Everyone reading this:
If you are reviewing this repository, you will notice that the core ETL data transformations are currently being drafted. **Why publish it now?** Because production systems must be built starting by the infrastructure level.

**What can you expect right now?** These are some of the features already available in the code provided:

* **Multi-Tenant Isolation:** Dynamic orchestrator routing between isolated `tenant_a` and `tenant_b` PostgreSQL environments.
* **Secure Provisioning:** Automated database initialization (`init.sh`).
* **Idempotent Migrations:** Production-safe schema state management utilizing `yoyo-migrations` with `.rollback.sql` fallbacks.
* **Least-Privilege Security:** Strict separation of concerns where Yoyo executes DDL as the superuser, provisioning restricted, schema-only access to the runtime `pipeline_user`.

### Tech Stack
* **Core:** Python 3.13, pandas, psycopg2, custom logger
* **Infrastructure:** Docker Compose, PostgreSQL 18, Linux/CLI
* **Data Engineering:** yoyo-migrations, custom Pipeline Orchestrator

### Architecture Breakdown
1. **`database`:** A persistent PostgreSQL container initialized dynamically via a secure shell entrypoint, establishing global roles and multi-tenant databases.
2. **`db-migrate`:** An ephemeral container that executes idempotent migrations across all tenants and establishes baseline table permissions before gracefully exiting.
3. **`elt-etl-pipeline`:** The main orchestrator. It uses Docker `depends_on` health checks to wait for the database to be ready and the migrations to succeed before securely executing the data ingestion flow via bind mounts.

### How to replicate it?
To test the container orchestration locally:

1. Clone the repository and configure your `.env` variables (though you can skip this part).
2. Place your raw ingestion files into `./data/tenant_a/` and `./data/tenant_a/` (ignored by Git to protect sensitive client data). Not currently available, you can try the containers logic.
3. Execute the pipeline:
   ```bash
   docker compose up --build