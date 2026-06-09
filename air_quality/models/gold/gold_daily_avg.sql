{{ config(materialized='table') }}

with base as (
    select * from {{ ref('silver_readings') }}
)

select
    cast(timestamp as date)   as date,
    year,
    station_code,
    pollutant,
    round(avg(value), 2)      as avg_value,
    count(*)                  as reading_count
from base
group by cast(timestamp as date), year, station_code, pollutant