----    1 Overview

----    2 Set Up Snowflake (Using Snowsight)

----    3 Setting Up your Desktop

--3.e) Create limited-access ingestion account

use role ACCOUNTADMIN;
create role if not exists VHOL_CDC_AGENT;
create or replace user vhol_streaming1 COMMENT="Creating for VHOL";
alter user vhol_streaming1 set rsa_public_key='<Paste Your Public Key Here>';


----    4 Begin Construction

--4.a) Create a new roles for this Lab and grant permissions
use role ACCOUNTADMIN;
set myname = current_user();
create role if not exists VHOL;
grant role VHOL to user identifier($myname);
grant role VHOL_CDC_AGENT to user vhol_streaming1;

create role if not exists PII_ADMIN;
grant role PII_ADMIN to user identifier($myname);
create role if not exists PII_ALLOWED;
grant role PII_ALLOWED to user identifier($myname);

--4.b) Create Warehouse
create or replace warehouse VHOL_CDC_WH WAREHOUSE_SIZE = XSMALL, AUTO_SUSPEND = 5, AUTO_RESUME= TRUE;
grant all privileges on warehouse VHOL_CDC_WH to role VHOL;
grant usage on warehouse VHOL_CDC_WH to role VHOL_CDC_AGENT;

grant usage on warehouse VHOL_CDC_WH to role PII_ADMIN;
grant usage on warehouse VHOL_CDC_WH to role PII_ALLOWED;

--4.c) Create Database
create or replace database VHOL_ENG_CDC;
use database VHOL_ENG_CDC;
grant ownership on schema PUBLIC to role VHOL;
revoke all privileges on database VHOL_ENG_CDC from role ACCOUNTADMIN;
grant ownership on database VHOL_ENG_CDC to role VHOL;

use role VHOL;
use VHOL_ENG_CDC.ENG;
use warehouse VHOL_CDC_WH;
grant usage on database VHOL_ENG_CDC to role VHOL_CDC_AGENT;
create schema ENG;
grant usage on schema ENG to role VHOL_CDC_AGENT;
grant usage on database VHOL_ENG_CDC to role PUBLIC;
grant usage on schema PUBLIC to role PUBLIC;

--4.d) Create a Staging/Landing Table
create or replace table ENG.CDC_STREAMING_TABLE (RECORD_CONTENT variant);
grant insert on table ENG.CDC_STREAMING_TABLE to role VHOL_CDC_AGENT;
select * from ENG.CDC_STREAMING_TABLE;
select count(*) from ENG.CDC_STREAMING_TABLE;

----    5 Streaming Records!

--5.b)  View New Records in Snowflake
select count(*) from ENG.CDC_STREAMING_TABLE;
select * from ENG.CDC_STREAMING_TABLE limit 100;

select RECORD_CONTENT:transaction:primaryKey_tokenized::string as orderid from ENG.CDC_STREAMING_TABLE limit 10;

select
    RECORD_CONTENT:transaction:primaryKey_tokenized::varchar as orderid_tokenized,
    RECORD_CONTENT:transaction:record_after:orderid_encrypted::varchar as orderid_encrypted,
    RECORD_CONTENT:transaction:action::varchar as action,
    RECORD_CONTENT:transaction:committed_at::varchar as committed_at,
    RECORD_CONTENT:transaction:dbuser::varchar as dbuser,
    RECORD_CONTENT:transaction:record_before::variant as before,
    RECORD_CONTENT:transaction:record_after::variant as after
  from ENG.CDC_STREAMING_TABLE
  where RECORD_CONTENT:transaction:action::varchar='INSERT' limit 1000;

  --5.c) But There is More Than One Table in My Source System
  select distinct RECORD_CONTENT:transaction:schema::varchar,RECORD_CONTENT:transaction:table::varchar from ENG.CDC_STREAMING_TABLE;

  --5.d) We can also get metadata about the Client application's Channel.
  --Specifically the offset token identifying the source's indicator of the last successfully-committed row.
  show channels in table ENG.CDC_STREAMING_TABLE;



