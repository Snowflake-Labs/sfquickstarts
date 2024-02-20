author: Swathi Jasti
id: developing_tasty_bytes_react_native_application_with_snowflake_sql_api_kr
summary: Developing Tasty Bytes React Native Data Application using Snowflake, SQL API
categories: Tasty-Bytes, Getting-Started, app-development
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, API, kr

# Tasty Bytes - SQL API로 React Native 데이터 애플리케이션 개발

<!-- ------------------------ -->
## 개요

duration: 2 <img src="assets/tasty_bytes_header.png"/>

오늘날의 데이터 주도적인 환경에서는 애플리케이션 대부분이 매우 데이터 집약적인 상태로 발전했습니다. 하지만 특히나 사용자 수가 늘어나고 데이터의 볼륨과 복잡성이 늘어남에 따라 성공적인 데이터 애플리케이션을 개발하는 것은 어려울 수 있습니다. Snowflake는 수많은 데이터 애플리케이션을 후방에서 지원합니다. 즉, 소프트웨어 팀이 엔지니어링 속도를 향상하고 운영 복잡성의 부담 없이 확장 가능한 애플리케이션을 만들 수 있도록 합니다. 엔지니어링 속도를 단축하는 것에 집중하기에 Snowflake는 뛰어난 애플리케이션 성능과 확장성을 제공합니다.

데이터 앱의 개발 속도를 단축하기 위해 Snowflake는 Snowflake 데이터베이스 내 데이터에 대한 원활한 액세스 및 조작을 가능하게 하는 RESTful API인 SQL API를 제공합니다. SQL API는 애플리케이션과 Snowflake 사이를 연결하는 다리입니다. 이를 통해 데이터를 프로그래밍 방식으로 검색 및 업데이트할 수 있습니다.

이 자습서에서 구축하는 애플리케이션은 가상의 푸드 트럭 회사인 Tasty Bytes와 Tasty Bytes의 트럭 기사가 고객의 주문을 확인하는 데 도움이 됩니다. 또한, 트럭 기사는 배달한 후 주문을 완료할 수 있습니다. 이 자습서는 트럭 기사를 위한 React Native 애플리케이션을 개발하는 데 SQL API를 활용하는 프로세스를 안내합니다.

### 사전 필요 조건 및 지식

- Snowflake에서 사용자, 데이터베이스 및 웨어하우스를 생성하는 데 필요한 권한
- 컴퓨터에서 소프트웨어를 설치 및 실행할 능력
- 기본적인 Git 사용 경험
- SQL에 대한 중급 수준의 지식
- Snowflake에서 SQL를 실행하기 위한 액세스

### 알아볼 내용

- Snowflake 및 SQL API를 사용하여 데이터 애플리케이션 개발하기
- 키 쌍 인증을 사용하여 Snowflake와 인증
- Javascript에서 JWT 토큰 생성하기

### 필요한 것

