author: Swathi Jasti
id: developing_tasty_bytes_react_native_application_with_snowflake_sql_api_ja
summary: Snowflakeを使用したTasty Bytes React Nativeデータアプリケーションの開発、SQL API
categories: Tasty-Bytes, Getting-Started, app-development
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, API, ja

# Tasty Bytes - SQL APIによるReact Nativeデータアプリケーションの開発

<!-- ------------------------ -->
## 概要

Duration: 2 <img src="assets/tasty_bytes_header.png"/>

現代のデータドリブンな状況においては、アプリケーションの大半が高度にデータ集約的なものへと進化しています。しかし、特にユーザー数が増加し、データの量と複雑さが増している中では、優れたデータアプリケーションの開発が困難となる場合があります。Snowflakeは、多くのデータアプリケーションを支える原動力であり、ソフトウェアチームがエンジニアリングを迅速化し、運用上の複雑さに煩わされず、スケーラブルなアプリケーションを作成できるようにします。Snowflakeは、エンジニアリングの迅速化に重点を置いており、極めて高いパフォーマンスとスケーラビリティをアプリケーションに提供します。

Snowflakeは、データアプリの開発を促進するためにSQL APIを提供しています。SQL APIは、Snowflakeデータベース内でのデータのシームレスなアクセスと操作を可能にするRESTful APIです。SQL APIは、お使いのアプリケーションとSnowflakeの橋渡しの役割を果たし、プログラムによるデータの取得と更新を可能にします。

このチュートリアルでは、架空のキッチンカー会社であるTasty Bytesとキッチンカーの運転手が顧客からの注文を確認し、運転手が配達時に注文を完了処理できるアプリケーションを作成します。このチュートリアルでは、SQL APIを活用してキッチンカー運転手向けのReact Nativeアプリケーションを開発するプロセスについて説明します。

### 前提条件

- Snowflakeでユーザー、データベース、ウェアハウスを作成するために必要な権限
- コンピュータにソフトウェアをインストールして実行できること
- gitの基本的な使用経験
- SQLの中級知識
- SnowflakeでSQLを実行するためのアクセス権

### 学習する内容

- SnowflakeとSQL APIを使用したデータアプリケーションの開発方法
- キーペア認証を使用したSnowflakeでの認証
- JavascriptでJWTトークンを生成する方法

### 必要なもの

