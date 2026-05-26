SELECT
   --** SSC-FDM-SSIS0004 - ADD AN ORDER BY CLAUSE TO ENSURE SORTED OUTPUT. THE SSIS MERGE JOIN TRANSFORMATION ASSUMES SORTED INPUTS AND NATURALLY PRODUCES A SORTED, DETERMINISTIC OUTPUT. THE EQUIVALENT SQL JOIN DOES NOT GUARANTEE ORDER. **
   orderheader.TruckID,
   orderheader.OrderID,
   orderheader.OrderDate,
   orderheader.OrderStatus,
   orderheader.TotalAmount,
   orderheader.TipAmount,
   orderdetailsource.Quantity
FROM
   {{ ref('stg_raw__orderheader') }} AS orderheader
   INNER JOIN
      {{ ref('stg_raw__orderdetailsource') }} AS orderdetailsource
      ON EQUAL_NULL(orderheader.OrderID, orderdetailsource.OrderID)