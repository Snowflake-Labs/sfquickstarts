-- create users are roles for the demo
use role useradmin;
create role itc_admin;
create role marketing;
create role it;
create role infosec;
create role executive;

create user "roy@itcrowd"      
    default_warehouse=demo_wh default_role=it        password='usesomethinggoodthiswontwork' must_change_password = true;
create user "moss@itcrowd"     
    default_warehouse=demo_wh default_role=infosec   password='usesomethinggoodthiswontwork' must_change_password = true;
create user "jen@itcrowd"      
    default_warehouse=demo_wh default_role=it        password='usesomethinggoodthiswontwork' must_change_password = true;
create user "denholm@itcrowd"  
    default_warehouse=demo_wh default_role=executive password='usesomethinggoodthiswontwork' must_change_password = true;
create user "douglas@itcrowd"  
    default_warehouse=demo_wh default_role=marketing password='usesomethinggoodthiswontwork' must_change_password = true;
create user "richmond@itcrowd" 
    default_warehouse=demo_wh default_role=itc_admin password='usesomethinggoodthiswontwork' must_change_password = true;

-- ONLY USING PASSWORDS AT ALL SINCE THIS IS A DEMO WITH DUMMY DATA!!

-- OPTIONAL KEY PAIR STEP
-- alter user "roy@itcrowd" set rsa_public_key='MIIB...';
-- alter user "moss@itcrowd" set rsa_public_key='MIIB...';
-- alter user "jen@itcrowd" set rsa_public_key='MIIB...';
-- alter user "denholm@itcrowd" set rsa_public_key='MIIB...';
-- alter user "douglas@itcrowd" set rsa_public_key='MIIB...';
-- alter user "richmond@itcrowd" set rsa_public_key='MIIB...';

use role useradmin;
grant role itc_admin to user "richmond@itcrowd";
grant role marketing to user "douglas@itcrowd";
grant role it to user "roy@itcrowd";
grant role it to user "moss@itcrowd";
grant role infosec to user "moss@itcrowd";
grant role it to user "jen@itcrowd";
grant role executive to user "denholm@itcrowd";

use role <ROLE_THAT_OWNS_THE_WAREHOUSE>;
grant usage on warehouse <WAREHOUSE_YOU_WILL_USE> to role itc_admin;
grant usage on warehouse <WAREHOUSE_YOU_WILL_USE> to role marketing;
grant usage on warehouse <WAREHOUSE_YOU_WILL_USE> to role it;
grant usage on warehouse <WAREHOUSE_YOU_WILL_USE> to role executive;
grant usage on warehouse <WAREHOUSE_YOU_WILL_USE> to role infosec;

-- create objects to use as the demo objects
use role sysadmin;
create database REYNHOLM_IND_DATA;
grant ownership on database REYNHOLM_IND_DATA to role itc_admin;


-- start doing this as richmond@itcrowd or another user with itc_admin role
use role itc_admin;
create schema REYNHOLM_IND_DATA.BASEMENT WITH MANAGED ACCESS;
create table CUSTOMERS as (
    SELECT
        a.C_SALUTATION,
        a.C_FIRST_NAME,
        a.C_LAST_NAME,
        CASE UNIFORM(1,3,RANDOM()) WHEN 1 THEN 'UK' WHEN 2 THEN 'US' ELSE 'FRANCE' END AS C_BIRTH_COUNTRY,
        a.C_EMAIL_ADDRESS,
        b.CD_GENDER,
        b.CD_CREDIT_RATING,
        CASE UNIFORM(1,3,RANDOM()) WHEN 1 THEN 'YES' WHEN 2 THEN 'NO' ELSE NULL END AS OPTIN
    FROM
        SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER a,
        SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER_DEMOGRAPHICS b
    WHERE
        a.C_CUSTOMER_SK = b.CD_DEMO_SK and
        a.C_SALUTATION is not null and
        a.C_FIRST_NAME is not null and
        a.C_LAST_NAME is not null and
        a.C_BIRTH_COUNTRY is not null and
        a.C_EMAIL_ADDRESS is not null and
        b.CD_GENDER is not null and
        b.CD_CREDIT_RATING is not null
    LIMIT 200 )
;

-- grant rights to roles for the demo objects
grant usage on database REYNHOLM_IND_DATA to role itc_admin;
grant usage on database REYNHOLM_IND_DATA to role marketing;
grant usage on database REYNHOLM_IND_DATA to role it;
grant usage on database REYNHOLM_IND_DATA to role executive;
grant usage on database REYNHOLM_IND_DATA to role infosec;
grant usage on schema REYNHOLM_IND_DATA.BASEMENT to role itc_admin;
grant usage on schema REYNHOLM_IND_DATA.BASEMENT to role marketing;
grant usage on schema REYNHOLM_IND_DATA.BASEMENT to role it;
grant usage on schema REYNHOLM_IND_DATA.BASEMENT to role executive;
grant usage on schema REYNHOLM_IND_DATA.BASEMENT to role infosec;
-- NOPEgrant select on table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS to role itc_admin;
grant select on table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS to role marketing;
grant select on table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS to role it;
grant select on table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS to role executive;

select * from REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS limit 50;

-- start doing this as richmond@itcrowd or another user with itc_admin role

-- lock down the objects with column and row level security
grant CREATE ROW ACCESS POLICY on schema REYNHOLM_IND_DATA.BASEMENT to role infosec;
create table REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING (
  role_name varchar,
  national_letter varchar,
  allowed varchar
);
grant ownership on table REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING to role infosec;
grant create masking policy on schema REYNHOLM_IND_DATA.BASEMENT to role infosec;

