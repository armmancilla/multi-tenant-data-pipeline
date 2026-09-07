--
-- file: migrations/tenant_b/000_grant_db_public_permissions.rollback.sql
--

REVOKE USAGE ON SCHEMA public FROM pipeline_user;