SELECT
   OrderID AS OrderID,
   LineNumber AS LineNumber,
   MenuItemID AS MenuItemID,
   Quantity AS Quantity,
   UnitPrice AS UnitPrice,
   Discount AS Discount,
   LineTotal AS LineTotal,
   SpecialRequests AS SpecialRequests
FROM
   {{ source('raw', 'OrderDetail') }}