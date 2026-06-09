{{ config(materialized='table') }}

with base as (
    select * from {{ ref('silver_readings') }}
)

select
    hour(timestamp)           as hour,
    year,
    station_code,
    pollutant,
    round(avg(value), 2)      as avg_value,
    count(*)                  as reading_count
from base
group by hour(timestamp), year, station_code, pollutant