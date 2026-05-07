-- Create monitoring and rule tables required by the orchestration layer.
create table if not exists monitoring.pipeline_runs (
    run_id text primary key,
    process_name text not null,
    status text not null,
    started_at timestamptz not null,
    finished_at timestamptz,
    details jsonb
);

create table if not exists monitoring.data_quality_anomalies_raw (
    anomaly_id text primary key,
    detected_at timestamptz not null,
    source_table text not null,
    record_id text,
    anomaly_type text not null,
    anomaly_detail text not null
);

create table if not exists raw.business_rules_raw (
    rule_version text primary key,
    effective_from date not null,
    office_address text not null,
    bonus_rate numeric(8, 4) not null,
    wellbeing_days integer not null,
    min_activities_per_year integer not null,
    max_km_walk_run numeric(10, 2) not null,
    max_km_cycle_scooter_other numeric(10, 2) not null,
    sportive_transport_modes jsonb not null,
    loaded_at timestamptz not null default now()
);
