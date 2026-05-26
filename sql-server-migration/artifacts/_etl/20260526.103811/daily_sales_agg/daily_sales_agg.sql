CREATE OR REPLACE TASK public.daily_sales_agg
COMMENT = '{ "description": "", "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
SELECT
   1;
CREATE OR REPLACE TASK public.daily_sales_agg_insert_start_log
WAREHOUSE=DUMMY_WAREHOUSE
AFTER public.daily_sales_agg
AS
BEGIN
   ---- Start block 'Package\insert_start_log'
   --** SSC-FDM-0007 - MISSING DEPENDENT OBJECT "etl_results.etl_logs" **
   INSERT INTO etl_results.etl_logs (name, execution_date) VALUES ('pkg_daily_sales_aggregate start', CURRENT_TIMESTAMP());
   ---- End block 'Package\insert_start_log'

END;

CREATE OR REPLACE TASK public.daily_sales_agg_df_load_daily_sales
WAREHOUSE=DUMMY_WAREHOUSE
AFTER public.daily_sales_agg_insert_start_log
AS
BEGIN
   ---- Start block 'Package\df_load_daily_sales'
   EXECUTE DBT PROJECT public.df_load_daily_sales ARGS='build --target dev';
   ---- End block 'Package\df_load_daily_sales'

END;

CREATE OR REPLACE TASK public.daily_sales_agg_insert_end_log
WAREHOUSE=DUMMY_WAREHOUSE
AFTER public.daily_sales_agg_df_load_daily_sales
AS
BEGIN
   ---- Start block 'Package\insert_end_log'
   --** SSC-FDM-0007 - MISSING DEPENDENT OBJECT "etl_results.etl_logs" **
   INSERT INTO etl_results.etl_logs (name, execution_date) VALUES ('pkg_daily_sales_aggregate start', CURRENT_TIMESTAMP());
   ---- End block 'Package\insert_end_log'

END;

