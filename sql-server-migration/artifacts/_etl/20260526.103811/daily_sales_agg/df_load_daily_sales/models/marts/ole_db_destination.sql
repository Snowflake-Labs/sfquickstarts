{{ config(
    alias='DailySalesAgg'
) }}
WITH source_data AS
(
   SELECT
      TruckID,
      SaleDate,
      OrderCount,
      TotalAmount,
      TipAmount,
      Quantity
   FROM
      {{ ref('int_aggregate') }}
)
SELECT
   sd.TruckID AS TruckID,
   sd.SaleDate AS SaleDate,
   sd.OrderCount AS OrderCount,
   sd.TotalAmount :: NUMBER(18, 4) AS GrossRevenue,
   sd.TipAmount :: NUMBER(18, 4) AS TotalTips,
   sd.Quantity AS ItemsSold
FROM
   source_data AS sd