-- this is done with your user with elevated rights
use role securityadmin;
grant ownership on table REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING to role infosec;
-- NOPE, blocked by Managed Access Schema
grant select on table REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING to role infosec;
grant insert on table REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING to role infosec;

-- start doing this as moss@itcrowd or another user with infosec role
use role infosec;
insert into REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING
  values
  ('ACCOUTADMIN','','FALSE'),
  ('ITC_ADMIN','','FALSE'),
  ('MARKETING','UK','TRUE'),
  ('IT','US','TRUE'),
  ('INFOSEC','','FALSE'),
  ('EXECUTIVE','FRANCE','TRUE');

use role infosec;
create or replace row access policy REYNHOLM_IND_DATA.BASEMENT.makes_no_sense as (C_BIRTH_COUNTRY varchar) returns boolean ->
  case
      -- check for full read access
      when exists ( 
            select 1 from REYNHOLM_IND_DATA.BASEMENT.ROW_ACCESS_MAPPING
              where role_name = current_role()
                and C_BIRTH_COUNTRY like national_letter
                and allowed = 'TRUE'
          ) then true
      -- control for the share
      when (
          invoker_share() in ('REYNHOLM_IND_DATA_SHARE')
          and C_BIRTH_COUNTRY='UK'
          ) then true
      -- always default deny
      else false
  end
;

-- granting apply rights won't work with managed access schema
--grant apply on row access policy REYNHOLM_IND_DATA.BASEMENT.makes_no_sense to role itc_admin;

use role securityadmin;
grant apply on row access policy REYNHOLM_IND_DATA.BASEMENT.makes_no_sense to role itc_admin;

-- start doing this as richmond@itcrowd or another user with itc_admin role
use role ITC_ADMIN;
alter table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS add row access policy REYNHOLM_IND_DATA.BASEMENT.makes_no_sense on (C_BIRTH_COUNTRY);
--alter table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS drop row access policy REYNHOLM_IND_DATA.BASEMENT.makes_no_sense;

-- start doing this as douglas@itcrowd or another user with marketing role
use role marketing;
select * from REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS limit 50;
-- study the results returned to see the effects of the row access policy

-- start doing this as moss@itcrowd or another user with infosec role
use role infosec;

-- conditional masking version
create masking policy REYNHOLM_IND_DATA.BASEMENT.hide_optouts as
(col_value varchar, optin string) returns varchar ->
  case
    when optin = 'YES' then col_value
    else '***MASKED***'
  end;
  
-- full column masking version, always masks
create masking policy REYNHOLM_IND_DATA.BASEMENT.hide_column_values as
(col_value varchar) returns varchar ->
  case
    when 1=1 then '***MASKED***'
    else '***MASKED***'
  end;

use role securityadmin;
grant apply on masking policy REYNHOLM_IND_DATA.BASEMENT.hide_optouts to role itc_admin;

-- start doing this as richmond@itcrowd or another user with itc_admin role
use role ITC_ADMIN;
alter table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS modify column C_EMAIL_ADDRESS
    set masking policy REYNHOLM_IND_DATA.BASEMENT.hide_optouts using (C_EMAIL_ADDRESS, OPTIN);

-- start doing this as douglas@itcrowd or another user with marketing role
use role marketing;
select * from REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS limit 50;

-- tag the objects
use role securityadmin;
grant create tag on schema REYNHOLM_IND_DATA.BASEMENT to role infosec;
use role accountadmin;
grant apply tag on account to role itc_admin;

-- start doing this as moss@itcrowd or another user with infosec role
use role infosec;
create tag REYNHOLM_IND_DATA.BASEMENT.peter;
create tag REYNHOLM_IND_DATA.BASEMENT.calendar;

-- start doing this as richmond@itcrowd or another user with itc_admin role
use role itc_admin;
alter table REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS set tag
    REYNHOLM_IND_DATA.BASEMENT.PETER = 'file',
    REYNHOLM_IND_DATA.BASEMENT.CALENDAR = 'geeks';
select system$get_tag('REYNHOLM_IND_DATA.BASEMENT.calendar', 'REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS', 'table') as CALENDAR;

-- start doing this as jen@itcrowd or another user with it role
use role it;
select extract_semantic_categories('REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS');

select VALUE from TABLE(FLATTEN(EXTRACT_SEMANTIC_CATEGORIES('REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS')::VARIANT:CD_GENDER)) AS f;

select 
    f.value:"privacy_category"::varchar as privacy_category,  
    f.value:"semantic_category"::varchar as semantic_category,
    f.value:"extra_info":"probability"::number(10,2) as probability
from 
    TABLE(
        FLATTEN(EXTRACT_SEMANTIC_CATEGORIES('REYNHOLM_IND_DATA.BASEMENT.CUSTOMERS')::VARIANT)
    ) AS f 
where f.key='CD_GENDER';

-- UNDO IT ALL
use role accountadmin;
drop share REYNHOLM_IND_DATA_SHARE;
use role itc_admin;
drop database REYNHOLM_IND_DATA;

use role useradmin;
drop user "roy@itcrowd";
drop user "moss@itcrowd";
drop user "jen@itcrowd";
drop user "denholm@itcrowd";
drop user "douglas@itcrowd";
drop user "richmond@itcrowd";
drop role itc_admin;
drop role marketing;
drop role it;
drop role infosec;
drop role executive;
