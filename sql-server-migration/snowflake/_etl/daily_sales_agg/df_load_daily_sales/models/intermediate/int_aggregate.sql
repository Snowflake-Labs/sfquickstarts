WITH source_data AS
(
   SELECT
      TotalAmount,
      TipAmount,
      Quantity,
      TruckID,
      SaleDate,
      OrderID,
      OrderDate,
      OrderStatus
   FROM
      {{ ref('int_data_conversion') }}
)
SELECT
   SUM(Quantity) AS Quantity,
   SUM(TipAmount) AS TipAmount,
   SUM(TotalAmount) AS TotalAmount,
   TruckID,
   SaleDate,
   COUNT(DISTINCT OrderID) AS OrderCount
FROM
   source_data
GROUP BY
   TruckID,
   SaleDate