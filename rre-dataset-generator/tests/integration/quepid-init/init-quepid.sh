#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
# This is a simple loop, a more robust solution might use a tool like wait-for-it.sh
until bundle exec rails db:version > /dev/null 2>&1; do
  echo "Waiting for database connection..."
  sleep 2
done

# Create the database if it doesn't exist
# The `db:prepare` task will create the DB, load the schema, and run migrations.
# It's safer than running `db:create` and `db:migrate` separately.
echo "Preparing database..."
bundle exec rails db:prepare

echo "Database is ready."

# Then exec the container's original command
exec "$@"