----    6 Create Dynamic Tables

--6.a) The Current State
CREATE OR REPLACE DYNAMIC TABLE ENG.LIMIT_ORDERS_CURRENT_DT
LAG = '1 minute'
WAREHOUSE = 'VHOL_CDC_WH'
AS
SELECT * EXCLUDE (score,action) from (
  SELECT
    RECORD_CONTENT:transaction:primaryKey_tokenized::varchar as orderid_tokenized,
    RECORD_CONTENT:transaction:record_after:orderid_encrypted::varchar as orderid_encrypted,
    TO_TIMESTAMP_NTZ(RECORD_CONTENT:transaction:committed_at::number/1000) as lastUpdated,
    RECORD_CONTENT:transaction:action::varchar as action,
    RECORD_CONTENT:transaction:record_after:client::varchar as client,
    RECORD_CONTENT:transaction:record_after:ticker::varchar as ticker,
    RECORD_CONTENT:transaction:record_after:LongOrShort::varchar as position,
    RECORD_CONTENT:transaction:record_after:Price::number(38,3) as price,
    RECORD_CONTENT:transaction:record_after:Quantity::number(38,3) as quantity,
    RANK() OVER (
        partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc) as score
  FROM ENG.CDC_STREAMING_TABLE
    WHERE
        RECORD_CONTENT:transaction:schema::varchar='PROD' AND RECORD_CONTENT:transaction:table::varchar='LIMIT_ORDERS'
)
WHERE score = 1 and action != 'DELETE';

SELECT count(*) FROM ENG.LIMIT_ORDERS_CURRENT_DT;

-- Wait for the lag (1 minute)
SELECT count(*) FROM LIMIT_ORDERS_CURRENT_DT;

--6.b) The Historical View (Slowly-Changing Dimensions / SCD)
CREATE OR REPLACE DYNAMIC TABLE ENG.LIMIT_ORDERS_SCD_DT
LAG = '1 minute'
WAREHOUSE = 'VHOL_CDC_WH'
AS
SELECT * EXCLUDE score from ( SELECT *,
  CASE when score=1 then true else false end as Is_Latest,
  LAST_VALUE(score) OVER (
            partition by orderid_tokenized order by valid_from desc)+1-score as version
  FROM (
      SELECT
        RECORD_CONTENT:transaction:primaryKey_tokenized::varchar as orderid_tokenized,
        --IFNULL(RECORD_CONTENT:transaction:record_after:orderid_encrypted::varchar,RECORD_CONTENT:transaction:record_before:orderid_encrypted::varchar) as orderid_encrypted,
        RECORD_CONTENT:transaction:action::varchar as action,
        IFNULL(RECORD_CONTENT:transaction:record_after:client::varchar,RECORD_CONTENT:transaction:record_before:client::varchar) as client,
        IFNULL(RECORD_CONTENT:transaction:record_after:ticker::varchar,RECORD_CONTENT:transaction:record_before:ticker::varchar) as ticker,
        IFNULL(RECORD_CONTENT:transaction:record_after:LongOrShort::varchar,RECORD_CONTENT:transaction:record_before:LongOrShort::varchar) as position,
        RECORD_CONTENT:transaction:record_after:Price::number(38,3) as price,
        RECORD_CONTENT:transaction:record_after:Quantity::number(38,3) as quantity,
        RANK() OVER (
            partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc) as score,
        TO_TIMESTAMP_NTZ(RECORD_CONTENT:transaction:committed_at::number/1000) as valid_from,
        TO_TIMESTAMP_NTZ(LAG(RECORD_CONTENT:transaction:committed_at::number/1000,1,null) over
                         (partition by orderid_tokenized order by RECORD_CONTENT:transaction:committed_at::number desc)) as valid_to
      FROM ENG.CDC_STREAMING_TABLE
      WHERE
            RECORD_CONTENT:transaction:schema::varchar='PROD' AND RECORD_CONTENT:transaction:table::varchar='LIMIT_ORDERS'
    ))
