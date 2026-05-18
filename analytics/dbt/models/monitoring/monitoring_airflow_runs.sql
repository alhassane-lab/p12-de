-- Monitoring view exposing Airflow DAG run state with task-level aggregates.
with task_stats as (
    select
        dag_id,
        run_id,
        count(*) as task_count,
        count(*) filter (where state = 'success') as task_success_count,
        count(*) filter (where state = 'failed') as task_failed_count,
        count(*) filter (where state = 'running') as task_running_count,
        count(*) filter (where state = 'queued') as task_queued_count
    from public.task_instance
    group by dag_id, run_id
)
select
    d.dag_id,
    d.run_id,
    d.run_type,
    d.state as dag_state,
    d.external_trigger,
    d.execution_date,
    d.data_interval_start,
    d.data_interval_end,
    d.queued_at,
    d.start_date,
    d.end_date,
    extract(epoch from (coalesce(d.end_date, now()) - d.start_date)) as duration_seconds,
    coalesce(t.task_count, 0) as task_count,
    coalesce(t.task_success_count, 0) as task_success_count,
    coalesce(t.task_failed_count, 0) as task_failed_count,
    coalesce(t.task_running_count, 0) as task_running_count,
    coalesce(t.task_queued_count, 0) as task_queued_count
from public.dag_run d
left join task_stats t
    on d.dag_id = t.dag_id
   and d.run_id = t.run_id
