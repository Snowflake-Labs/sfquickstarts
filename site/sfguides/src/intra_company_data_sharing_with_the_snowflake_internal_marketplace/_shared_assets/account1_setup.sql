--Login to your Primary Account from Step 1 and execute the following commands in a worksheet.

USE ROLE accountadmin;
SET my_user_var = CURRENT_USER();
ALTER USER identifier($my_user_var) SET DEFAULT_ROLE = accountadmin;

CREATE OR REPLACE WAREHOUSE compute_wh WAREHOUSE_SIZE=small INITIALLY_SUSPENDED=TRUE;
GRANT ALL ON WAREHOUSE compute_wh TO ROLE public;

-- Enable the ACCOUNTADMIN role for auto-fulfillment
USE ROLE orgadmin;
SELECT current_account_name(), current_region();
SELECT SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT('!FILL IN CURRENT_ACCOUNT_NAME()!');

-- Create another user in the primary account:

USE ROLE accountadmin;
CREATE ROLE domain3_admin_role;

CREATE OR REPLACE USER domain3_admin
  PASSWORD = 'FILL_IN_YOUR_PASSWORD'
  LOGIN_NAME = domain3_admin
  DISPLAY_NAME = domain3_admin
  EMAIL = 'FILL_IN_YOUR_EMAIL'
  MUST_CHANGE_PASSWORD = FALSE
  DEFAULT_WAREHOUSE = compute_wh
  DEFAULT_ROLE = domain3_admin_role
  COMMENT = 'Marketing domain admin';

GRANT ROLE domain3_admin_role TO USER domain3_admin;

-- Create a secondary account in the same region (default):
USE ROLE orgadmin;

CREATE ACCOUNT hol_account2
  admin_name = domain2_admin
  admin_password = 'FILL_IN_YOUR_PASSWORD'
  email = 'FILL_IN_YOUR_EMAIL'
  must_change_password = false
  edition = enterprise;

-- Create an organization account for admin purposes:
CREATE ORGANIZATION ACCOUNT hol_org_account
  admin_name = org_admin
  admin_password = 'FILL_IN_YOUR_PASSWORD'
  email = 'FILL_IN_YOUR_EMAIL'
  must_change_password = false
  edition = enterprise; 

– Make a note of your account names, URLs, and passwords! 
