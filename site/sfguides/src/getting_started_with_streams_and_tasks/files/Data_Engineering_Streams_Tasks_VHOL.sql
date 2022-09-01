--FILE:  Data_Engineering_Streams_Tasks_VHOL.sql
--SQL FILE for "Building Continuous Data Pipelines with Snowflake"

--** 1. Overview **
--** 2. Setting Up Snowflake **


--** 3. Begin Construction **

--3.a)  Create a new role for this Lab and grant permissions
use role ACCOUNTADMIN;
set myname = current_user();
create role if not exists VHOL;
grant role VHOL to user identifier($myname);
grant create database on account to role VHOL;
grant EXECUTE TASK, EXECUTE MANAGED TASK on ACCOUNT to role VHOL;
grant IMPORTED PRIVILEGES on DATABASE SNOWFLAKE to role VHOL;

--3.b)  Create a dedicated virtual warehouse for compute
create or replace warehouse VHOL_WH WAREHOUSE_SIZE = XSMALL, AUTO_SUSPEND = 5, AUTO_RESUME= TRUE;
grant all privileges on warehouse VHOL_WH to role VHOL;

--3.c)  Create Database used throughout this Lab
use role VHOL;
create or replace database VHOL_ST;
grant all privileges on database VHOL_ST to role VHOL;
use database VHOL_ST;
use schema PUBLIC;
use warehouse VHOL_WH;

--3.d)  Create an internal Stage
create or replace stage VHOL_STAGE
FILE_FORMAT = ( TYPE=JSON,STRIP_OUTER_ARRAY=TRUE );

--3.e)  Create a Staging/Landing Table
create or replace table CC_TRANS_STAGING (RECORD_CONTENT variant);


-- ** 4.Simulated Stream Source **

--Create Simulation Data Generation Stored Procedure (Using Snowpark Java)
create or replace procedure SIMULATE_KAFKA_STREAM(mystage STRING,prefix STRING,numlines INTEGER)
  RETURNS STRING
  LANGUAGE JAVA
  PACKAGES = ('com.snowflake:snowpark:latest')
  HANDLER = 'StreamDemo.run'
  AS
  $$
    import com.snowflake.snowpark_java.Session;
    import java.io.*;
    import java.util.HashMap;
    public class StreamDemo {
      public String run(Session session, String mystage,String prefix,int numlines) {
        SampleData SD=new SampleData();
        BufferedWriter bw = null;
        File f=null;
        try {
            f = File.createTempFile(prefix, ".json");
            FileWriter fw = new FileWriter(f);
	        bw = new BufferedWriter(fw);
            boolean first=true;
            bw.write("[");
            for(int i=1;i<=numlines;i++){
                if (first) first = false;
                else {bw.write(",");bw.newLine();}
                bw.write(SD.getDataLine(i));
            }
            bw.write("]");
            bw.close();
            return session.file().put(f.getAbsolutePath(),mystage,options)[0].getStatus();
        }
        catch (Exception ex){
            return ex.getMessage();
        }
        finally {
            try{
	            if(bw!=null) bw.close();
                if(f!=null && f.exists()) f.delete();
	        }
            catch(Exception ex){
	            return ("Error in closing:  "+ex);
	        }
        }
      }

      private static final HashMap<String,String> options = new HashMap<String, String>() {
        { put("AUTO_COMPRESS", "TRUE"); }
      };

      // sample data generator (credit card transactions)
    public static class SampleData {
      private static final java.util.Random R=new java.util.Random();
      private static final java.text.NumberFormat NF_AMT = java.text.NumberFormat.getInstance();
      String[] transactionType={"PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","PURCHASE","REFUND"};
      String[] approved={"true","true","true","true","true","true","true","true","true","true","false"};
      static {
        NF_AMT.setMinimumFractionDigits(2);
        NF_AMT.setMaximumFractionDigits(2);
        NF_AMT.setGroupingUsed(false);
      }

      private static int randomQty(int low, int high){
        return R.nextInt(high-low) + low;
      }

      private static double randomAmount(int low, int high){
        return R.nextDouble()*(high-low) + low;
      }

      private String getDataLine(int rownum){
        StringBuilder sb = new StringBuilder()
            .append("{")
            .append("\"element\":"+rownum+",")
            .append("\"object\":\"basic-card\",")
            .append("\"transaction\":{")
            .append("\"id\":"+(1000000000 + R.nextInt(900000000))+",")
            .append("\"type\":"+"\""+transactionType[R.nextInt(transactionType.length)]+"\",")
            .append("\"amount\":"+NF_AMT.format(randomAmount(1,5000)) +",")
            .append("\"currency\":"+"\"USD\",")
            .append("\"timestamp\":\""+java.time.Instant.now()+"\",")
            .append("\"approved\":"+approved[R.nextInt(approved.length)]+"")
            .append("},")
            .append("\"card\":{")
                .append("\"number\":"+ java.lang.Math.abs(R.nextLong()) +"")
            .append("},")
            .append("\"merchant\":{")
            .append("\"id\":"+(100000000 + R.nextInt(90000000))+"")
            .append("}")
            .append("}");
        return sb.toString();
      }
    }
}
$$;


