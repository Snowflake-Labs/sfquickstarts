USE TastyBytesDB;
GO
CREATE TABLE TastyBytes.EmployeeShift (

    ShiftID int IDENTITY(1,1) NOT NULL, 
    EmployeeName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    TruckID int NOT NULL, 
    ShiftDate date NOT NULL, 
    StartTime datetime NOT NULL, 
    EndTime datetime NOT NULL, 
    HoursWorked numeric(17, 6) NULL, 
    Role varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL CONSTRAINT [DF__EmployeeSh__Role__5CD6CB2B] DEFAULT ('Cook'), 
    HourlyRate smallmoney NOT NULL, 
    CreatedAt datetime NOT NULL CONSTRAINT [DF__EmployeeS__Creat__5DCAEF64] DEFAULT (getdate())
)