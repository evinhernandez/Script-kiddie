FROM python:3.11-slim

WORKDIR /workspace
COPY . /workspace

RUN python -m pip install -U pip \
  && pip install -e packages/core -e packages/model_gateway -e apps/api

EXPOSE 8000
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000"]
