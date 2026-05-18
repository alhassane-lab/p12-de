-- Gold snapshot model exposing employee activity and benefit eligibility over simulated activity dates.
with rules as (
    select *
    from {{ ref('business_rules_validity') }}
),
employees as (
    select
        employee_id,
        full_name,
        business_unit,
        contract_type,
        gross_salary,
        transport_mode,
        distance_km_to_office
    from {{ ref('sil_employees') }}
),
valid_activities as (
    select
        employee_id,
        process_date,
        activity_date,
        activity_id,
        distance_km,
        duration_min,
        calories_burned
    from {{ ref('sil_sport_activities') }}
    where is_valid_activity
),
snapshot_dates as (
    select distinct activity_date as snapshot_date
    from valid_activities
    where activity_date is not null
),
employee_snapshots as (
    select
        e.employee_id,
        e.full_name,
        e.business_unit,
        e.contract_type,
        e.gross_salary,
        e.transport_mode,
        e.distance_km_to_office,
        d.snapshot_date
    from employees e
    cross join snapshot_dates d
),
timeline as (
    select
        s.employee_id,
        s.full_name,
        s.business_unit,
        s.contract_type,
        s.snapshot_date,
        s.transport_mode,
        s.distance_km_to_office,
        count(a.activity_id) filter (
            where a.activity_date = s.snapshot_date
        ) as activity_count_on_date,
        round(coalesce(sum(a.distance_km) filter (
            where a.activity_date = s.snapshot_date
        ), 0)::numeric, 2) as distance_km_on_date,
        coalesce(sum(a.duration_min) filter (
            where a.activity_date = s.snapshot_date
        ), 0) as duration_min_on_date,
        count(a.activity_id) as activity_count_12m,
        count(distinct a.activity_date) as sport_days_count_12m,
        max(a.activity_date) as last_activity_date,
        max(a.process_date) as last_process_date,
        case
            when r.sportive_transport_modes ? s.transport_mode and (
                (s.transport_mode in ('marche', 'running', 'marche/running') and s.distance_km_to_office <= r.max_km_walk_run)
                or
                (s.transport_mode in ('velo', 'trottinette', 'roller', 'skate', 'velo/trottinette/autres') and s.distance_km_to_office <= r.max_km_cycle_scooter_other)
            ) then true
            else false
        end as is_bonus_eligible,
        round((s.gross_salary * r.bonus_rate)::numeric, 2) as potential_bonus_amount,
        case
            when r.sportive_transport_modes ? s.transport_mode and (
                (s.transport_mode in ('marche', 'running', 'marche/running') and s.distance_km_to_office <= r.max_km_walk_run)
                or
                (s.transport_mode in ('velo', 'trottinette', 'roller', 'skate', 'velo/trottinette/autres') and s.distance_km_to_office <= r.max_km_cycle_scooter_other)
            )
                then round((s.gross_salary * r.bonus_rate)::numeric, 2)
            else 0::numeric
        end as bonus_amount,
        case
            when not (r.sportive_transport_modes ? s.transport_mode) then 'transport_non_sportif'
            when not (
                (s.transport_mode in ('marche', 'running', 'marche/running') and s.distance_km_to_office <= r.max_km_walk_run)
                or
                (s.transport_mode in ('velo', 'trottinette', 'roller', 'skate', 'velo/trottinette/autres') and s.distance_km_to_office <= r.max_km_cycle_scooter_other)
            ) then 'distance_hors_regle'
            else 'eligible'
        end as bonus_reason,
        case
            when count(a.activity_id) >= r.min_activities_per_year then true
            else false
        end as is_wellbeing_eligible,
        case
            when count(a.activity_id) >= r.min_activities_per_year then r.wellbeing_days
            else 0
        end as wellbeing_days_awarded,
        case
            when count(a.activity_id) >= r.min_activities_per_year then 'eligible'
            else 'insufficient_activities'
        end as wellbeing_reason,
        r.rule_version
    from employee_snapshots s
    inner join rules r
        on s.snapshot_date >= r.valid_from_inclusive
       and (r.effective_to_exclusive is null or s.snapshot_date < r.effective_to_exclusive)
    left join valid_activities a
        on s.employee_id = a.employee_id
       and a.activity_date between s.snapshot_date - interval '365 days' and s.snapshot_date
    group by
        s.employee_id,
        s.full_name,
        s.business_unit,
        s.contract_type,
        s.snapshot_date,
        s.transport_mode,
        s.distance_km_to_office,
        s.gross_salary,
        r.bonus_rate,
        r.min_activities_per_year,
        r.wellbeing_days,
        r.max_km_walk_run,
        r.max_km_cycle_scooter_other,
        r.sportive_transport_modes,
        r.rule_version
)
select *
from timeline
