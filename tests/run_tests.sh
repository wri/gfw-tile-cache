#!/bin/bash

set -e

# Clean Python cache to avoid stale bytecode issues
echo "Cleaning Python cache..."
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name "*.pyc" -delete 2>/dev/null || true

pushd /app/tests/terraform
terraform init && terraform plan && terraform apply -auto-approve
popd

wait_for_postgres.sh pytest --cov-report term --cov-report xml:/app/tests/cobertura.xml --cov=app --cov=lambdas "$@"