--** 5. Develop and Testing **

--5.a)  Call SP to generate the compressed JSON load file
call SIMULATE_KAFKA_STREAM('@VHOL_STAGE','SNOW_',1000000);

--5.b)  Verify file was created in the internal stage
list @VHOL_STAGE PATTERN='.*SNOW_.*';

--5.c)  Load file into Staging Table  (about 100Mb raw json data per file).  Later, this will be setup to run repetitively on a schedule to simulate a real-time stream ingestion process.
copy into CC_TRANS_STAGING from @VHOL_STAGE PATTERN='.*SNOW_.*';

--5.d)  Now, there should be raw source JSON data in our Landing/Staging Table now stored in a VARIANT column.
select count(*) from CC_TRANS_STAGING;
select * from CC_TRANS_STAGING limit 10;

--5.e) Run Test Queries.  Now as a VARIANT datatype, the contents of the JSON is now understood.
select RECORD_CONTENT:card:number as card_id from CC_TRANS_STAGING limit 10;

select
RECORD_CONTENT:card:number::varchar,
RECORD_CONTENT:merchant:id::varchar,
RECORD_CONTENT:transaction:id::varchar,
RECORD_CONTENT:transaction:amount::float,
RECORD_CONTENT:transaction:currency::varchar,
RECORD_CONTENT:transaction:approved::boolean,
RECORD_CONTENT:transaction:type::varchar,
RECORD_CONTENT:transaction:timestamp::datetime
from CC_TRANS_STAGING
where RECORD_CONTENT:transaction:amount::float < 600 limit 10;

--5.f)  Create a View of Staging Table for real-time operational queries (normalize variant column to a full tabular representation)
create or replace view CC_TRANS_STAGING_VIEW (card_id, merchant_id, transaction_id, amount, currency, approved, type, timestamp ) as (
select
RECORD_CONTENT:card:number::varchar card_id,
RECORD_CONTENT:merchant:id::varchar merchant_id,
RECORD_CONTENT:transaction:id::varchar transaction_id,
RECORD_CONTENT:transaction:amount::float amount,
RECORD_CONTENT:transaction:currency::varchar currency,
RECORD_CONTENT:transaction:approved::boolean approved,
RECORD_CONTENT:transaction:type::varchar type,
RECORD_CONTENT:transaction:timestamp::datetime timestamp
from CC_TRANS_STAGING);

--5.g) We will be creating a stream, so we need to enable change tracking
alter table CC_TRANS_STAGING set CHANGE_TRACKING = true;
alter view CC_TRANS_STAGING_VIEW set CHANGE_TRACKING = true;

--5.h) Preview your View
select * from CC_TRANS_STAGING_VIEW limit 10;
select count(*) from CC_TRANS_STAGING_VIEW limit 10;

