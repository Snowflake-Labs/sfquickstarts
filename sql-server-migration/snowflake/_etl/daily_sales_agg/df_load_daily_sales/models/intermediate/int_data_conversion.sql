WITH source_data AS
(
   SELECT
      OrderDate,
      TruckID,
      OrderID,
      OrderStatus,
      TotalAmount,
      TipAmount,
      Quantity
   FROM
      {{ ref('int_conditional_split_case_1') }}
)
SELECT
   OrderDate,
   TruckID,
   OrderID,
   OrderStatus,
   TotalAmount,
   TipAmount,
   Quantity,
   OrderDate :: DATE AS SaleDate
FROM
   source_data AS sd