id: getting_started_with_snowpark_kr
summary: 이 가이드는 Snowpark를 사용하여 단순한 예시 설정을 위한 기본 지침을 제공합니다.
categories: Getting-Started
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: 스노우플레이크 시작하기, 데이터 과학, 데이터 엔지니어링, Twitter, kr

# Snowpark 시작하기

<!-- ------------------------ -->
## 개요

Duration: 1

[Snowpark API](https://docs.snowflake.com/ko/developer-guide/snowpark/index.html)를 사용하여 SQL 문 대신 오브젝트(예: [DataFrame](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrame.html))를 사용하는 코드를 작성하여 데이터를 쿼리하고 조작할 수 있습니다. Snowpark는 복잡한 데이터 파이프라인을 쉽게 구축할 수 있도록 설계되었습니다. 이를 통해 데이터를 이동하지 않고도 Snowflake와 직접 상호 작용할 수 있습니다. Snowpark API를 사용할 때 라이브러리는 Snowflake에서 여러분의 코드를 업로드하고 실행합니다. 따라서 처리를 위해 별도의 시스템으로 데이터를 이동할 필요가 없습니다.

현재 Snowpark는 AWS에서 공식적으로 제공하고 있으며 Azure와 GCP에서는 미리 보기 기능입니다.

### 구축할 것

- 스테이지에서 데이터를 처리하기 위해 Snowpark 라이브러리를 사용하는 Scala 애플리케이션

### 학습할 내용

- 스테이지에서 데이터를 로드하는 DataFrame 생성 방법
- Scala 코드를 위한 사용자 정의 함수 생성 방법
- Scala 함수에서 저장 프로시저 생성 방법

### 사전 필요 조건 및 지식

- Scala에 대한 이해
- Amazon Web Services(AWS) 또는 Microsoft Azure에서 호스트하는 [Snowflake](https://www.snowflake.com/) 계정.
- [git](https://git-scm.com/downloads)
- [SBT](https://www.scala-sbt.org/)

또한 Scala 2.12(특히나 버전 2.12.9 또는 그 이후 2.12.x 버전)를 대상으로 SBT 프로젝트를 지원하는 개발 도구나 환경을 사용할 수 있습니다. Snowpark는 아직 2.12 이후의 Scala 버전(예: 2.13)을 지원하지 않습니다.

Snowpark는 Java 11에서 실행되도록 컴파일된 코드를 지원합니다.

<!-- ------------------------ -->
## 리포지토리 다운로드

Duration: 5

Snowflake GitHub 리포지토리에서 데모를 찾을 수 있습니다. Git을 설치한 다음 여러분의 터미널을 사용하여 리포지토리를 복제할 수 있습니다.

### 리포지토리 복제

1. 터미널 창을 열고 다음 명령을 실행하여 리포지토리를 복제하고자 하는 디렉터리를 변경한 다음 리포지토리를 복제합니다.
   
   ```console
   cd {directory_where_you_want_the_repository}
   git clone https://github.com/Snowflake-Labs/sfguide-snowpark-demo
   ```

2. 복제한 리포지토리의 디렉터리를 변경합니다.
   
   ```console
   cd sfguide-snowpark-demo
   ```

리포지토리의 데모 디렉터리에는 다음 파일이 포함되어 있습니다.

- `build.sbt`: 이 데모 프로젝트를 위한 SBT 빌드 파일입니다.

- `snowflake_connection.properties`: Snowflake에 연결하기 위해 이 데모의 예에서는 이 파일의 설정을 읽습니다. 이 파일을 편집하고 Snowflake 데이터베이스와 연결하기 위해 사용하는 설정을 지정하게 됩니다.

- `src/main/scala/HelloWorld.scala`: Snowpark 라이브러리를 사용하는 단순한 예시입니다. Snowflake와 연결되며 `SHOW TABLES` 명령을 실행하고 나열된 첫 3개의 테이블을 출력합니다. 이 예시를 실행하여 Snowflake에 연결할 수 있는지 확인합니다.

- `src/main/scala/UDFDemoSetup.scala`: 데모를 위해 UDF(사용자 정의 함수)에 필요한 데이터와 라이브러리를 설정합니다. UDF는 이름이 지정된 내부 스테이지에 업로드되어야 하는 데이터 파일과 JAR 파일에 의존합니다. 데이터와 JAR 파일을 다운로드하고 추출한 후 이 예시를 실행하여 스테이지를 생성하고 파일을 업로드합니다.

- `src/main/scala/UDFDemo.scala`: UDF를 생성하고 호출하는 단순한 코드 예시입니다.

<!-- ------------------------ -->
## Snowflake와의 연결을 위한 설정 구성

Duration: 5

데모 디렉터리에는 예시 코드가 Snowflake와 연결하기 위해 [세션 생성](https://docs.snowflake.com/ko/developer-guide/snowpark/creating-session.html)에 사용하는 `snowflake_connection.properties` 파일이 포함되어 있습니다. 코드가 여러분의 Snowflake 계정과 연결될 수 있도록 이러한 속성을 편집해야 합니다.

### 연결 설정 구성

이 파일을 편집하고 Snowflake와 연결하기 위해 사용하는 값으로 `&lt;placeholder&gt;` 값을 대체합니다. 예:

```console
URL = https://myaccount.snowflakecomputing.com
USER = myusername
PRIVATE_KEY_FILE = /home/username/rsa_key.p8
PRIVATE_KEY_FILE_PWD = my_passphrase_for_my_encrypted_private_key_file
ROLE = my_role
WAREHOUSE = my_warehouse
DB = my_db
SCHEMA = my_schema
```

- [여러분의 계정 식별자를 포함하는 URL](https://docs.snowflake.com/ko/user-guide/organizations-connect.html)을 사용합니다. URL 형식에 대한 자세한 정보는 [계정 식별자](https://docs.snowflake.com/ko/user-guide/admin-account-identifier.html)를 확인하십시오.
- 선택하는 `ROLE`에는 스테이지를 생성하고 지정된 데이터베이스 및 스키마에서 테이블을 작성할 수 있는 권한이 있어야 합니다.
- 다른 속성의 경우 [JDBC 드라이버가 지원하는 연결 매개 변수](https://docs.snowflake.com/ko/user-guide/jdbc-parameters.html)를 사용하십시오.

<!-- ------------------------ -->
## Snowflake 연결

Duration: 5

이 단계에서는 여러분이 Snowflake를 데모 코드 및 연결 속성과 연결할 수 있음을 확인하겠습니다.

### Snowflake와 연결할 수 있음을 확인

[SBT 명령줄 도구](https://www.scala-sbt.org/1.x/docs/Running.html)를 사용하여 다음 명령을 실행해 Snowflake와 연결할 수 있음을 확인하기 위해 `HelloWorld.scala` 예시를 구축하고 실행합니다.

```console
sbt "runMain HelloWorld"
```

### 코드 검토회

HelloWorld 애플리케이션이 성공적으로 실행되면 다음과 같은 애플리케이션의 코드와 출력의 검토회를 확인하십시오.

- 세션을 설정하기 위해 애플리케이션 코드는 `snowflake_connection.properties`에 지정된 설정으로 [Session](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/Session.html) 오브젝트를 생성합니다.
  
  ```scala
  val session = Session.builder.configFile("snowflake_connection.properties").create
  ```

- 그런 다음 애플리케이션 코드는 [DataFrame을 생성](https://docs.snowflake.com/ko/developer-guide/snowpark/working-with-dataframes.html)하여 `SHOW TABLES` 명령 실행의 결과를 저장합니다.
  
  ```scala
  val df = session.sql("show tables")
  ```
  
  이는 SQL 문을 실행하지 않습니다. 출력에는 Snowpark 라이브러리가 SQL 문을 실행했음을 나타내는 어떠한 `INFO` 메시지도 포함되지 않습니다.
  
  ```console
  === Creating a DataFrame to execute a SQL statement ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
  ```

- Snowpark에서 [DataFrame](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrame.html)은 느슨하게 평가됩니다. 이는 여러분이 작업을 수행하는 메서드를 호출할 때까지 문이 실행되지 않음을 의미합니다. 이러한 메서드 중 하나는 DataFrame에서 첫 10개의 행을 출력하는 `show`입니다.
  
  ```scala
  df.show()
  ```
  
  출력에서 확인할 수 있듯이 `show`는 SQL 문을 실행합니다. 결과는 DataFrame에 반환되며 DataFrame에 있는 첫 10개의 행이 출력됩니다.
  
  ```console
  === Execute the SQL statement and print the first 10 rows ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25558-0504-b2b8-0000-438301da121e] show tables
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  |"created_on"             |"name"             |"database_name"     |"schema_name"  |"kind"  |"comment"  |"cluster_by"  |"rows"  |"bytes"  |"owner"       |"retention_time"  |"automatic_clustering"  |"change_tracking"  |"is_external"  |
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  |2022-02-15 11:19:20.294  |DEMO_HAPPY_TWEETS  |SNOWPARK_DEMO_DATA  |PUBLIC         |TABLE   |           |              |22      |2560     |ACCOUNTADMIN  |1                 |OFF                     |OFF                |N              |
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ```

이제 Snowflake와 연결할 수 있음을 확인했으니 UDF 작업을 생성하기 위해 데이터와 라이브러리를 가져와야 합니다.

<!-- ------------------------ -->
## 데모를 위한 데이터 파일 및 라이브러리 다운로드

Duration: 10

이 단계에서는 앞으로 생성할 사용자 정의 함수를 실행하기 위해 필요한 샘플 데이터 파일과 라이브러리를 다운로드하겠습니다. 이 데모는 [CoreNLP 프로젝트](https://stanfordnlp.github.io/CoreNLP/)에서 가져온 [sentiment140](https://www.kaggle.com/kazanova/sentiment140) 데이터 세트와 라이브러리를 사용합니다.

### 종속성 JAR 및 샘플 데이터 파일 다운로드

1. [sentiment140](https://www.kaggle.com/kazanova/sentiment140) 페이지로 이동하고 **Download**를 클릭하여 데이터 세트가 포함된 ZIP 아카이브를 다운로드합니다.

2. 다운로드한 `archive.zip` 파일에서 `training.1600000.processed.noemoticon.csv` 압축을 풉니다.

3. [CoreNLP 라이브러리 버전 3.6.0을 다운로드하십시오](https://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip).

4. 다운로드한 `stanford-corenlp-full-2015-12-09.zip` 파일에서 라이브러리 압축을 풉니다.

5. `sfguide-snowpark-demo` 디렉터리에서 데이터와 JAR 파일을 위한 임시 디렉터리(예: `mkdir files_to_upload`)를 생성합니다.

6. `archive.zip`에서 추출한 다음 파일을 `sfguide-snowpark-demo/files_to_upload/` 디렉터리에 복사합니다.
   
   - `training.1600000.processed.noemoticon.csv`

7. `stanford-corenlp-full-2015-12-09.zip`에서 추출한 다음 파일을 `sfguide-snowpark-demo/files_to_upload/` 디렉터리에 복사합니다.
   
   - `stanford-corenlp-3.6.0.jar`
   - `stanford-corenlp-3.6.0-models.jar`
   - `slf4j-api.jar`
   - `ejml-0.23.jar`

`sfguide-snowpark-demo/files_to_upload/`에서 이제 다음 파일이 나타나야 합니다.

```console
$ pwd
<path>/sfguide-snowpark-demo

$ ls files_to_upload
ejml-0.23.jar					stanford-corenlp-3.6.0.jar
slf4j-api.jar					training.1600000.processed.noemoticon.csv
stanford-corenlp-3.6.0-models.jar
```

다음으로 `UDFDemoSetup.scala` 예시를 실행하여 이러한 파일을 위한 스테이지를 생성하고 스테이지에 파일을 업로드합니다.

<!-- ------------------------ -->
## 내부 스테이지에 데이터 파일 및 라이브러리 업로드

Duration: 20

이 섹션에서는 `UDFDemoSetup.scala` 예시를 실행하여 데이터 파일과 라이브러리를 저장하기 위한 [내부 스테이지](https://docs.snowflake.com/ko/user-guide/data-load-local-file-system-create-stage.html)를 생성한 다음 이러한 파일을 스테이지에 업로드하겠습니다.

데모의 사용자 정의 함수는 Snowflake에서 실행되기에 이러한 라이브러리를 위한 JAR 파일을 Snowflake에 제공하기 위해 내부 스테이지에 업로드해야 합니다. 또한 데모가 데이터에 액세스할 스테이지에 데이터 세트를 업로드해야 합니다.

### 종속성 JAR 및 샘플 데이터 파일 업로드

다음 명령을 실행하여 코드를 실행합니다.

```console
sbt "runMain UDFDemoSetup"
```

### 코드 검토회

UDFDemoSetup 애플리케이션이 성공적으로 실행된다면 다음을 읽어 수행하는 작업을 이해합니다.

세션을 생성한 다음 애플리케이션 코드는 `uploadDemoFiles`를 두 번 호출합니다. 한 번은 샘플 데이터 CSV 파일을 업로드하기 위해 호출하며 다른 한 번은 생성할 UDF의 종속성이 될 JAR 파일을 업로드하기 위해 호출합니다. 이 메서드는 Snowpark 라이브러리를 사용하여 업로드된 파일을 위한 스테이지를 생성합니다.

- `uploadDemoFiles` 메서드는 파일이 업로드되어야 하는 스테이지의 이름과 더불어 업로드할 파일 이름과 일치하는 파일 패턴을 사용합니다.
  
  ```scala
  def uploadDemoFiles(stageName: String, filePattern: String): Unit = {
  ```
  
  아래에서는 `uploadDemoFiles` 내부에서 무슨 일이 벌어지는지를 설명합니다.

- 코드는 SQL 문을 실행하여 스테이지를 생성합니다. `collect` 메서드는 DataFrame에서 작업을 수행하여 SQL 문을 실행합니다.
  
  ```scala
  session.sql(s"create or replace stage $stageName").collect()
  ```
  
  예시의 이러한 부분에서는 메서드가 데이터 파일을 위해 스테이지를 생성할 때 다음 출력이 나타나야 합니다.
  
  ```console
  === Creating the stage @snowpark_demo_data ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter QUERY_TAG from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b1f7-0000-438301d9f31e] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:27)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b2bc-0000-438301da22ba] create or replace stage snowpark_demo_data
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b1f7-0000-438301d9f322] alter session unset query_tag
  ```
  
  추후에 JAR 파일을 위한 스테이지를 생성하기 위해 이 메서드가 다시 호출되었을 때 다음 출력이 나타나야 합니다.
  
  ```console
  === Creating the stage @snowpark_demo_udf_dependency_jars ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b1f7-0000-438301d9f326] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:27)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2b8-0000-438301da122e] create or replace stage snowpark_demo_udf_dependency_jars
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b1f7-0000-438301d9f32a] alter session unset query_tag
  ```

- 다음으로 예시는 [FileOperation](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/FileOperation.html) 오브젝트를 사용하여 스테이지에 파일을 업로드합니다. `Session.file` 메서드를 통해 이 오브젝트의 인스턴스에 액세스합니다. 파일을 업로드(사실상 `PUT` 명령 실행)하기 위해 FileOperation 오브젝트의 `put` 메서드를 호출합니다. `put` 메서드는 [PutResult](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/PutResult.html) 오브젝트의 배열을 반환합니다. 각각에는 특정 파일의 결과가 포함되어 있습니다.
  
  ```scala
  val res = session.file.put(s"$uploadDirUrl/$filePattern", stageName)
  res.foreach(r => Console.println(s"  ${r.sourceFileName}: ${r.status}"))
  ```
  
  메서드가 데이터 파일을 업로드할 때 다음이 나타나야 합니다.
  
  ```console
  === Uploading files matching training.1600000.processed.noemoticon.csv to @snowpark_demo_data ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b2b8-0000-438301da1226] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///Users/straut/workfiles/git/sfguide-snowpark-demo/files_to_upload/training.1600000.processed.noemoticon.csv @snowpark_demo_data
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2bc-0000-438301da22be] alter session unset query_tag
    training.1600000.processed.noemoticon.csv: UPLOADED
  ```
  
  메서드가 JAR 파일을 업로드할 때 다음이 나타나야 합니다.
  
  ```console
  === Uploading files matching *.jar to @snowpark_demo_udf_dependency_jars ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2b8-0000-438301da1232] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///Users/straut/workfiles/git/sfguide-snowpark-demo/files_to_upload/*.jar @snowpark_demo_udf_dependency_jars
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a2557d-0504-b2b8-0000-438301da1236] alter session unset query_tag
    slf4j-api.jar: UPLOADED
    stanford-corenlp-3.6.0.jar: UPLOADED
    ejml-0.23.jar: UPLOADED
    stanford-corenlp-3.6.0-models.jar: UPLOADED
  ```

- 그런 다음 예시는 `LS` 명령을 실행하여 새롭게 생성된 스테이지에 파일을 나열하고 출력의 첫 10개의 행을 출력합니다.
  
  ```scala
  session.sql(s"ls @$stageName").show()
  ```
  
  메서드가 CSV 파일을 업로드했을 때 다음이 나타나야 합니다.
  
  ```console
  === Files in @snowpark_demo_data ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2bc-0000-438301da22c2] ls @snowpark_demo_data
  ---------------------------------------------------------------------------------------------------------------------------------------
  |"name"                                              |"size"    |"md5"                                |"last_modified"                |
  ---------------------------------------------------------------------------------------------------------------------------------------
  |snowpark_demo_data/training.1600000.processed.n...  |85088032  |da1aae6fe4879f916e740bd80af19685-17  |Tue, 15 Feb 2022 20:06:28 GMT  |
  ---------------------------------------------------------------------------------------------------------------------------------------
  ```
  
  메서드가 JAR 파일을 업로드했을 때 다음이 나타나야 합니다.
  
  ```console
  === Files in @snowpark_demo_udf_dependency_jars ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a2557d-0504-b2bc-0000-438301da22ca] ls @snowpark_demo_udf_dependency_jars
  ----------------------------------------------------------------------------------------------------------------------------------------
  |"name"                                              |"size"     |"md5"                                |"last_modified"                |
  ----------------------------------------------------------------------------------------------------------------------------------------
  |snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz  |189776     |92c4f90ad7fcb8fecbe0be3951f9b8a3     |Tue, 15 Feb 2022 20:13:38 GMT  |
  |snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz  |22640      |b013b6f5f80f95a285e3169c4f0b85ce     |Tue, 15 Feb 2022 20:13:37 GMT  |
  |snowpark_demo_udf_dependency_jars/stanford-core...  |378223264  |e4b4fdfbec76cc7f8fed01e08eec4dc0-73  |Tue, 15 Feb 2022 20:08:39 GMT  |
  |snowpark_demo_udf_dependency_jars/stanford-core...  |6796432    |2c4a458b9a205395409349b56dc64f8d     |Tue, 15 Feb 2022 20:13:38 GMT  |
  ----------------------------------------------------------------------------------------------------------------------------------------
  ```

다음으로 `UDFDemo.scala` 예시를 실행하여 사용자 정의 함수를 생성합니다.

<!-- ------------------------ -->
## UDF 데모 실행

Duration: 10

이 단계에서는 `UDFDemo.scala` 데모 애플리케이션을 실행하여 UDF(사용자 정의 함수)를 생성하고 호출하겠습니다. Snowpark 라이브러리가 이러한 작업을 어떻게 수행하는지 확인하기 위해 다음 주제를 읽어 예시와 출력을 보다 자세하게 확인하십시오.

### UDF 생성 및 호출

다음 명령을 실행하여 코드를 실행합니다.

```console
sbt "runMain UDFDemo"
```

이 예시는 다음 작업을 수행합니다.

- 데이터를 데모 파일에서 DataFrame으로 로드합니다.
- 문자열을 분석하고 문자열에서 단어의 감정을 결정하는 UDF(사용자 정의 함수)를 생성합니다.
- DataFrame에 있는 열의 각 값을 대상으로 UDF를 호출합니다.
- 다음을 포함한 새로운 DataFrame을 생성합니다.
  - 원본 데이터를 포함한 열
  - UDF의 반환값을 포함한 새로운 열
- 감정이 행복하다고 결정한 UDF가 있는 행만을 포함한 새로운 DataFrame 생성

이러한 작업의 수행 방법을 자세히 알아보려면 다음 주제를 확인하십시오.

<!-- ------------------------ -->
## 스테이지에서 데이터 로드 및 DataFrame 생성

Duration: 5

`collectTweetData` 메서드는 `DataFrame`을 생성하여 [스테이지에 있는 파일에서 CSV 데이터를 읽습니다](https://docs.snowflake.com/ko/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-stages). [DataFrameReader](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameReader.html) 오브젝트로 이러한 작업을 수행합니다.

### 코드 검토회

- 이 메서드는 Session 오브젝트를 수신하여 Snowflake와의 연결에 사용합니다.
  
  ```scala
  def collectTweetData(session: Session): DataFrame = {
  ```

- `session` ***변수***에 있는 `implicits`에서 이름을 가져와 여러분은 DataFrame 메서드로 인수를 전송할 때 열을 나타내는 속기(예: `'columnName` 및 `$"columnName"`)를 사용할 수 있습니다.
  
  ```scala
  import session.implicits._
  ```

- 데모 파일은 CSV 파일이기에 우선 파일의 스키마를 정의해야 합니다. Snowpark에서는 데이터의 각 열 이름과 유형을 식별하는 [StructField](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/StructField.html) `Seq` 오브젝트를 생성하여 이러한 작업을 수행합니다. 이러한 오브젝트는 [com.snowflake.snowpark.types](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/index.html) 패키지의 구성 요소입니다.
  
  ```scala
  val schema = Seq(
    StructField("target", StringType),
    StructField("ids", StringType),
    StructField("date", StringType),
    StructField("flag", StringType),
    StructField("user", StringType),
    StructField("text", StringType),
  )
  ```

- `Session.read` 메서드를 통해 `DataFrameReader` 오브젝트에 액세스합니다. `DataFrameReader` 오브젝트는 로드할 파일의 스키마, 옵션 및 유형을 지정하기 위해 사용하는 메서드를 제공합니다. 스키마 및 옵션 설정을 위해 이러한 메서드는 `DataFrameReader` 오브젝트와 더불어 스키마 및 옵션 세트를 반환합니다. 이를 통해 아래에서 확인할 수 있듯이 이러한 메서드 호출을 묶을 수 있습니다. 파일 유형 지정 메서드(이 경우 `csv` 메서드)는 지정된 파일에서 데이터를 로드하기 위해 설정된 DataFrame을 반환합니다.
  
  ```scala
  val origData = session
    .read
    .schema(StructType(schema))
    .option("compression", "gzip")
    .csv(s"@$dataStageName/$dataFilePattern")
  ```
  
  이 예시에서 `dataStageName` 및 `dataFilePattern`은 `UDFDemoSetup`을 실행했을 때 앞서 해당 스테이지에 업로드했던 스테이지와 파일의 이름을 나타냅니다. DataFrame이 느슨하게 평가됨을 기억하실 수도 있습니다. 이는 여러분이 데이터를 검색하기 위해 메서드를 호출할 때까지 데이터를 로드하지 않음을 의미합니다. 추가 메서드를 호출하여 데이터 검색을 위해 메서드를 호출하기 전에 DataFrame을 변환할 수 있습니다(다음 코드 줄에서처럼).

- 다음으로 예시는 트윗을 포함한 열(`text`라는 열)만 포함된 새로운 DataFrame(`tweetData`)을 반환합니다. DataFrame에는 원본 DataFrame인 `origData`의 첫 100개의 행이 포함되어 있습니다. 이 예시에서 `drop` 및 `limit` 메서드는 각각 이러한 메서드에 의해 변환된 새로운 DataFrame를 반환합니다. 각 메서드는 메서드에 의해 변환된 새로운 DataFrame을 반환하기에 아래와 같이 메서드 호출을 묶을 수 있습니다.
  
  ```scala
  val tweetData = origData.drop('target, 'ids, 'date, 'flag, 'user).limit(100)
  ```

- 이 시점에는 `tweetData` DataFrame에 실제 데이터가 포함되어 있지 않습니다. 데이터를 로드하기 위해 작업(이 경우 `show`)을 수행하는 메서드를 호출해야 합니다.
  
  예시는 `tweetData` DataFrame을 반환합니다.
  
  ```scala
  tweetData.show()
  return tweetData
  ```

### 출력

`collectTweetData`의 경우 다음과 같은 출력이 나타나야 합니다.

```console
=== Setting up the DataFrame for the data in the stage ===

[sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.

=== Retrieving the data and printing the text of the first 10 tweets
[sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da600a]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
[sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da600e]  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100) LIMIT 10
------------------------------------------------------
|"TEXT"                                              |
------------------------------------------------------
|"...
```

<!-- ------------------------ -->
## UDF 정의

Duration: 5

`createUDF` 메서드는 감정을 위해 트윗을 분석하는 UDF의 종속성을 설정한 다음 Snowflake에서 UDF를 생성합니다.

### 코드 검토회

- 메서드는 UDF의 종속성을 지정하기 위해 사용되는 `Session` 오브젝트를 사용합니다.
  
  ```scala
  def createUDF(session: Session): UserDefinedFunction = {
  ```

- UDF는 별도의 JAR 파일로 패키징된 라이브러리에 의존하기에 이러한 JAR 파일로 Snowpark 라이브러리를 인도해야 합니다. `Session.addDependency` 메서드를 호출하여 이러한 작업을 수행합니다. 예시에서는 이러한 JAR 파일을 종속성으로 추가합니다.
  
  ```scala
  session.addDependency(s"@$jarStageName/stanford-corenlp-3.6.0.jar.gz")
  session.addDependency(s"@$jarStageName/stanford-corenlp-3.6.0-models.jar.gz")
  session.addDependency(s"@$jarStageName/slf4j-api.jar.gz")
  session.addDependency(s"@$jarStageName/ejml-0.23.jar.gz")
  ```
  
  이 예시에서 `jarStageName`은 여러분이 `UDFDemoSetup`을 실행했을 때 JAR 파일을 업로드했던 스테이지 이름을 나타냅니다.

- 예시는 `com.snowflake.snowpark.functions` 오브젝트의 `udf` 함수를 호출하여 UDF를 정의합니다. UDF는 `analyze` 메서드로 데이터 열에 있는 각각의 값을 전송합니다.
  
  ```scala
  val sentimentFunc = udf(analyze(_))
  return sentimentFunc
  ```

### 출력

- Snowpark 라이브러리는 Snowpark를 위해 JAR 파일을 추가하고 여러분의 예시를 위해 종속성(앞서 지정했던 종속성과 같이)을 추가합니다.
  
  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Automatically added /Users/straut/workfiles/git/sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to session dependencies.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Adding /Users/straut/workfiles/git/sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to session dependencies
  ```

- 다음으로 Snowpark 라이브러리는 JAR 파일을 위한 임시 스테이지를 생성합니다...
  
  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b311-0000-438301da500e] create temporary stage if not exists "SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter QUERY_TAG from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6012] alter session set query_tag = 'com.snowflake.snowpark.functions$.udf
  UDFDemo$.createUDF(UDFDemo.scala:108)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6016] ls @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da601a]  SELECT "name" FROM ( SELECT  *  FROM  TABLE ( RESULT_SCAN('01a255c9-0504-b313-0000-438301da6016')))
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b311-0000-438301da501a] alter session unset query_tag
  ```
  
  ...그리고 Snowpark와 애플리케이션 코드를 위해 JAR 파일을 스테이지에 업로드합니다. Snowpark는 또한 여러분의 UDF를 컴파일하고 JAR 파일을 스테이지에 업로드합니다.
  
  ```console
  [snowpark-2]  INFO (Logging.scala:22) - Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-9]  INFO (Logging.scala:22) - Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-11]  INFO (Logging.scala:22) - Compiling UDF code
  [snowpark-11]  INFO (Logging.scala:22) - Finished Compiling UDF code in 765 ms
  [snowpark-11]  INFO (Logging.scala:22) - Uploading UDF jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-11]  INFO (Logging.scala:22) - Finished Uploading UDF jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 1413 ms
  [snowpark-2]  INFO (Logging.scala:22) - Finished Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 2236 ms
  [snowpark-9]  INFO (Logging.scala:22) - Finished Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 8482 ms
  ```

- 마지막으로 라이브러리는 여러분의 데이터베이스에서 UDF를 정의합니다.
  
  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6022] CREATE TEMPORARY FUNCTION "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422(arg1 STRING) RETURNS INT LANGUAGE JAVA IMPORTS = ('@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0-models.jar.gz','@snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/f25d6649aab5cfb7a9429be961d73687/snowparkdemo_2.12-0.1.jar','@snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/85061e2a4c65715009267162d183eec1/snowpark-0.6.0.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/SNOWPARK_DEMO_DATAPUBLICtempUDF_1136829422_126127561/udfJar_591813027.jar') HANDLER='SnowUDF.compute'
  ```

<!-- ------------------------ -->
## 트윗 처리를 위해 UDF 사용

Duration: 5

`processHappyTweets` 메서드는 UDF를 사용하여 어떤 트윗이 행복한지 발견하기 위해 트윗 텍스트를 분석합니다.

### 코드 검토회

- 메서드는 다음을 수신합니다.
  
  - Snowflake와의 연결을 위한 `Session`.
  - 여러분이 생성했던 UDF.
  - 트윗을 나타내는 DataFrame.
  
  ```scala
  def processHappyTweets(session: Session, sentimentFunc: UserDefinedFunction, tweetData: DataFrame): Unit = {
  ```

- `session` 변수의 `implicits`에서 이름을 가져옵니다.
  
  ```scala
  import session.implicits._
  ```

- 다음으로 예시는 `sentiment`라는 열을 추가하여 `tweetData` DataFrame을 변환하는 새로운 DataFrame인 `analyzed`를 생성합니다. `sentiment` 열에는 `text` 열에서 해당하는 값을 포함한 UDF(`sentimentFunc`) 호출의 결과가 포함되어 있습니다.
  
  ```scala
  val analyzed = tweetData.withColumn("sentiment", sentimentFunc('text))
  ```

- 예시는 `sentiment`에 `3`이라는 값이 있는 행만 포함되도록 `analyzed` DataFrame을 변환하는 또 다른 DataFrame인 `happyTweets`를 생성합니다.
  
  ```scala
  val happyTweets = analyzed.filter('sentiment === 3)
  ```

- 다음으로 예시는 `show` 메서드를 호출하여 SQL 문(UDF 포함)을 실행하고 결과를 DataFrame으로 검색한 다음 첫 10개의 행을 출력합니다.
  
  ```scala
  happyTweets.show()
  ```
  
  `show` 메서드가 실행되면 다음과 같은 출력이 나타나야 합니다.
  
  ```console
  === Retrieving the data and printing the first 10 tweets ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da5026]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da502a]  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT", "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422("TEXT") AS "SENTIMENT" FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100)) WHERE ("SENTIMENT" = 3 :: int)) LIMIT 10
  --------------------------------------------------------------------
  |"TEXT"                                              |"SENTIMENT"  |
  --------------------------------------------------------------------
  |"...
  ```

- 마지막으로 예시는 [DataFrame에 있는 데이터를](https://docs.snowflake.com/ko/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-save-table) `demo_happy_tweets`라는 테이블에 저장합니다. 이를 위해 예시는 `DataFrame.write` 메서드 호출에 의해 검색되는 [DataFrameWriter](https://docs.snowflake.com/ko/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameWriter.html) 오브젝트를 사용합니다. 예시는 `DataFrameWriter` 오브젝트의 `mode` 메서드로 `SaveMode.Overwrite`를 전송하여 테이블에 있는 모든 기존 데이터를 덮어씁니다.
  
  ```scala
  happyTweets.write.mode(Overwrite).saveAsTable("demo_happy_tweets")
  ```
  
  `saveAsTable` 메서드가 실행되면 다음과 같은 출력이 나타나야 합니다.
  
  ```console
  === Saving the data to the table demo_happy_tweets ===
  
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da502e]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b313-0000-438301da602a]  CREATE  OR  REPLACE  TABLE demo_happy_tweets AS  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT", "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422("TEXT") AS "SENTIMENT" FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100)) WHERE ("SENTIMENT" = 3 :: int))
  ```

이 부분이 끝났습니다! 지금까지 Scala 코드를 사용자 정의 함수로 업로드한 다음 UDF를 실행하여 행복한 트윗을 위해 트윗 데이터를 분석했습니다.

마지막 단계에서는 이미 보유하고 있는 코드를 가져와 Snowflake에서 이를 저장 프로시저로 변환하겠습니다.

<!-- ------------------------ -->
## Scala 코드에서 저장 프로시저 생성

Duration: 5

이 단계에서는 방금 실행했던 코드를 가져와 이로부터 저장 프로시저를 생성하겠습니다. 이를 위해 Scala 코드를 Snowflake 워크시트로 복사하고 코드를 SQL 문에서 래핑한 다음 이를 실행하여 저장 프로시저를 생성하겠습니다.

다음 단계에서는 [새로운 웹 인터페이스](https://docs.snowflake.com/ko/user-guide/ui-web.html)를 사용합니다.

관련 설명서를 위해 [Snowpark에서 저장 프로시저 작성(Scala)](https://docs.snowflake.com/ko/sql-reference/stored-procedures-scala.html)을 확인하십시오.

### 저장 프로시저 생성 및 실행

1. 새로운 웹 인터페이스에서 새로운 워크시트를 생성하고 이름을 `discoverHappyTweets`라고 지정합니다.

2. 워크시트 편집기에서 세션 컨텍스트가 앞서 편집했던 snowflake_connection.properties 파일에 지정했던 설정과 일치하는지 확인합니다. 예:
   
   - 왼쪽 상단에 있는 드롭다운에서 지정했던 역할을 선택합니다.
   - 오른쪽 상단에 있는 세션 컨텍스트 드롭다운에서 지정했던 역할과 웨어하우스 값을 선택합니다.
   - 데이터베이스 드롭다운에서 지정했던 데이터베이스와 스키마를 선택합니다.

3. `discoverHappyTweets` 워크시트에 다음을 붙여넣습니다.
   
   ```sql
   create or replace procedure discoverHappyTweets()
   returns string
   language scala
   runtime_version=2.12
   packages=('com.snowflake:snowpark:latest')
   imports=('@snowpark_demo_udf_dependency_jars/ejml-0.23.jar','@snowpark_demo_udf_dependency_jars/slf4j-api.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0-models.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0.jar')
   handler = 'UDFDemo.discoverHappyTweets'
   target_path = '@snowpark_demo_udf_dependency_jars/discoverHappyTweets.jar'
   as
   $$
   
   /*Paste the UDFDemo object Scala code, including imports. You can optionally
   omit the main function.*/
   
   $$;
   ```
   
   이 코드는 `discoverHappyTweets`라는 저장 프로시저를 생성합니다. 설명서에는 더 많이 있지만 다음을 확인해야 합니다.
   
   - `packages` 매개 변수는 사용할 Snowpark 버전을 지정합니다.
   - `imports` 매개 변수는 코드의 종속성으로 필요한 JAR 파일을 지정합니다. 이는 앞서 Snowflake에 업로드했던 JAR 파일의 목록입니다.
   - `handler` 매개 변수는 저장 프로시저를 실행할 때 Snowflake가 호출해야 하는 함수를 지정합니다.
   - `target_path` 매개 변수는 이 코드를 실행할 때 생성할 JAR의 이름과 위치를 지정합니다. Snowflake는 코드를 컴파일하고 컴파일된 클래스를 패키징합니다.

4. `$$` 구분 기호 간 섹션에 `UDFDemo`에서 가져온 Scala 코드를 붙여넣습니다. `import` 문이 포함되어야 합니다. 필요하지 않으니 `main` 함수를 포함하지 마십시오. 특히나 Snowflake는 여러분이 오브젝트를 생성했던 곳에 Session 오브젝트를 삽입합니다. Snowflake는 대신 `handler` 매개 변수로 지정했던 메서드를 호출합니다.

5. 워크시트에서 코드를 실행합니다. Snowflake는 `CREATE PROCEDURE`의 본문에 있는 코드를 컴파일하고 이를 JAR 파일로 패키징합니다.

6. 새로운 워크시트를 생성하고 이름을 `call discoverHappyTweets`라고 지정합니다.

7. 새로운 워크시트에 다음 코드를 붙여넣습니다.
   
   ```sql
   call discoverHappyTweets();
   select * from demo_happy_tweets;
   ```

8. 워크시트에서 2개의 줄을 모두 선택한 다음 워크시트에서 코드를 실행합니다. Snowflake가 저장 프로시저를 호출함에 따라 워크시트 아래에 메시지가 나타나야 합니다. 프로시저 호출이 완료된 후 이는 행복한 트윗 목록인 쿼리 결과로 대체됩니다. 저장 프로시저 호출은 단순히 메서드 또는 저장 프로시저와 관련된 함수를 실행합니다. 클래스패스에서 JAR 파일을 통해 실행됩니다.

이처럼 쉽게 저장 프로시저를 생성할 수 있습니다. 보너스 포인트를 위해 새로운 저장 프로시저를 밤마다 수행하는 작업으로 호출할 수 있습니다.

```sql
create or replace task process_tweets_nightly
warehouse = 'small'
schedule = '1440 minute'
as
call discoverHappyTweets();
```

<!-- ------------------------ -->
## 종료 및 다음 단계

Duration: 1

축하드립니다! Snowpark를 사용하여 트윗을 대상으로 감정 분석을 수행했습니다. 이 가이드를 위해 트윗의 샘플 데이터 세트를 사용했습니다. 새로운 트윗이 작성됨에 따라 이를 자동으로 수집하고자 한다면 [Snowflake로 Twitter 데이터 자동 수집](/guide/auto_ingest_twitter_data/) 가이드를 따르십시오.

### 다룬 내용

- **데이터 로딩** - Snowpark를 사용하여 Snowflake로 Twitter 데이터 로드(Scala)
- **데이터** - CSV 파일에서 DataFrame 생성 및 필요하지 않은 열 삭제
- **감정 분석** - Scala를 사용하여 트윗 DataFrame을 대상으로 감정 분석 수행
- **Snowpark UDF** - Scala를 사용하여 Snowflake 테이블에 DataFrame 작성
- **Snowpark 저장 프로시저** - Snowflake를 사용하여 Scala에서 저장 프로시저 생성

### 관련 리소스

- [Snowpark Docs](https://docs.snowflake.com/ko/LIMITEDACCESS/snowpark.html)
- [GitHub의 Source 코드 예시](https://github.com/Snowflake-Labs/sfguide-snowpark-demo)