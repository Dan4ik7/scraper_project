#!/bin/bash

# Wait for PostgreSQL to be ready
until psql -h $DB_HOST -U $POSTGRES_USER -d $DB_NAME -c '\q'; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
done

# Add a delay before running the Python script (adjust as needed)
sleep 10

# Run the Python script with password
PGPASSWORD=$POSTGRES_PASSWORD python 999_scrapper_final.py