;

select  count(*) from LIMIT_ORDERS_SCD_DT;
--wait the lag period (~ 1 minute)
select  * from LIMIT_ORDERS_SCD_DT  limit 1000;

--- should have all 1M records, plus some
select  count(*) from LIMIT_ORDERS_SCD_DT;

--6.c) Aggregations / Summary Table
CREATE OR REPLACE DYNAMIC TABLE ENG.LIMIT_ORDERS_SUMMARY_DT
LAG = '1 minute'
WAREHOUSE = 'VHOL_CDC_WH'
AS
SELECT ticker,position,min(price) as MIN_PRICE,max(price) as MAX_PRICE, TO_DECIMAL(avg(price),38,2) as AVERAGE_PRICE,
    SUM(quantity) as TOTAL_SHARES,TO_DECIMAL(TOTAL_SHARES*AVERAGE_PRICE,38,2) as TOTAL_VALUE_USD
from (
  SELECT
    RECORD_CONTENT:transaction:action::varchar as action,
    RECORD_CONTENT:transaction:record_after:ticker::varchar as ticker,
    RECORD_CONTENT:transaction:record_after:LongOrShort::varchar as position,
    RECORD_CONTENT:transaction:record_after:Price::number(38,3) as price,
    RECORD_CONTENT:transaction:record_after:Quantity::number(38,3) as quantity
  FROM ENG.CDC_STREAMING_TABLE
  WHERE
        RECORD_CONTENT:transaction:schema::varchar='PROD' AND RECORD_CONTENT:transaction:table::varchar='LIMIT_ORDERS'
  QUALIFY RANK() OVER (
        partition by RECORD_CONTENT:transaction:primaryKey_tokenized::varchar order by RECORD_CONTENT:transaction:committed_at::number desc) = 1
)
WHERE action != 'DELETE' group by ticker,position order by position,TOTAL_VALUE_USD DESC
;

-- You know to wait for the Lag by now
select * from LIMIT_ORDERS_SUMMARY_DT where position='LONG' order by TOTAL_VALUE_USD;
--We are tracking the 30 Dow Jones Industrial Average Stocks (both Long and Short Limit Orders)
select  count(*) from LIMIT_ORDERS_SUMMARY_DT;

--6.e) Create a view for consumers
create or replace view PUBLIC.CURRENT_LIMIT_ORDERS_VW
  as select orderid_tokenized, lastUpdated,client,ticker,position,quantity,price
  FROM ENG.LIMIT_ORDERS_CURRENT_DT order by orderid_tokenized;

grant select on view PUBLIC.CURRENT_LIMIT_ORDERS_VW to role PUBLIC;

select * from PUBLIC.CURRENT_LIMIT_ORDERS_VW limit 1000;



----- *************************   PII Section    *****************************************************

----    7 Handling PII/Sensitive Data

--7.a) Create roles and assign ownerships & access
use role VHOL;
use database VHOL_ENG_CDC;
create or replace schema PII COMMENT='Stay Out - Authorized Users Only';
grant ownership on schema PII to role PII_ADMIN;
grant usage on database VHOL_ENG_CDC to role PII_ADMIN;
grant usage on database VHOL_ENG_CDC to role PII_ALLOWED;
grant usage on schema ENG to role PII_ADMIN;
grant usage on schema ENG to role PII_ALLOWED;
grant select,references on dynamic table ENG.LIMIT_ORDERS_CURRENT_DT to role PII_ADMIN;
grant select on dynamic table ENG.LIMIT_ORDERS_CURRENT_DT to role PII_ALLOWED;

--7.b) Become PII_ADMIN
use role PII_ADMIN;
use schema VHOL_ENG_CDC.PII;
use warehouse VHOL_CDC_WH;

