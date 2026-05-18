-- Silver model cleaning employee data and enriching it with distance-based eligibility flags.
with deduplicated as (
    select
        *,
        row_number() over (
            partition by employee_id
            order by ingested_at desc, row_hash desc
        ) as rn
    from {{ ref('brz_rh_employees') }}
    where employee_id is not null
),
rules as (
    select *
    from {{ ref('business_rules_validity') }}
    where is_current
),
normalized as (
    select
        d.employee_id,
        d.last_name,
        d.first_name,
        concat_ws(' ', d.first_name, d.last_name) as full_name,
        {{ xl_serial_to_date('d.birth_date_raw') }} as birth_date,
        {{ xl_serial_to_date('d.hire_date_raw') }} as hire_date,
        d.business_unit,
        cast(nullif(d.gross_salary_raw, '') as numeric(12, 2)) as gross_salary,
        d.contract_type,
        cast(nullif(d.cp_days_raw, '') as integer) as cp_days,
        d.home_address,
        lower(
            translate(
                coalesce(d.declared_transport_mode, 'inconnu'),
                'éèêëàâäîïôöùûüç',
                'eeeeaaaiioouuuc'
            )
        ) as declared_transport_mode_normalized
    from deduplicated d
    where d.rn = 1
),
coords as (
    select
        n.*,
        -- In this POC the address is converted into deterministic pseudo-coordinates.
        -- That keeps the demo fully offline while still allowing distance-based rules.
        {{ pseudo_geocode_lat('n.home_address') }} as home_lat,
        {{ pseudo_geocode_lon('n.home_address') }} as home_lon,
        43.5652::numeric(10, 6) as office_lat,
        3.9029::numeric(10, 6) as office_lon
    from normalized n
),
distance_calc as (
    select
        c.*,
        {{ haversine_km('c.home_lat', 'c.home_lon', 'c.office_lat', 'c.office_lon') }} as distance_km_to_office
    from coords c
)
select
    d.employee_id,
    d.last_name,
    d.first_name,
    d.full_name,
    d.birth_date,
    d.hire_date,
    d.business_unit,
    d.gross_salary,
    d.contract_type,
    d.cp_days,
    d.home_address,
    d.declared_transport_mode_normalized as transport_mode,
    d.home_lat,
    d.home_lon,
    d.office_lat,
    d.office_lon,
    d.distance_km_to_office,
    -- Sportive transport eligibility is based on normalized declared modes.
    case
        when d.declared_transport_mode_normalized in (
            select jsonb_array_elements_text(rules.sportive_transport_modes)
            from rules
        )
            then true
        else false
    end as is_transport_mode_sportive,
    -- Distance thresholds are externalized in business_rules so they can be replayed
    -- without rewriting the transformation logic.
    case
        when d.declared_transport_mode_normalized in ('marche', 'running', 'marche/running')
            then d.distance_km_to_office <= (select max_km_walk_run from rules)
        when d.declared_transport_mode_normalized in ('velo', 'trottinette', 'roller', 'skate', 'velo/trottinette/autres')
            then d.distance_km_to_office <= (select max_km_cycle_scooter_other from rules)
        else false
    end as is_distance_rule_valid
from distance_calc d