- [GitHub](https://github.com/) 계정
- [VSCode](https://code.visualstudio.com/download) 또는 선호하는 IDE 설치
- [NodeJS](https://nodejs.org/en/download/) 설치

### 구축할 것

- SQL API를 사용하는 데이터 애플리케이션

<!-- ------------------------ -->
## Snowflake에서 데이터 설정

duration: 3

이 데모를 위해 Tasty Bytes 주문 데이터를 사용합니다. 주문 데이터를 사용하여 다음 기능이 탑재된 트럭 기사를 위한 애플리케이션을 구축하게 됩니다.

- 트럭 기사는 대기열에서 주문을 확인할 수 있습니다.
- 기사는 Snowflake에서 주문 상태를 업데이트하여 준비가 되면 주문을 완료할 수 있습니다.
- 기사는 완료된 주문을 확인할 수 있습니다.

다음을 위해 Snowflake 웹 인터페이스인 [Snowsight](https://docs.snowflake.com/ko/user-guide/ui-snowsight.html#)를 사용하게 됩니다.

- Snowflake 객체(웨어하우스, 데이터베이스, 스키마) 생성
- S3에서 데이터 수집
- 데이터를 결합하여 뷰 생성

### 객체 생성, 데이터 로드 및 데이터 결합

Worksheets로 이동하고, 새로운 워크시트를 생성하기 위해 오른쪽 상단 모서리에 있는 ‘+’를 클릭하고, ‘SQL Worksheet’를 선택합니다.

워크시트에 다음 SQL을 붙여넣고 실행하여 Snowflake 객체(웨어하우스, 데이터베이스, 스키마)를 생성하고, S3에서 가공 전 주문 데이터를 수집하고, 다운스트림 사용을 위해 이를 모델링합니다.

```sql
-- use our accountadmin role
USE ROLE accountadmin;

-- create our database
CREATE OR REPLACE DATABASE frostbyte_tasty_bytes_app;

-- create raw, harmonized, and analytics schemas
-- raw zone for data ingestion
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_app.raw;

-- harmonized zone for data processing
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_app.harmonized;

-- analytics zone for data driven insights
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_app.analytics;

-- create csv file format
CREATE OR REPLACE FILE FORMAT frostbyte_tasty_bytes_app.raw.csv_ff 
type = 'csv';

-- create an external stage pointing to S3
CREATE OR REPLACE STAGE frostbyte_tasty_bytes_app.raw.s3load
COMMENT = 'Quickstarts S3 Stage Connection'
url = 's3://sfquickstarts/frostbyte_tastybytes/app/app_orders/'
file_format = frostbyte_tasty_bytes_app.raw.csv_ff;

-- create our raw.app_order_header table
CREATE OR REPLACE TABLE frostbyte_tasty_bytes_app.raw.app_order_header
(
  order_id NUMBER(19,0),
    month NUMBER(2,0),
    day NUMBER(2,0),
    hour NUMBER(2,0),
    minute NUMBER(2,0),
    second NUMBER(2,0),
    order_total NUMBER(19,3),
    order_tax_amount NUMBER(2,0),
    first_name VARCHAR,
    last_name VARCHAR,
    gender VARCHAR,
    order_status VARCHAR
);

-- create our raw.order_detail table
CREATE OR REPLACE TABLE frostbyte_tasty_bytes_app.raw.app_order_detail
(
  order_id NUMBER(19,0),
  order_detail_id NUMBER(19,0),
  menu_item_name VARCHAR,
  quantity NUMBER(2,0),
  unit_price NUMBER(19,3)
);

-- create our virtual warehouse
CREATE OR REPLACE WAREHOUSE tasty_app_wh AUTO_SUSPEND = 60;

-- use our TASTY_APP_WH virtual warehouse so we can load our data
USE WAREHOUSE tasty_app_wh;

-- ingest from S3 into the app_order_header table
COPY INTO frostbyte_tasty_bytes_app.raw.app_order_header
FROM @frostbyte_tasty_bytes_app.raw.s3load/app_order_header.csv.gz;

-- ingest from S3 into the app_order_detail table
COPY INTO frostbyte_tasty_bytes_app.raw.app_order_detail
FROM @frostbyte_tasty_bytes_app.raw.s3load/app_order_detail.csv.gz;

-- create our harmonized.data_app_orders_v view
CREATE OR REPLACE VIEW frostbyte_tasty_bytes_app.harmonized.data_app_orders_v
  AS
SELECT 
    oh.order_id,
    TIMESTAMP_NTZ_FROM_PARTS(YEAR(CURRENT_DATE()),oh.month,oh.day,oh.hour,oh.second, 0) AS order_ts,
    oh.order_total,
    oh.order_tax_amount,
    oh.first_name,
    oh.last_name,
    oh.gender,
    oh.order_status,
    od.order_detail_id,
    od.menu_item_name,
    od.quantity,
    od.unit_price
FROM frostbyte_tasty_bytes_app.raw.app_order_header oh
JOIN frostbyte_tasty_bytes_app.raw.app_order_detail od
ON oh.order_id = od.order_id;

-- promote our view to analytics
CREATE OR REPLACE VIEW frostbyte_tasty_bytes_app.analytics.data_app_orders_v
  AS
SELECT * FROM frostbyte_tasty_bytes_app.harmonized.data_app_orders_v;

-- view orders data
SELECT * FROM frostbyte_tasty_bytes_app.analytics.data_app_orders_v;
```

<!-- ------------------------ -->
## 애플리케이션을 위해 사용자 생성

duration: 5

강력한 보안 조치를 보장하려면 개인 계정과 분리된 애플리케이션을 위한 전용 사용자 계정을 생성하는 것이 필수적입니다. 이 새로운 계정은 Snowflake를 쿼리하는 데 활용됩니다. 모범 보안 사례에 따라 해당 계정은 키 쌍 인증을 사용하고 Snowflake 환경 내에서 제한된 액세스를 보유하게 됩니다.

### 1단계: 인증을 위해 공개 및 개인 키 생성

개인 및 공개 키를 생성하기 위해 다음 명령을 실행합니다. 이러한 키는 사용자를 Snowflake와 인증하는 데 필요합니다.

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_app_key 4096
$ openssl rsa -in snowflake_app_key -pubout -out snowflake_app_key.pub
```

### 2단계: Snowflake에서 사용자와 역할 생성 및 이 새로운 역할에 대한 데이터 액세스 부여

다음 SQL 문을 실행하여 사용자 계정을 생성하고 애플리케이션에 필요한 데이터에 대한 액세스를 부여합니다.

```SQL
-- use our securityadmin role
USE ROLE securityadmin;

-- create the tasty_bytes_data_app_demo role
CREATE OR REPLACE ROLE tasty_bytes_data_app_demo;

-- use our securityadmin role
USE ROLE accountadmin;

-- grant privileges to our tasty_bytes_data_app_demo role
GRANT USAGE ON WAREHOUSE tasty_app_wh TO ROLE tasty_bytes_data_app_demo;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes_app TO ROLE tasty_bytes_data_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_app.analytics TO ROLE tasty_bytes_data_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_app.harmonized TO ROLE tasty_bytes_data_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_app.raw TO ROLE tasty_bytes_data_app_demo;
GRANT SELECT ON ALL VIEWS IN SCHEMA frostbyte_tasty_bytes_app.analytics TO ROLE tasty_bytes_data_app_demo;
GRANT SELECT ON ALL VIEWS IN SCHEMA frostbyte_tasty_bytes_app.harmonized TO ROLE tasty_bytes_data_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_app.analytics TO ROLE tasty_bytes_data_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_app.harmonized TO ROLE tasty_bytes_data_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_app.raw TO ROLE tasty_bytes_data_app_demo;
GRANT UPDATE ON TABLE frostbyte_tasty_bytes_app.raw.app_order_header TO ROLE tasty_bytes_data_app_demo;

-- use our useradmin role
USE ROLE useradmin;

-- Open the ~/.ssh/snowflake_app_key.pub file from Step 1 and copy the contents starting just after the PUBLIC KEY header, 
-- and stopping just before the PUBLIC KEY footer for INSERT_RSA_PUBLIC_KEY_HERE.
CREATE OR REPLACE USER data_app_demo
RSA_PUBLIC_KEY='<INSERT_RSA_PUBLIC_KEY_HERE>' 
DEFAULT_ROLE=frostbyte_tasty_bytes_app 
DEFAULT_WAREHOUSE=tasty_app_wh 
MUST_CHANGE_PASSWORD=false;

-- use our securityadmin role
USE ROLE securityadmin;
GRANT ROLE tasty_bytes_data_app_demo TO USER data_app_demo;
```

<!-- ------------------------ -->
## SQL API를 사용하는 데이터 애플리케이션

duration: 10

실행할 애플리케이션은 React Native에서 작성되었습니다.

### 1단계: 소스 코드 가져오기

1. `git clone https://github.com/sf-gh-sjasti/TastyBytesReactNativeAppWithSnowflake-SQL_API.git reactNativeApp`을 사용하여 리포지토리를 복제합니다.
2. `cd reactNativeApp` 폴더로 이동합니다.
3. 종속성을 설치하기 위해 `npm install`을 실행합니다.

### 2단계: 애플리케이션 구성

1. VS Code 또는 선호하는 IDE에서 `reactNativeApp` 폴더를 엽니다.
2. `.env` 파일을 열고 개인 키로 `PRIVATE_KEY` 값을 업데이트합니다. 헤더(`-----BEGIN RSA PRIVATE KEY-----`) 및 푸터(`-----END RSA PRIVATE KEY-----`)를 비롯한 전체 개인 키를 `~/.ssh/snowflake_app_key.pub`에서 복사하여 붙여넣습니다.
3. us-west 리전에 있다면 Snowflake 계정으로 `SNOWFLAKE_ACCOUNT_IDENTIFIER`를 업데이트합니다. 또는, us-west 리전 외부에 있다면 `SNOWFLAKE_ACCOUNT_IDENTIFIER`를 '<SNOWFLAKE ACCOUNT>.<REGION>'으로 업데이트합니다. Snowflake에서 snowflake_account 값을 가져오려면 Snowsight에서 `SELECT CURRENT_ACCOUNT()`를 실행합니다. Snowflake에서 리전 값을 가져오려면 Snowsight에서 `SELECT CURRENT_REGION()`을 실행합니다. SNOWFLAKE_ACCOUNT_IDENTIFIER 및 SNOWFLAKE_ACCOUNT는 us-west에서도 동일합니다.
4. Snowflake 계정으로 `SNOWFLAKE_ACCOUNT`를 업데이트합니다.
5. 자신의 공개 키 지문으로 `PUBLIC_KEY_FINGERPRINT`를 업데이트합니다. 공개 키 지문을 가져오려면 Snowsight에서 `DESCRIBE USER data_app_demo ` SQL을 실행하여 RSA_PUBLIC_KEY_FP 속성 값을 가져옵니다.

### 3단계: 소스 코드 검토

SQL API를 사용하여 Snowflake와 인증하기 위해 키 쌍 인증을 사용합니다. JWT 토큰 생성 방법을 이해하기 위해 `Tokens.js`를 참고할 수 있습니다. `Orders.js`에는 Orders 화면을 렌더링하기 위한 소스 코드가 있습니다. 또한, SQL API 호출과 필요한 헤더를 시작하는 방법을 알아보기 위해 이 파일을 참고할 수 있습니다. `OrderDetails.js`에는 Order Details 화면을 렌더링하기 위한 소스 코드가 있습니다.

### 4단계: 애플리케이션 테스트

1. `npx expo start --clear`를 실행하고 `w` 키를 눌러 웹 브라우저에서 앱을 실행합니다.
2. 이렇게 하면 웹 브라우저에서 앱이 시작됩니다.
3. 시작된 후 InQueue Orders 화면을 확인할 수 있습니다.

<img src="assets/OrdersInQueue.png"/>

4. 이제 Order Details를 확인하기 위해 View Order 버튼을 클릭합니다.

<img src="assets/OrderDetails.png"/>

5. 주문을 완료하기 위해 ORDER READY 버튼을 클릭합니다. 이 작업은 해당 Order의 Order Status 값을 Completed로 업데이트하고 InQueue Orders 화면으로 리디렉션합니다.
6. 이제 완료된 주문을 확인하기 위해 Order History 탭을 클릭합니다.

<img src="assets/OrderHistory.png"/>

<!-- ------------------------ -->
## 정리

duration: 1

Snowsight Worksheets로 이동하고, 새로운 워크시트를 생성하기 위해 오른쪽 상단 모서리에 있는 ‘+’를 클릭하고, ‘SQL Worksheet’를 선택합니다. 워크시트에 다음 SQL을 붙여넣고 실행하여 Quickstart에서 생성한 Snowflake 객체를 드롭합니다.

```sql
USE ROLE accountadmin;
DROP DATABASE frostbyte_tasty_bytes_app;
DROP WAREHOUSE tasty_app_wh;

USE ROLE securityadmin;
DROP USER data_app_demo;
DROP ROLE tasty_bytes_data_app_demo;
```

<!-- ------------------------ -->
## 결론

duration: 1

### 결론

**끝났습니다!** Tasty Bytes - SQL API로 React Native 데이터 애플리케이션 개발 Quickstart를 성공적으로 완료하셨습니다.

이를 진행하면서 배운 내용은 다음과 같습니다.

- Snowflake 및 SQL API를 사용하여 데이터 애플리케이션 개발
- 키 쌍 인증을 사용하여 Snowflake와 인증
- Javascript에서 JWT 토큰 생성

### 다음 단계

Snowflake 데이터 클라우드에서의 여정을 계속하려면 아래 링크를 방문하여 사용 가능한 더 많은 Tasty Bytes - Quickstart를 확인하십시오.

- ### [Tasty Bytes 사용 - Quickstarts 목차](/guide/tasty_bytes_introduction_kr/index.html)
