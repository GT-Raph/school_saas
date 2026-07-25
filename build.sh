#!/usr/bin/env bash

set -o errexit
set -o pipefail

echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Applying migrations..."
python manage.py migrate --no-input

echo "Synchronizing Render hostname..."
python manage.py sync_render_domain

echo "Bootstrapping platform administrator..."
python manage.py bootstrap_platform_admin

echo "Checking tenant integrity..."
python manage.py check_tenant_integrity

echo "Running deployment checks..."
python manage.py check --deploy

echo "Build completed."