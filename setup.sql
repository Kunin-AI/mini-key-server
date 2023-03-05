-- create the databases
SELECT 'CREATE DATABASE keyserver'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keyserver')\gexec

-- create the users for each database
CREATE USER keyserver;
GRANT ALL PRIVILEGES ON DATABASE keyserver to keyserver;

-- FLUSH PRIVILEGES;
