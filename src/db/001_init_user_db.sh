#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
    CREATE DATABASE ${DB_NAME};
    GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOSQL

psql -v ON_ERROR_STOP=1 --username "$DB_USER" --dbname "$DB_NAME" -f /docker-entrypoint-initdb.d/movies_db_schema.ddl
psql -v ON_ERROR_STOP=1 --username "$DB_USER" --dbname "$DB_NAME" -f /docker-entrypoint-initdb.d/movies_db_content.dump