--5.i) Create a Stream on the operational view
create or replace stream CC_TRANS_STAGING_VIEW_STREAM on view CC_TRANS_STAGING_VIEW SHOW_INITIAL_ROWS=true;
select count(*) from CC_TRANS_STAGING_VIEW_STREAM;
select * from CC_TRANS_STAGING_VIEW_STREAM limit 10;

--5.j) Create Analytical table (normalized) for transformation (ELT) and easier user consumption (Staging table for landing can then be purged after X days)
create or replace table CC_TRANS_ALL (
card_id varchar,
merchant_id varchar,
transaction_id varchar,
amount float,
currency varchar,
approved boolean,
type varchar,
timestamp datetime);


--** 6.  Create Data Pipeline #1

--6.a)  Create Task
create or replace task GENERATE_TASK
WAREHOUSE=VHOL_WH
SCHEDULE = '1 minute'
COMMENT = 'Generates simulated real-time data for ingestion'
as
call SIMULATE_KAFKA_STREAM('@VHOL_STAGE','SNOW_',1000000);


--6.b)  View Definition of Task
describe task GENERATE_TASK;

--6.c)  Manually Run Task
execute task GENERATE_TASK;

--6.d) Monitor our Activities

--6.e)  Enable Task to Run on its Schedule
alter task GENERATE_TASK RESUME;

--6.f)  List Files in Stage now ready to be copied into Snowflake
list @VHOL_STAGE PATTERN='.*SNOW_.*';

--6.g)  Wait a couple minutes and then you should see that the Task is regularly generating and adding a new file to the Stage.
list @VHOL_STAGE PATTERN='.*SNOW_.*';

--6.h)  Create a Second Task
create or replace task PROCESS_FILES_TASK
USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
SCHEDULE = '3 minute'
COMMENT = 'Ingests Incoming Staging Datafiles into Staging Table'
as
copy into CC_TRANS_STAGING from @VHOL_STAGE PATTERN='.*SNOW_.*';

--6.i)  Check Staging Table, View, and Stream
select count(*) from CC_TRANS_STAGING;
select * from CC_TRANS_STAGING limit 10;
select count(*) from CC_TRANS_STAGING_VIEW_STREAM;
select * from CC_TRANS_STAGING_VIEW_STREAM limit 10;

--6.j)  Execute Task Manually
execute task PROCESS_FILES_TASK;

--6.k)  Query Staging View and its Stream
select count(*) from CC_TRANS_STAGING_VIEW;
select count(*) from CC_TRANS_STAGING_VIEW_STREAM;

--6.l)  Begin task to run on its schedule
alter task PROCESS_FILES_TASK resume;

--6.m)  Create Third Task
create or replace task REFINE_TASK
USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
SCHEDULE = '4 minute'
COMMENT = '2.  ELT Process New Transactions in Landing/Staging Table into a more Normalized/Refined Table (flattens JSON payloads)'
when
SYSTEM$STREAM_HAS_DATA('CC_TRANS_STAGING_VIEW_STREAM')
as
insert into CC_TRANS_ALL (select
card_id, merchant_id, transaction_id, amount, currency, approved, type, timestamp
from CC_TRANS_STAGING_VIEW_STREAM);

--6.n)  Query Analytical Table
select count(*) from CC_TRANS_ALL;

--6.o)  Query Staging Table's Stream
select count(*) from CC_TRANS_STAGING_VIEW_STREAM;

--6.p)  Run Task Manually
execute task REFINE_TASK;

--6.q)  Query Staging Table's Stream
select count(*) from CC_TRANS_ALL;
select count(*) from CC_TRANS_STAGING_VIEW_STREAM;

--6.r)  Schedule Task
alter task REFINE_TASK resume;

--6.s)  Reporting
--Reporting (For no latency, but only 14 days of retention)
select * from VHOL_ST.INFORMATION_SCHEMA.LOAD_HISTORY where SCHEMA_NAME=current_schema() and TABLE_NAME='CC_TRANS_STAGING';

