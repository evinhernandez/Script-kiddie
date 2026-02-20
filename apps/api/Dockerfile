FROM python:3.11-slim

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /workspace
COPY . /workspace

RUN python -m pip install -U pip \
  && pip install -e packages/core -e packages/model_gateway -e apps/api

# Drop root privileges at runtime for both API and Celery worker containers.
RUN useradd --create-home --uid 10001 appuser \
  && chown -R appuser:appuser /workspace

EXPOSE 8000
USER appuser
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000"]
