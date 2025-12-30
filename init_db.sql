-- Create Databases if they don't exist
-- Note: CREATE DATABASE cannot be run inside a transaction block or with IF NOT EXISTS in some PG versions
-- These satisfy the needs of both the API and Botpress

-- The user 'ricagoapi_user' is used by both the API and Botpress in the current .env setup
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ricagoapi_user') THEN
        CREATE ROLE ricagoapi_user WITH LOGIN PASSWORD 'changeme123';
    END IF;
END
$$;

-- Create databases if they don't exist
SELECT 'CREATE DATABASE ricagoapi' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ricagoapi')\gexec
SELECT 'CREATE DATABASE botpress' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'botpress')\gexec

-- Grant Permissions
ALTER DATABASE ricagoapi OWNER TO ricagoapi_user;
GRANT ALL PRIVILEGES ON DATABASE ricagoapi TO ricagoapi_user;

-- Botpress requires public schema permissions for its user
\c botpress
GRANT ALL PRIVILEGES ON SCHEMA public TO ricagoapi_user;
\c ricagoapi
GRANT ALL PRIVILEGES ON SCHEMA public TO ricagoapi_user;
