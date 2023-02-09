CREATE ROLE servicenow_reader_role;
GRANT USAGE ON DATABASE SERVICENOW_DEST_DB TO ROLE servicenow_reader_role;
GRANT USAGE ON SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role; 
GRANT SELECT ON FUTURE TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;

GRANT ROLE servicenow_reader_role to role accountadmin;
USE DATABASE servicenow_dest_db;
USE SCHEMA dest_schema;

USE WAREHOUSE SERVICENOW_WAREHOUSE;

SELECT * FROM incident;
SELECT distinct upper(raw:) from incident;
SELECT upper(raw:description) c, count (raw:category) co from incident group by c order by co desc ;

SELECT upper(raw:category) cat, raw:task_effective_number num, upper(raw:description) des, count (raw:category) co from incident 
--where raw:task_effective_number = 'INC0008111' 
group by 1,2,3 order by cat desc;

--INC0008111