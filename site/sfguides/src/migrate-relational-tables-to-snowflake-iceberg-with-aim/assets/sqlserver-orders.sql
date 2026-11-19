-- Sample relational table for the Iceberg lab.
-- Run this on the SQL Server instance registered with `scai connection add-sql-server`.

IF DB_ID('IcebergLab') IS NULL
    CREATE DATABASE IcebergLab;
GO

USE IcebergLab;
GO

IF SCHEMA_ID('Sales') IS NULL
    EXEC('CREATE SCHEMA Sales');
GO

IF OBJECT_ID('Sales.Orders') IS NOT NULL
    DROP TABLE Sales.Orders;
GO

CREATE TABLE Sales.Orders (
    OrderId     INT            NOT NULL PRIMARY KEY,
    OrderTs     DATETIME2(6)   NOT NULL,
    Amount      DECIMAL(10, 2) NOT NULL,
    Notes       NVARCHAR(200)  NULL
);
GO

INSERT INTO Sales.Orders (OrderId, OrderTs, Amount, Notes) VALUES
    (1, '2024-03-15T14:30:00', 19.50, 'first order'),
    (2, '2024-06-01T09:00:00', 42.00, NULL),
    (3, '2024-11-20T18:45:00',  7.25, 'gift wrap');
GO
