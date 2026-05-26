WITH source_data AS
(
   SELECT
      TruckID,
      OrderID,
      OrderDate,
      OrderStatus,
      TotalAmount,
      TipAmount,
      Quantity
   FROM
      {{ ref('int_merge_join') }}
)
SELECT
   TruckID,
   OrderID,
   OrderDate,
   OrderStatus,
   TotalAmount,
   TipAmount,
   Quantity
FROM
   source_data
WHERE
   NOT (OrderStatus = 'Completed')