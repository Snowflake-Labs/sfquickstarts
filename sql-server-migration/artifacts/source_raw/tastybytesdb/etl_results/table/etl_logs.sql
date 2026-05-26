USE TastyBytesDB;
GO
CREATE TABLE etl_results.etl_logs (

    LogID int IDENTITY(1,1) NOT NULL, 
    name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL, 
    execution_date datetime NOT NULL
)