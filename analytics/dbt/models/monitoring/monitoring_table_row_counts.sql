-- Monitoring view exposing current row counts for key pipeline tables.
select 'raw' as layer_name, 'rh_employees_raw' as table_name, count(*)::bigint as row_count
from raw.rh_employees_raw
union all
select 'raw', 'sport_declarations_raw', count(*)::bigint
from raw.sport_declarations_raw
union all
select 'raw', 'sport_activities_stream_raw', count(*)::bigint
from raw.sport_activities_stream_raw
union all
select 'silver', 'sil_employees', count(*)::bigint
from {{ ref('sil_employees') }}
union all
select 'silver', 'sil_sport_activities', count(*)::bigint
from {{ ref('sil_sport_activities') }}
union all
select 'gold', 'gold_kpi_employee_status', count(*)::bigint
from {{ ref('gold_kpi_employee_status') }}
union all
select 'gold', 'gold_employee_benefit_timeline', count(*)::bigint
from {{ ref('gold_employee_benefit_timeline') }}
union all
select 'gold', 'gold_employee_map', count(*)::bigint
from {{ ref('gold_employee_map') }}
