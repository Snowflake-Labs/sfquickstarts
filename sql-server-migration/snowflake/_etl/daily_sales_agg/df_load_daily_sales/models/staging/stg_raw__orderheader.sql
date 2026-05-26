SELECT
   OrderID AS OrderID,
   CustomerID AS CustomerID,
   TruckID AS TruckID,
   OrderDate AS OrderDate,
   CompletedAt AS CompletedAt,
   OrderStatus AS OrderStatus,
   TotalAmount AS TotalAmount,
   TipAmount AS TipAmount,
   PaymentMethod AS PaymentMethod,
   OrderNotes AS OrderNotes,
   CreatedAt AS CreatedAt,
   ModifiedAt AS ModifiedAt
FROM
   {{ source('raw', 'OrderHeader') }}