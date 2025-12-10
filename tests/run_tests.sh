#!/bin/bash

set -e

pushd /app/tests/terraform
terraform init && terraform plan && terraform apply -auto-approve
popd

wait_for_postgres.sh pytest --cov-report term --cov-report xml:/app/tests/cobertura.xml --cov=app --cov=lambdas "$@"

