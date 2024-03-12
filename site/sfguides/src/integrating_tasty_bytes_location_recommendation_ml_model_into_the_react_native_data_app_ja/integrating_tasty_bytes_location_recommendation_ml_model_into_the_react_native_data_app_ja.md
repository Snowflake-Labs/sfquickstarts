author: Swathi Jasti
id: integrating_tasty_bytes_location_recommendation_ml_model_into_the_react_native_data_app_ja
summary: Tasty Bytesのロケーション推奨MLモデルのReact Nativeデータアプリケーションへの統合
categories: Tasty-Bytes, Getting-Started, app-development, Data-Science-&-Ml
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, API, Data Science, Snowpark, Machine Learning, ja

# Tasty Bytesのロケーション推奨MLモデルのReact Nativeデータアプリケーションへの統合

<!-- ------------------------ -->
## 概要

Duration: 2 <img src="assets/tasty_bytes_header.png"/>

Snowflakeは、MLモデルをストアドプロシージャ、ユーザー定義関数（UDF）、ユーザー定義テーブル関数（UDTF）としてデプロイできるようにする便利な機能を通じて、機械学習モデルのデータアプリケーションへの統合を簡素化しました。さらに、Snowflakeは、デプロイされたMLモデルへのクエリを容易にするRESTful APIであるSQL APIを提供し、アプリケーションとMLモデルのシームレスな統合を可能にします。

このチュートリアルでは、架空のキッチンカー会社であるTasty Bytesとキッチンカーの運転手が、データアプリケーション内でMLモデルにより直接提供されるロケーション推奨を確認できるアプリケーションを作成します。このロケーション推奨MLモデルは、PythonユーザーがSnowflakeプラットフォームを簡単に活用できるように、Snowparkを使用してSnowflake内に構築されています。このモデルは、Snowflakeマーケットプレイスの過去の販売データとSafegraphの気象データを使用して、モデルにより多くの情報を提供します。このチュートリアルでは、MLモデルをキッチンカーの運転手用のアプリにデプロイし、統合するプロセスについて説明します。

### 前提条件

- Snowflakeでユーザー、データベース、ウェアハウスを作成するために必要な権限
- コンピュータにソフトウェアをインストールして実行できること
- gitの基本的な使用経験
- SQLの中級知識
- SnowflakeでSQLを実行するためのアクセス権

### 学習する内容

- **Snowflakeマーケット**プレイスからサードパーティデータにアクセスする方法
- ストアドプロシージャを使用して**Snowflakeでモデルをトレーニングする**方法
- モデル推論のためにユーザー定義関数に**Snowflakeでモデルを展開する**方法
- データアプリに**MLモデルを統合する**方法

### 必要なもの

