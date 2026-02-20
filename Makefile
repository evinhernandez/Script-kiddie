SHELL := /bin/sh

POSTGRES_PASSWORD ?= scriptkiddie
REDIS_PASSWORD ?= scriptkiddie

.PHONY: docker-up docker-down test-docker

docker-up:
	cd infra && POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) REDIS_PASSWORD=$(REDIS_PASSWORD) docker compose up -d --build

docker-down:
	cd infra && POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) REDIS_PASSWORD=$(REDIS_PASSWORD) docker compose down

test-docker:
	docker run --rm -e PIP_ROOT_USER_ACTION=ignore -v "$$(pwd)":/workspace -w /workspace python:3.11-slim sh -lc "python -m pip install -U pip && pip install -e packages/core[dev] -e packages/model_gateway[dev] -e packages/cli[dev] -e apps/api[dev] && pytest -q packages/core/tests packages/model_gateway/tests packages/cli/tests apps/api/tests"
