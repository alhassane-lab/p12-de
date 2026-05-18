-- Gold model consolidating quality anomalies detected across key business datasets.
with rules as (
    select *
    from {{ ref('business_rules_validity') }}
    where current_date >= effective_from
      and (effective_to_exclusive is null or current_date < effective_to_exclusive)
),
employee_anomalies as (
    select
        md5(employee_id || '-distance') as anomaly_id,
        current_timestamp as detected_at,
        'sil_employees' as table_name,
        employee_id as record_id,
        'distance_rule_issue' as anomaly_type,
        'Distance negative ou hors seuil reglementaire' as anomaly_detail
    from {{ ref('sil_employees') }}
    cross join rules
    where distance_km_to_office < 0
       or (
           transport_mode in ('marche', 'running', 'marche/running')
           and distance_km_to_office > rules.max_km_walk_run
       )
       or (
           transport_mode in ('velo', 'trottinette', 'roller', 'skate')
           and distance_km_to_office > rules.max_km_cycle_scooter_other
       )
),
salary_anomalies as (
    select
        md5(employee_id || '-salary') as anomaly_id,
        current_timestamp as detected_at,
        'sil_employees' as table_name,
        employee_id as record_id,
        'salary_issue' as anomaly_type,
        'Salaire brut non positif' as anomaly_detail
    from {{ ref('sil_employees') }}
    where gross_salary <= 0
),
activity_anomalies as (
    select
        md5(activity_id || '-activity') as anomaly_id,
        current_timestamp as detected_at,
        'sil_sport_activities' as table_name,
        activity_id as record_id,
        'invalid_activity' as anomaly_type,
        'Activite invalide detectee dans le flux' as anomaly_detail
    from {{ ref('sil_sport_activities') }}
    where not is_valid_activity
)
select * from employee_anomalies
union all
select * from salary_anomalies
union all
select * from activity_anomalies
