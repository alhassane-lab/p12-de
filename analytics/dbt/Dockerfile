FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --default-timeout=100 "dbt-postgres>=1.8,<1.9"