--Reporting (Up to 90 minutes latency with this view, but 365 days of retention)
select * from SNOWFLAKE.ACCOUNT_USAGE.LOAD_HISTORY where SCHEMA_NAME=current_schema() and TABLE_NAME='CC_TRANS_STAGING';

--6.t)  Stop Tasks
alter task REFINE_TASK SUSPEND;
alter task PROCESS_FILES_TASK SUSPEND;
alter task GENERATE_TASK SUSPEND;

--6.u)  See how many transactions we have fully processed so far
select count(*) from CC_TRANS_ALL;


-- ** 7. Create Data Pipeline #2 **

--7.a)  Create Two Tasks
--First Task
create or replace task REFINE_TASK2
WAREHOUSE=VHOL_WH
as
insert into CC_TRANS_ALL (select
card_id, merchant_id, transaction_id, amount, currency, approved, type, timestamp
from CC_TRANS_STAGING_VIEW_STREAM);

--Second Task
create or replace task PROCESS_FILES_TASK2
WAREHOUSE=VHOL_WH
as
copy into CC_TRANS_STAGING from @VHOL_STAGE PATTERN='.*SNOW_.*';

--7.b)  Create Root Task
create or replace task LOAD_TASK
WAREHOUSE=VHOL_WH
SCHEDULE = '1 minute'
COMMENT = 'Full Sequential Orchestration'
as
call SIMULATE_KAFKA_STREAM('@VHOL_STAGE','SNOW_',1000000);

--7.c)  First Predecessor
--Have task REFINE_TASK2 be a predecessor of PROCESS_FILES_TASK2
alter task REFINE_TASK2 add after PROCESS_FILES_TASK2;
alter task REFINE_TASK2 RESUME;

--Have task LOAD_TASK be a predecessor of PROCESS_FILES_TASK2
alter task PROCESS_FILES_TASK2 add after LOAD_TASK;
alter task PROCESS_FILES_TASK2 RESUME;

--7.d)  View DAG Orchestration

--7.e)  Start LOAD Task
alter task LOAD_TASK RESUME;

--Wait, as task will run after one minute.  Then, see a file created in Stage
list @VHOL_STAGE PATTERN='.*SNOW_.*';

--7.f)  Tasks in Parallel
alter task LOAD_TASK SUSPEND;
create or replace task WAIT_TASK
  WAREHOUSE=VHOL_WH
  after PROCESS_FILES_TASK2
as
  call SYSTEM$wait(1);

--7.g)  Run Load Task
alter task WAIT_TASK RESUME;
alter task LOAD_TASK RESUME;

--7.h)  Monitor

--7.i)  Task Dependencies
select * from table(information_schema.task_dependents(task_name => 'LOAD_TASK', recursive => true));

--7.j)  Section is Complete
--Suspend your Tasks for this Section
alter task LOAD_TASK SUSPEND;
alter task REFINE_TASK2 SUSPEND;
alter task PROCESS_FILES_TASK2 SUSPEND;
alter task WAIT_TASK SUSPEND;


-- ** 8. Final Steps & Cleanup

--8.a)  See how many transactions we have processed
select count(*) from CC_TRANS_ALL;

--8.b) Let's look at our newest record now in your Analytical table:
select * from CC_TRANS_ALL order by TIMESTAMP desc limit 1;

--8.c)  See all tasks we have created, and to confirm their state are all "Suspended"
show tasks;

--8.d)    Drop Database, removing all objects created by this Lab (Optional)
--use role ACCOUNTADMIN;
--drop database if exists VHOL_ST;

--8.e)    Drop Warehouse (Optional)
--use role ACCOUNTADMIN;
--drop warehouse if exists VHOL_WH;

--8.f)    Drop Role (Optional)
--use role ACCOUNTADMIN;
--drop role if exists VHOL;

-- or if not Dropping Role, at least revoke these permissions
--use role ACCOUNTADMIN;
--revoke create database on account from role VHOL;
--revoke create warehouse on account from role VHOL;

-- ** #9 Conclusion **
--Congratulations, you have completed this Lab!