- [GitHub](https://github.com/)のアカウント
- [VSCode](https://code.visualstudio.com/download)のインストール、またはお好みのIDE
- [NodeJS](https://nodejs.org/en/download/)のインストール

### 構築するもの

- SQL APIを使用するデータアプリケーション

<!-- ------------------------ -->
## Snowflakeでのデータの設定

Duration:3

ここでは、Tasty Bytesの注文データを使用します。注文データを使用して、以下の機能を持つキッチンカーの運転手用のアプリケーションを構築します。

- キッチンカーの運転手がキュー内の注文を確認できる
- 運転手が、準備が整ったらSnowflakeで注文ステータスを更新することにより注文を完了処理できる
- 運転手が完了済みの注文を確認できる

Snowflakeウェブインターフェイスである[Snowsight](https://docs.snowflake.com/ja/user-guide/ui-snowsight.html#)を使用して、次のことを行います。

- Snowflakeオブジェクト（ウェアハウス、データベース、スキーマ）を作成する
- S3からデータを取り込む
- データを結合してビューを作成する

### オブジェクトの作成、データのロード、データの結合を行う

ワークシートに移動し、右上の「+」をクリックして新しいワークシートを作成し、「SQLワークシート」を選択します。

ワークシートに以下のSQLを貼り付けて実行します。このSQLは、Snowflakeオブジェクト（ウェアハウス、データベース、スキーマ）を作成し、S3から未加工の注文データを取り込み、それをダウンストリームで使用するためにモデリングするためのものです。

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
## アプリケーションのユーザーを作成する

Duration:5

堅牢なセキュリティ対策を確保するには、個人アカウントとは別に、アプリケーション専用のユーザーアカウントを設定することが不可欠です。この新しいアカウントは、Snowflakeのクエリに使用されます。セキュリティに関するベストプラクティスに従い、このアカウントではキーペア認証を採用し、アクセスをSnowflake環境内に制限します。

### ステップ1：認証用の公開キーと非公開キーの生成

以下のコマンドを実行して、非公開キーと公開キーを作成します。これらのキーは、Snowflakeでユーザーを認証するために必要となります。

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_app_key 4096
$ openssl rsa -in snowflake_app_key -pubout -out snowflake_app_key.pub
```

### ステップ2：Snowflakeでユーザーとロールを作成し、この新しいロールにデータアクセスを許可する

以下のSQLステートメントを実行してユーザーアカウントを作成し、アプリケーションに必要なデータへのアクセス権を付与します。

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
## SQL APIによるデータアプリケーション

Duration:10

皆さんが実行するアプリケーションはReact Nativeで記述されます。

### ステップ1：ソースコードを取得する

1. `git clone https://github.com/sf-gh-sjasti/TastyBytesReactNativeAppWithSnowflake-SQL_API.git reactNativeApp`を使用してレポジトリをクローンします。
2. フォルダ`cd reactNativeApp`に移動します。
3. `npm install`を実行して依存関係をインストールします。

### ステップ2：アプリケーションを設定する

1. VS Codeまたはお好みのIDEで`reactNativeApp`フォルダを開きます。
2. `.env`ファイルを開き、非公開キーで`PRIVATE_KEY`の値を更新します。ヘッダー（`-----BEGIN RSA PRIVATE KEY-----`）とフッター（`-----END RSA PRIVATE KEY-----`）を含め、`~/.ssh/snowflake_app_key.pub`から非公開キー全体をコピー＆ペーストします。
3. 米国西部に所在している場合は、`SNOWFLAKE_ACCOUNT_IDENTIFIER`を自分のSnowflakeアカウントに更新してください。（あるいは）米国西部以外の場所に所在している場合は、`SNOWFLAKE_ACCOUNT_IDENTIFIER`を「<SNOWFLAKE ACCOUNT>.<REGION>」に更新してください。Snowflakeからsnowflake_accountの値を取得するには、Snowsightで`SELECT CURRENT_ACCOUNT()`を実行してください。Snowflakeからリージョン値を取得するには、Snowsightで`SELECT CURRENT_REGION()`を実行してください。SNOWFLAKE_ACCOUNT_IDENTIFIERとSNOWFLAKE_ACCOUNTは米国西部では同じとなります。
4. `SNOWFLAKE_ACCOUNT`を自分のSnowflakeアカウントに更新します。
5. `PUBLIC_KEY_FINGERPRINT`を自分のユーザー公開キーのフィンガープリントに更新します。公開キーのフィンガープリントを取得するには、SnowsightでSQL、`DESCRIBE USER data_app_demo `を実行し、RSA_PUBLIC_KEY_FPプロパティ値を取得します。

### ステップ3：ソースコードをレビューする

ここでは、SQL APIを使用し、Snowflakeでキーペア認証を使用して認証を行います。JWTトークンの生成方法については、`Tokens.js`を参照してください。`Orders.js`には、「注文」画面をレンダリングするためのソースコードがあります。このファイルには、SQL API呼び出しの開始方法と必要なヘッダーに関する情報も記載されています。`OrderDetails.js`には、「注文の詳細」画面をレンダリングするためのソースコードがあります。

### ステップ4：アプリケーションをテストする

1. `npx expo start --clear`を実行し、`w`キーを押してWebブラウザでアプリを実行します。
2. この操作により、Webブラウザでアプリが起動します。
3. 起動すると、「キュー内の注文」画面が表示されます。

<img src="assets/OrdersInQueue.png"/>
4. 注文の詳細を表示するには、「View Order（注文を表示）」ボタンをクリックします。

<img src="assets/OrderDetails.png"/>
5. 注文を完了処理するには、「ORDER READY（注文準備完了）」ボタンをクリックします。この操作により、この注文の注文ステータスの値が「完了」に更新され、「キュー内の注文」画面に戻ります。
6. ここで、「注文履歴」タブをクリックすると、完了した注文を確認できます。

<img src="assets/OrderHistory.png"/>
<!-- ------------------------ -->
## クリーンアップ

Duration:1

Snowsightワークシートに移動し、右上の「+」をクリックして新しいワークシートを作成し、「SQLワークシート」を選択します。次のSQLをワークシートに貼り付けて実行し、クイックスタートで作成したSnowflakeオブジェクトを削除します。

```sql
USE ROLE accountadmin;
DROP DATABASE frostbyte_tasty_bytes_app;
DROP WAREHOUSE tasty_app_wh;

USE ROLE securityadmin;
DROP USER data_app_demo;
DROP ROLE tasty_bytes_data_app_demo;
```

<!-- ------------------------ -->
## まとめ

Duration:1

### まとめ

**お疲れ様でした。**Tasty Bytes - SQL APIによるReact Nativeデータアプリケーションの開発クイックスタートを無事完了しました。

これにより、次のことを学習しました。

- SnowflakeとSQL APIを使用したデータアプリケーションの開発
- キーペア認証を使用したSnowflakeでの認証
- JavascriptでのJWTトークンの生成

### 次のステップ

引き続きSnowflakeデータクラウドについて学習するには、以下のリンクから利用可能なTasty Bytes - クイックスタートをご覧ください。

- ### [Powered by Tasty Bytes - クイックスタート目次](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction_ja/index.html)