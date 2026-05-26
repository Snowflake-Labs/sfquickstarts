USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.OrderHeader (

    OrderID int IDENTITY(1,1) NOT NULL, 
    CustomerID int NOT NULL, 
    TruckID int NOT NULL, 
    OrderDate datetime NOT NULL CONSTRAINT [DF__OrderHead__Order__5165187F] DEFAULT (getdate()), 
    CompletedAt datetime NULL, 
    OrderStatus varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL CONSTRAINT [DF__OrderHead__Order__52593CB8] DEFAULT ('Pending'), 
    TotalAmount money NOT NULL CONSTRAINT [DF__OrderHead__Total__534D60F1] DEFAULT ((0.00)), 
    TipAmount money NULL CONSTRAINT [DF__OrderHead__TipAm__5441852A] DEFAULT ((0.00)), 
    PaymentMethod varchar(30) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    OrderNotes nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL, 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__OrderHead__Creat__5535A963] DEFAULT (getdate()), 
    ModifiedAt datetime NULL
)