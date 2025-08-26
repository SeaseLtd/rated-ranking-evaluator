#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
until bundle exec rails db:version > /dev/null 2>&1; do
  echo "Waiting for database connection..."
  sleep 2
done

echo "Preparing database..."
bundle exec rails db:prepare

echo "Database is ready."

# Then exec the container's original command - in this case app.command
exec "$@" # bundle exec puma -C config/puma.rb