--7.c) Reusable Decryption Secure Function
CREATE OR REPLACE SECURE FUNCTION PII._DECRYPT_AES(FIELD string, ENCRYPTIONKEY string)
RETURNS VARCHAR
LANGUAGE JAVA
HANDLER = 'Decrypt.decryptField'
AS
$$;
import java.security.Key;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

class Decrypt {
    private static final String ALGORITHM = "AES";
    private Key KEY;
    private KeyGenerator KEYGENERATOR;
    private Cipher CIPHER;
    public Decrypt() throws Exception{
        CIPHER = Cipher.getInstance(ALGORITHM);
    }
    public String decryptField(String field, String encryptionKey) {
        try {
            setKey(encryptionKey);
            CIPHER.init(Cipher.DECRYPT_MODE, KEY);
            byte[] decodedBytes=CIPHER.doFinal(Base64.getDecoder().decode(field));
            return new String(decodedBytes, StandardCharsets.UTF_8);
        }
        catch (Exception ex){
            return ex.getMessage();
        }
  }
  public void setKey(String k) throws Exception {
        byte[] k0 = new String(k.toCharArray()).getBytes(StandardCharsets.UTF_8);
        SecretKeySpec secretKey = new SecretKeySpec(k0,ALGORITHM);
        KEY=secretKey;
  }
}
$$;

grant usage on function PII._DECRYPT_AES(string,string) to role PII_ADMIN;
select PII._DECRYPT_AES('NhVcyJa8/r3Wdy6WNvT0yQw+SouNYGPAy/ddVe6064Y=', 'O90hS0k9qHdsMDkPe46ZcQ==') as orderid;

--7.d)  This Pipeline's Decryption Secure Function

CREATE OR REPLACE SECURE FUNCTION PII.DECRYPT_CDC_FIELD(FIELD string)
RETURNS VARCHAR
 as
 $$
 select PII._DECRYPT_AES(FIELD, 'O90hS0k9qHdsMDkPe46ZcQ==')
 $$;

grant usage on function PII.DECRYPT_CDC_FIELD(varchar) to role PII_ADMIN;
select PII.DECRYPT_CDC_FIELD('NhVcyJa8/r3Wdy6WNvT0yQw+SouNYGPAy/ddVe6064Y=');

revoke usage on function PII.DECRYPT_CDC_FIELD(varchar) from role PII_ADMIN;

--7.e)  Create Secure View
Create or replace secure view PII.LIMIT_ORDERS_VW
as
  select orderid_tokenized,orderid_encrypted,
    PII.DECRYPT_CDC_FIELD(orderid_encrypted) as orderid_PII,
    lastUpdated,client,ticker,position,price,quantity
  from ENG.LIMIT_ORDERS_CURRENT_DT order by orderid_PII;

grant usage on schema PII to role PII_ALLOWED;
grant usage on function PII._DECRYPT_AES(string,string) to role PII_ALLOWED;
grant usage on function PII.DECRYPT_CDC_FIELD(varchar) to role PII_ALLOWED;
grant select on view PII.LIMIT_ORDERS_VW to role PII_ALLOWED;

--7.f)  Be PII-Enabled
use role PII_ALLOWED;
use VHOL_ENG_CDC.PII;
select * from PII.LIMIT_ORDERS_VW order by ORDERID_PII limit 1000;
select * from PII.LIMIT_ORDERS_VW where ticker='MMM' and position='LONG' order by ORDERID_PII;
select * from PII.LIMIT_ORDERS_VW limit 1000;

----    8 Check Security

--8.b) See how many transactions you have processed
use role VHOL;
select count(*) from ENG.CDC_STREAMING_TABLE;

--(Optionall Cleanup Steps c,d,e,f)
--drop database VHOL_ENG_CDC;

--use role ACCOUNTADMIN;
--drop warehouse VHOL_CDC_WH;

--drop role VHOL;
--drop role VHOL_CDC_AGENT;
--drop role PII_ADMIN;
--drop role PII_ALLOWED;

