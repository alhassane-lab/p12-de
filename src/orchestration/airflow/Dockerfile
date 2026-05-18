FROM apache/airflow:2.10.2-python3.11

COPY requirements.txt /tmp/project-requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /tmp/project-requirements.txt \
    && pip install --no-cache-dir "dbt-postgres>=1.8,<1.9"
