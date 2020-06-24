#!/bin/sh
# wait-for-postgres.sh

set -e

until PGPASSWORD=$DB_PASSWORD_RO psql -h "$DB_HOST_RO" -U "$DB_USER_RO" -d "$DATABASE_RO" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec "$@"