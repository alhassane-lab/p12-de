-- Create the landing tables used for raw ingestion and event persistence.
create table if not exists raw.rh_employees_raw (
    ingestion_id text not null,
    ingested_at timestamptz not null default now(),
    process_date date not null,
    source_file text not null,
    employee_id text,
    last_name text,
    first_name text,
    birth_date_raw text,
    business_unit text,
    hire_date_raw text,
    gross_salary_raw text,
    contract_type text,
    cp_days_raw text,
    home_address text,
    declared_transport_mode text,
    row_hash text not null
);

create table if not exists raw.sport_declarations_raw (
    ingestion_id text not null,
    ingested_at timestamptz not null default now(),
    process_date date not null,
    source_file text not null,
    employee_id text,
    declared_sport text,
    row_hash text not null
);

create table if not exists raw.sport_activities_stream_raw (
    event_id text primary key,
    process_date date not null,
    topic text not null,
    partition_id integer not null,
    offset_id bigint not null,
    event_ts timestamptz not null,
    consumed_at timestamptz not null default now(),
    payload_json jsonb not null
);

create table if not exists raw.slack_messages_raw (
    message_id text primary key,
    process_date date not null,
    activity_id text not null,
    employee_id text not null,
    channel_name text not null,
    message_text text not null,
    generated_at timestamptz not null,
    status text not null
);