- [GitHub](https://github.com/)のアカウント
- [VSCode](https://code.visualstudio.com/download)のインストール、またはお好みのIDE
- [NodeJS](https://nodejs.org/en/download/)のインストール

### 構築するもの

- Snowparkを使ったMLモデルを基盤とするデータアプリケーション

<!-- ------------------------ -->
## Snowflakeでのデータの設定

Duration: 3

Snowflakeウェブインターフェイスである[Snowsight](https://docs.snowflake.com/ja/user-guide/ui-snowsight.html#)を使用して、次のことを行います。

- SnowflakeマーケットプレイスからSafeGraphロケーションデータにアクセスする
- Snowflakeオブジェクト（ウェアハウス、データベース、スキーマ）を作成する
- S3からシフト売上データを取り込む
- シフト売上とSafeGraphロケーションデータを結合する

Tasty Bytesは世界中の都市でキッチンカーを運行しており、各キッチンカーは1日に2つの異なる販売ロケーションを選択できます。これらのロケーションはSafeGraphの関心ポイントにマッピングされています。SafeGraphマーケットプレイスデータの緯度と経度をシフト売上データに結合し、モデルトレーニングで特徴量として使用します。

### ステップ1 - SnowflakeマーケットプレイスからSafeGraph POIデータを取得する

- Snowflakeアカウントにログインします。

- 以下の手順とビデオに従って、SnowflakeアカウントからSafeGraphマーケットプレイスのリスティングにアクセスします。
  
  - ホームアイコンをクリック
  - マーケットプレイスをクリック
  - frostbyteを検索
  - 「SafeGraph: frostbyte」をクリック
  - 「Get（取得）」をクリック
  - データベースの名称をFROSTBYTE_WEATHERSOURCE（すべて大文字）に変更
  - 追加ロールへの付与 -> \[PUBLIC（公開）]

<img src = "assets/acquire_safegraph.gif">
> SafeGraphは、世界中のあらゆる場所に関するデータを提供するグローバルな地理空間データ会社です。Esri、Tripadvisor、Mapbox、Syscoなどの顧客は、SafeGraphのデータを使用して、自社の顧客をより正確に把握し、新しい製品を生み出し、より的確な経営判断を行っています。

### ステップ2 - オブジェクトの作成、データのロード、データの結合を行う

ワークシートに移動し、右上の「+」をクリックして新しいワークシートを作成し、「SQLワークシート」を選択します。

ワークシートに以下のSQLを貼り付けて実行します。このSQLは、Snowflakeオブジェクト（ウェアハウス、データベース、スキーマ）を作成し、S3から未加工の注文データを取り込み、それをダウンストリームで使用するためにモデリングするためのものです。

```sql
-- use our accountadmin role
USE ROLE accountadmin;

-- create a development database for data science work
CREATE OR REPLACE DATABASE frostbyte_tasty_bytes_ml_app;

-- create raw, harmonized, and analytics schemas
-- raw zone for data ingestion
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_ml_app.raw;
-- harmonized zone for data processing
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_ml_app.harmonized;
-- analytics zone for development
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes_ml_app.analytics;

-- create csv file format
CREATE OR REPLACE FILE FORMAT frostbyte_tasty_bytes_ml_app.raw.csv_ff 
type = 'csv';

-- create an external stage pointing to S3
CREATE OR REPLACE STAGE frostbyte_tasty_bytes_ml_app.raw.s3load
COMMENT = 'Quickstarts S3 Stage Connection'
url = 's3://sfquickstarts/frostbyte_tastybytes/'
file_format = frostbyte_tasty_bytes_ml_app.raw.csv_ff;

-- define shift sales table
CREATE OR REPLACE TABLE frostbyte_tasty_bytes_ml_app.raw.shift_sales(
	location_id NUMBER(19,0),
	city VARCHAR(16777216),
	date DATE,
	shift_sales FLOAT,
	shift VARCHAR(2),
	month NUMBER(2,0),
	day_of_week NUMBER(2,0),
	city_population NUMBER(38,0)
);

-- create and use a compute warehouse
CREATE OR REPLACE WAREHOUSE tasty_ml_app_wh AUTO_SUSPEND = 60;
USE WAREHOUSE tasty_ml_app_wh;

-- ingest from S3 into the shift sales table
COPY INTO frostbyte_tasty_bytes_ml_app.raw.shift_sales
FROM @frostbyte_tasty_bytes_ml_app.raw.s3load/analytics/shift_sales/;

-- join in SafeGraph data
CREATE OR REPLACE TABLE frostbyte_tasty_bytes_ml_app.harmonized.shift_sales
  AS
SELECT
    a.location_id,
    a.city,
    a.date,
    a.shift_sales,
    a.shift,
    a.month,
    a.day_of_week,
    a.city_population,
    b.latitude,
    b.longitude,
    b.location_name,
    b.street_address
FROM frostbyte_tasty_bytes_ml_app.raw.shift_sales a
JOIN frostbyte_safegraph.public.frostbyte_tb_safegraph_s b
ON a.location_id = b.location_id;

-- promote the harmonized table to the analytics layer for data science development
CREATE OR REPLACE VIEW frostbyte_tasty_bytes_ml_app.analytics.shift_sales_v
  AS
SELECT * FROM frostbyte_tasty_bytes_ml_app.harmonized.shift_sales;

-- view shift sales data
SELECT * FROM frostbyte_tasty_bytes_ml_app.analytics.shift_sales_v;
```

<!-- ------------------------ -->
## アプリケーションのユーザーを作成する

Duration: 5

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

-- create our tasty_bytes_data_ml_app_demo role
CREATE ROLE tasty_bytes_data_ml_app_demo;

-- use our accountadmin role
USE ROLE accountadmin;

-- grant privileges to our tasty_bytes_data_app_demo role
GRANT USAGE ON WAREHOUSE tasty_ml_app_wh TO ROLE tasty_bytes_data_ml_app_demo;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes_ml_app TO ROLE tasty_bytes_data_ml_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_ml_app.analytics TO ROLE tasty_bytes_data_ml_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_ml_app.harmonized TO ROLE tasty_bytes_data_ml_app_demo;
GRANT USAGE ON SCHEMA frostbyte_tasty_bytes_ml_app.raw TO ROLE tasty_bytes_data_ml_app_demo;
GRANT SELECT ON ALL VIEWS IN SCHEMA frostbyte_tasty_bytes_ml_app.analytics TO ROLE tasty_bytes_data_ml_app_demo;
GRANT SELECT ON ALL VIEWS IN SCHEMA frostbyte_tasty_bytes_ml_app.harmonized TO ROLE tasty_bytes_data_ml_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_ml_app.analytics TO ROLE tasty_bytes_data_ml_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_ml_app.harmonized TO ROLE tasty_bytes_data_ml_app_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA frostbyte_tasty_bytes_ml_app.raw TO ROLE tasty_bytes_data_ml_app_demo;

-- use our useradmin role
USE ROLE useradmin;

-- Open the ~/.ssh/snowflake_app_key.pub file from Step 1 and copy the contents starting just after the PUBLIC KEY header, 
-- and stopping just before the PUBLIC KEY footer for INSERT_RSA_PUBLIC_KEY_HERE.
CREATE USER data_ml_app_demo
RSA_PUBLIC_KEY='<INSERT_RSA_PUBLIC_KEY_HERE>' 
DEFAULT_ROLE=tasty_bytes_data_ml_app_demo 
DEFAULT_WAREHOUSE=tasty_ml_app_wh 
MUST_CHANGE_PASSWORD=FALSE;

-- use our securityadmin role
USE ROLE securityadmin;
GRANT ROLE tasty_bytes_data_ml_app_demo TO USER data_ml_app_demo;
```

<!-- ------------------------ -->
## SnowflakeにおけるMLモデルのトレーニングと展開

Duration: 10

### 概要

Tasty Bytesは、5年間で前年比25%の売上成長を達成することを目指しています。この目標をサポートし、キッチンカーフリート全体で1日の収益を最大化するため、データサイエンスチームは、所定のシフトで最も高い売上が期待できるロケーションにキッチンカーを誘導するMLモデルを構築する必要があります。

ワークシートに移動し、右上の「+」をクリックして新しいワークシートを作成し、「SQLワークシート」を選択します。

ワークシートに以下のSQLを貼り付けて実行し、ロケーション推奨モデルをトレーニングしてデプロイします。

```sql
USE ROLE accountadmin;
USE DATABASE frostbyte_tasty_bytes_ml_app;
USE SCHEMA analytics;
USE WAREHOUSE tasty_ml_app_wh;

CREATE STAGE IF NOT EXISTS app_stage;

-- Create stored proc for shift table
CREATE OR REPLACE PROCEDURE build_shift_feature_table()
    RETURNS string
    LANGUAGE python
    RUNTIME_VERSION = '3.8'
    PACKAGES = ('snowflake-snowpark-python')
    HANDLER = 'create_table'
AS
$$
def create_table(session):
    import snowflake.snowpark.functions as F
    import snowflake.snowpark.types as T
    from snowflake.snowpark import Window
    
    # Create DataFrame
    snowpark_df = session.table("frostbyte_tasty_bytes_ml_app.analytics.shift_sales_v")
    
    # Create rolling average
    window_by_location_all_days = (
    Window.partition_by("location_id", "shift")
    .order_by("date")
    .rows_between(Window.UNBOUNDED_PRECEDING, Window.CURRENT_ROW - 1))
    
    snowpark_df = snowpark_df.with_column(
    "avg_location_shift_sales", 
    F.avg("shift_sales").over(window_by_location_all_days))
    
    # Impute
    snowpark_df = snowpark_df.fillna(value=0, subset=["avg_location_shift_sales"])
    
    # Encode
    snowpark_df = snowpark_df.with_column("shift", F.iff(F.col("shift") == "AM", 1, 0))
    
    # Get date
    date_tomorrow = snowpark_df.filter(F.col("shift_sales").is_null()).select(F.min("date")).collect()[0][0]
    
    # Filter
    feature_df = snowpark_df.filter(F.col("date") == date_tomorrow).drop(F.col("shift_sales"))
    
    # Get Location Detail
    location_df = session.table("frostbyte_tasty_bytes_ml_app.analytics.shift_sales_v").select("location_id", "location_name", "street_address")
    
    # Join
    feature_df = feature_df.join(location_df,
                    feature_df.location_id == location_df.location_id,
                    "left") \
                    .drop(location_df.location_id) \
                    .drop(location_df.location_name) \
                    .drop(location_df.street_address) \
                    .rename(feature_df.location_id, "location_id") \
                    .rename(feature_df.location_name, "location_name") \
                    .rename(feature_df.street_address, "street_address")
    
    # Save table
    feature_df.write.mode("overwrite").save_as_table("frostbyte_tasty_bytes_ml_app.analytics.shift_features")
    
    return "SUCCESS"
$$;

-- Call sproc to create feature table
Call build_shift_feature_table();

-- Set permissions
GRANT ALL PRIVILEGES ON TABLE frostbyte_tasty_bytes_ml_app.analytics.shift_features to tasty_bytes_data_ml_app_demo;

-- Create training stored procedure
CREATE OR REPLACE PROCEDURE SPROC_TRAIN_LINREG()
    RETURNS STRING
    LANGUAGE PYTHON
    RUNTIME_VERSION = '3.8'
    PACKAGES = ('snowflake-snowpark-python','scikit-learn','joblib')
    HANDLER = 'train_model'
AS
$$
def train_model(session):
    import snowflake.snowpark.functions as F
    import snowflake.snowpark.types as T
    from snowflake.snowpark import Window
    
    # Create DataFrame
    snowpark_df = session.table("frostbyte_tasty_bytes_ml_app.analytics.shift_sales_v")
    
    # Create rolling average
    window_by_location_all_days = (
    Window.partition_by("location_id", "shift")
    .order_by("date")
    .rows_between(Window.UNBOUNDED_PRECEDING, Window.CURRENT_ROW - 1))
    
    snowpark_df = snowpark_df.with_column(
    "avg_location_shift_sales", 
    F.avg("shift_sales").over(window_by_location_all_days))
    
    # Impute
    snowpark_df = snowpark_df.fillna(value=0, subset=["avg_location_shift_sales"])
    
    # Encode
    snowpark_df = snowpark_df.with_column("shift", F.iff(F.col("shift") == "AM", 1, 0))
    
    # Get date
    date_tomorrow = snowpark_df.filter(F.col("shift_sales").is_null()).select(F.min("date")).collect()[0][0]
    
    # Filter to historical
    historical_snowpark_df = snowpark_df.filter(F.col("shift_sales").is_not_null())
    
    # Drop
    historical_snowpark_df = historical_snowpark_df.drop("location_id", "city", "date")
    
    # Split
    train_snowpark_df, test_snowpark_df = historical_snowpark_df.randomSplit([0.8, 0.2])
    
    # Import packages
    from sklearn.linear_model import LinearRegression
    from joblib import dump
    
    feature_cols = ["MONTH", "DAY_OF_WEEK", "LATITUDE", "LONGITUDE", "CITY_POPULATION", "AVG_LOCATION_SHIFT_SALES", "SHIFT"]
    target_col = "SHIFT_SALES"

    # Get training data
    df = train_snowpark_df.to_pandas()

    # Set inputs X and outputs y
    X = df[feature_cols]
    y = df[target_col]

    # Train model
    model = LinearRegression().fit(X, y)

    # Save model
    model_name = "linreg_location_sales_model.sav"
    dump(model, "/tmp/" + model_name)
    session.file.put(
        "/tmp/" + model_name,
        "@APP_STAGE",
        auto_compress=False,
        overwrite=True
    )

    return "SUCCESS"
$$;

-- Train model
Call sproc_train_linreg();

-- Deploy the model as a UDF
CREATE OR REPLACE 
  FUNCTION udf_predict_location_sales_prod(arg1 FLOAT,arg2 FLOAT,
                                                  arg3 FLOAT,arg4 FLOAT,
                                                  arg5 FLOAT,arg6 FLOAT,
                                                  arg7 FLOAT)
    RETURNS FLOAT
    LANGUAGE PYTHON 
    RUNTIME_VERSION=3.8
    IMPORTS=('@APP_STAGE/linreg_location_sales_model.sav')
    PACKAGES=('scikit-learn','joblib','cloudpickle==2.0.0','pandas', 'cachetools')
    HANDLER='predict'
    as
$$
import pandas
import cachetools
from _snowflake import vectorized

@cachetools.cached(cache={})
def load_model(filename):
    import joblib
    import sys
    import os
    
    import_dir = sys._xoptions.get("snowflake_import_directory")
    if import_dir:
        with open(os.path.join(import_dir, filename), 'rb') as file:
            m = joblib.load(file)
            return m

@vectorized(input=pandas.DataFrame)
def predict(X: pandas.DataFrame) -> pandas.Series:
    # Load the model
    model = load_model("linreg_location_sales_model.sav")

    # Get predictions
    predictions = model.predict(X)

    # Return rounded predictions
    return predictions.round(2)
$$;

-- Set permissions
GRANT ALL PRIVILEGES ON FUNCTION udf_predict_location_sales_prod(FLOAT,FLOAT,FLOAT, FLOAT,FLOAT,FLOAT,FLOAT) to tasty_bytes_data_ml_app_demo;
```

<!-- ------------------------ -->
## SQL APIを使ったMLモデルからのデータ取得とデータアプリケーションへの統合

Duration: 10

皆さんが実行するアプリケーションはReact Nativeで記述されます。

### ステップ1：ソースコードを取得する

1. `https://github.com/sf-gh-sjasti/IntegrationTastyBytesMLModelInDataApp.git reactNativeMLApp`を使用してレポジトリをクローンします。
2. フォルダ`cd reactNativeMLApp`に移動します。
3. `npm install`を実行して依存関係をインストールします。

### ステップ2：アプリケーションを設定する

1. VS Codeまたは起この意のIDEで`reactNativeMLApp`フォルダを開きます。
2. `.env`ファイルを開き、非公開キーで`PRIVATE_KEY`の値を更新します。ヘッダー（`-----BEGIN RSA PRIVATE KEY-----`）とフッター（`-----END RSA PRIVATE KEY-----`）を含め、`~/.ssh/snowflake_app_key.pub`から非公開キー全体をコピー＆ペーストします。
3. 米国西部に所在している場合は、`SNOWFLAKE_ACCOUNT_IDENTIFIER`を自分のSnowflakeアカウントに更新してください。（あるいは）米国西部以外の場所に所在している場合は、`SNOWFLAKE_ACCOUNT_IDENTIFIER`を「<SNOWFLAKE ACCOUNT>.<REGION>」に更新してください。Snowflakeからsnowflake_accountの値を取得するには、Snowsightで`SELECT CURRENT_ACCOUNT()`を実行してください。Snowflakeからリージョン値を取得するには、Snowsightで`SELECT CURRENT_REGION()`を実行してください。SNOWFLAKE_ACCOUNT_IDENTIFIERとSNOWFLAKE_ACCOUNTは米国西部では同じとなります。
4. `SNOWFLAKE_ACCOUNT`を自分のSnowflakeアカウントに更新します。
5. `PUBLIC_KEY_FINGERPRINT`を自分のユーザー公開キーのフィンガープリントに更新します。公開キーのフィンガープリントを取得するには、SnowsightでSQL、`DESCRIBE USER data_app_demo `を実行し、RSA_PUBLIC_KEY_FPプロパティ値を取得します。

### ステップ3：ソースコードをレビューする

ここでは、SQL APIを使用し、Snowflakeでキーペア認証を使用して認証を行います。JWTトークンの生成方法については、`Tokens.js`を参照してください。`Locations.js`には、「ロケーション」画面をレンダリングするためのソースコードがあります。このファイルには、SQL APIを使用してUDFをクエリする方法と必要なヘッダーに関する情報も記載されています。

### ステップ4：アプリケーションをテストする

1. `npx expo start --clear`を実行し、`w`キーを押してWebブラウザでアプリを実行します。
2. この操作により、Webブラウザでアプリが起動します。
3. 起動すると、「キュー内の注文」画面が表示されます。

<img src="assets/Locations.png"/>
<!-- ------------------------ -->
## クリーンアップ

Duration: 1

Snowsightワークシートに移動し、右上の「+」をクリックして新しいワークシートを作成し、「SQLワークシート」を選択します。次のSQLをワークシートに貼り付けて実行し、クイックスタートで作成したSnowflakeオブジェクトを削除します。

```sql
USE ROLE accountadmin;
DROP DATABASE frostbyte_tasty_bytes_ml_app;
DROP WAREHOUSE tasty_ml_app_wh;

USE ROLE securityadmin;
DROP USER data_ml_app_demo;
DROP ROLE tasty_bytes_data_ml_app_demo;
```

<!-- ------------------------ -->
## まとめ

Duration: 1

### まとめ

**お疲れ様でした。**Tasty Bytesのロケーション推奨MLモデルのReact Nativeデータアプリケーションへの統合クイックスタートが無事完了しました。

これにより、次のことを学習しました。

- **Snowflakeマーケットプレイス**からサードパーティデータを取得する
- ストアドプロシージャを使用してSnowflakeでMLモデルのトレーニングする
- モデル推論を実行するためにMLモデルをSnowflakeにUDFとしてデプロイする
- MLモデルをデータアプリに統合する

### 次のステップ

ロケーション推奨MLモデルの詳細については、[Tasty Bytes - データサイエンスのためのSnowpark入門](https://quickstarts.snowflake.com/guide/tasty_bytes_snowpark_101_for_data_science)クイックスタートを参照してください。

引き続きSnowflakeデータクラウドについて学習するには、以下のリンクから利用可能なTasty Bytes - クイックスタートをご覧ください。

- ### [Powered by Tasty Bytes - クイックスタート目次](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction_ja)