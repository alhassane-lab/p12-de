-- Initialize the logical PostgreSQL schemas used by the POC pipeline.
create schema if not exists raw;
create schema if not exists bronze;
create schema if not exists silver;
create schema if not exists gold;
create schema if not exists monitoring;
