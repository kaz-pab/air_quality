{{ config(materialized='table') }}

with source as (
    select *
    from read_parquet('D:/Projects/DE_PoC/bronze/*.parquet')
),

filtered as (
    select
        timestamp,
        station_code,
        value,
        pollutant,
        year
    from source
    where station_code like 'MzWar%'
      and value >= 0
      and value < 1000
)

select * from filtered