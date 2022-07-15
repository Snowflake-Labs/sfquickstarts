summary: Python 시작하기
id: getting_started_with_python_kr
categories: Getting Started
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: 스노우플레이크 시작하기, SQL, 데이터 엔지니어링, SnowSQL, Python, kr

# Python 시작하기

<!-- ------------------------ -->
## 개요

Duration: 1

다양한 언어로 Snowflake와 연결할 수 있습니다. 선택한 언어가 Python이라면 Snowflake와의 연결을 여기에서 시작하는 것이 좋습니다. Python Connector 실행을 시작한 다음 이를 사용하여 수행할 수 있는 기본 작업에 대해 알아보겠습니다. Python Connector는 꽤나 강력하며 Pandas DataFrames와의 통합도 지원합니다.

### 사전 필요 조건 및 지식

- Python에 대한 이해

### 학습할 내용

- Python Connector 설정 방법
- 설치 테스트 방법
- Snowflake 연결 방법
- 세션 매개 변수 설정 방법
- 웨어하우스 생성 방법
- 데이터베이스 생성 방법
- 스키마 생성 방법
- 테이블 생성 방법
- 데이터 삽입 방법
- 데이터 쿼리 방법

### 필요한 것

- [Snowflake](https://www.snowflake.com/) 계정
- 텍스트 편집기

### 구축할 것

- Snowflake Python Connector 사용 예

<!-- ------------------------ -->
## Python Connector 설정

Duration: 5

이 가이드에서는 Python 3을 사용하겠습니다. 여러분의 시스템에 있는 Python의 버전을 확인하겠습니다. 터미널을 열고 다음 명령을 입력하여 확인합니다.

```
python --version
```

출력이 3.5 이상이라면 시작할 준비가 되었습니다! 아니라면 최신 버전의 Python을 설치해야 합니다. 최신 릴리스는 Python 웹 사이트에서 찾을 수 있습니다.

최신 Python 버전을 다운로드했다면 Python용 Snowflake Connector를 설치할 수 있습니다. Python 패키지 설치 프로그램인 `pip`를 사용하고 다음 명령을 실행하여 설치하겠습니다.

```
pip install --upgrade snowflake-connector-python
```

Linux 배포판을 사용하고 있다면 여러분의 배포 리포지토리에 몇몇 패키지를 설치해야 합니다. 특히나 다음과 동등한 수준이 필요합니다.

* libm-devel
* openssl-devel

Python과 Snowflake Connector가 모두 설치되었다면 시작할 준비가 되었습니다! 설치되었는지 확인해 보겠습니다.

<!-- ------------------------ -->
## 설치 테스트

Duration: 3

Snowflake 커넥터 *사용*을 자세히 알아보기 전에 올바르게 설치되었는지 확인하겠습니다. 다음 스크립트를 통해 확인할 수 있습니다.

```
#!/usr/bin/env python
import snowflake.connector

# Gets the version
ctx = snowflake.connector.connect(
    user='<your_user_name>',
    password='<your_password>',
    account='<your_account_name>'
    )
cs = ctx.cursor()
try:
    cs.execute("SELECT current_version()")
    one_row = cs.fetchone()
    print(one_row[0])
finally:
    cs.close()
ctx.close()
```

텍스트 편집기를 열고 해당 스크립트를 복사한 다음 `validate.py`로 저장합니다. 여러분의 사용자 이름, 암호 및 계정을 해당하는 필드에 입력해야 합니다.

파일이 저장된 위치에서 터미널을 열고 다음 명령을 실행합니다.

```
python validate.py
```

모든 것이 성공적이라면 설치된 Snowflake 버전이 나타나야 합니다. 그렇지 않으면 여러분의 상황에 해당하는 오류가 나타납니다.

<!-- ------------------------ -->
## Snowflake 연결

Duration: 5

Python용 Snowflake 커넥터를 사용할 시간입니다. Python 환경을 엽니다. 우선적으로 해야 하는 일은 Snowflake 커넥터 모듈을 가져오는 것입니다. 어떠한 Snowflake 관련 명령을 사용하기 전에 이를 가져와야 합니다.

```
import snowflake.connector
```

환경 변수와 같은 외부 소스에서 여러분의 로그인 정보를 읽는 것을 고려해 보십시오. 이는 여러분의 스크립트에 추가적인 보안을 제공하며 장기적으로 시간을 절약합니다. 이 예에서는 `os.getenv`를 사용하여 `PASSWORD.` 변수를 위한 `SNOWSQL_PWD` 환경 변수를 가져오겠습니다.

```
PASSWORD = os.getenv('SNOWSQL_PWD')
```

다음과 같이 Python Connector 내에서 이러한 변수를 사용하게 됩니다.

```
conn = snowflake.connector.connect(
    user=USER,
    password=PASSWORD,
    account=ACCOUNT
    )
```

좋습니다! 이제 세부 사항을 자세히 알아보겠습니다.

<!-- ------------------------ -->
## 세션 매개 변수 설정

Duration: 1

세션 매개 변수를 설정하여 여러분의 세션을 조정하고 여러분이 원하는 대로 설정할 수 있습니다. 2가지 방식으로 설정할 수 있습니다. 우선 처음 연결할 때 다음과 같이 설정할 수 있습니다.

```
conn = snowflake.connector.connect(
    user='XXXX',
    password='XXXX',
    account='XXXX',
    session_parameters={
        'QUERY_TAG': 'EndOfMonthFinancials',
    }
)
```

아니면 연결한 다음 `ALTER SESSION SET` SQL 문을 실행하여 설정할 수 있습니다.

```
conn.cursor().execute("ALTER SESSION SET QUERY_TAG = 'EndOfMonthFinancials'")
```

강력한 보안 방법을 사용하기 위해 Snowflake 기능의 이점을 누리고 있으셨을 수 있습니다. 그렇다면 추가적인 단계를 밟아 Snowflake Python Connector를 구성하는 것이 좋습니다.

* [Single Sign-on (SSO)](https://docs.snowflake.com/ko/user-guide/admin-security-fed-auth-use.html#label-sso-with-command-line-clients)
* [키 쌍 인증](https://docs.snowflake.com/ko/user-guide/python-connector-example.html#using-key-pair-authentication)
  - [키 회전](https://docs.snowflake.com/ko/user-guide/python-connector-example.html#key-rotation)
* [OAuth](https://docs.snowflake.com/ko/user-guide/oauth-intro.html#label-oauth-intro-clients-drivers-conns)

이 시점에는 Snowflake 내에서 오브젝트 조작을 시작할 수 있습니다.

<!-- ------------------------ -->
## 웨어하우스 생성

Duration: 2

Snowflake와 상호 작용하기 위한 SQL 명령에 익숙하다면 Python Connector 내 명령에도 익숙하실 것입니다. 명령이 어떻게 구성되어 있는지 분석해 보겠습니다.

`conn`은 여러분을 여러분의 Snowflake 계정과 연결하는 오브젝트임을 기억하십시오. 이를 사용하여 다음 형식을 가진 SQL 명령을 실행할 수 있습니다.

```
conn.cursor().execute("YOUR SQL COMMAND")
```

우선 [가상 웨어하우스](https://docs.snowflake.com/ko/user-guide/warehouses-overview.html)를 생성하겠습니다. 가상 웨어하우스에는 Snowflake를 통해 쿼리와 DML 작업을 수행하기 위해 필요한 서버가 포함되어 있습니다. `CREATE WAREHOUSE` SQL 명령을 통합하여 하나의 가상 웨어하우스를 생성할 수 있습니다.

```
conn.cursor().execute("CREATE WAREHOUSE IF NOT EXISTS tiny_warehouse_mg")
```

`CREATE WAREHOUSE` 명령은 예상대로 웨어하우스를 생성하지만 암시적으로 해당 웨어하우스를 여러분의 세션을 위한 활성 웨어하우스로 설정하기도 합니다. 이미 웨어하우스를 생성했다면 `USE WAREHOUSE` 명령을 사용하여 명시적으로 이를 활성 웨어하우스로 설정할 수 있습니다.

```
conn.cursor().execute("USE WAREHOUSE tiny_warehouse_mg")
```

이제 웨어하우스가 있으니 데이터베이스를 다뤄 보겠습니다.

<!-- ------------------------ -->
## 데이터베이스 생성

Duration: 2

다음 단계는 데이터베이스 생성입니다. 데이터베이스는 여러분의 데이터베이스 오브젝트가 포함되어 있는 스키마를 포함합니다. 웨어하우스를 생성했을 때와 동일한 방식으로 데이터베이스를 생성할 수 있습니다. 다만 이번에는 `CREATE DATABASE` 명령을 사용하겠습니다.

```
conn.cursor().execute("CREATE DATABASE IF NOT EXISTS testdb")
```

데이터베이스 생성 또한 해당 데이터베이스를 현재 세션의 활성 데이터베이스로 설정합니다. 이미 생성된 데이터베이스를 세션을 위한 활성 데이터베이스로 설정해야 한다면 `USE DATABASE` 명령을 사용합니다.

```
conn.cursor().execute("USE DATABASE testdb")
```

그런 다음 스키마를 생성해야 합니다.

<!-- ------------------------ -->
## 스키마 생성

Duration: 2

스키마는 여러분의 데이터베이스 오브젝트의 그룹화입니다. 스키마에는 여러분의 테이블, 테이블에 있는 데이터 및 뷰가 포함되어 있습니다. 스키마는 데이터베이스 내에 있습니다. `CREATE SCHEMA` 명령으로 스키마를 생성할 수 있습니다.

```
conn.cursor().execute("CREATE SCHEMA IF NOT EXISTS testschema")
```

`CREATE SCHEMA`는 또한 여러분의 세션을 위해 이를 활성 스키마로 설정하기에 명시적으로 `USE SCHEMA` 또한 호출할 필요가 없습니다. 이미 생성된 스키마를 사용하고 싶을 때만 사용하십시오.

```
conn.cursor().execute("USE SCHEMA testschema")
```

기본값으로 스키마는 현재 데이터베이스에서 사용됩니다. 또 다른 데이터베이스를 지정하여 이러한 다른 데이터베이스에서 사용할 수 있습니다.

```
conn.cursor().execute("USE SCHEMA otherdb.testschema")
```

스키마를 사용하고 있으니 테이블에 대해 알아볼 시간입니다.

<!-- ------------------------ -->
## 테이블 생성

Duration: 2

웨어하우스, 데이터베이스 및 스키마를 생성했으니 데이터에 있는 데이터 조작에 필요한 모든 것이 준비되었습니다. 우선 테이블을 생성해야 합니다. `CREATE TABLE` 명령을 통해 생성합니다.

```
conn.cursor().execute(
    "CREATE OR REPLACE TABLE "
    "test_table(col1 integer, col2 string)")
```

`conn.cursor().execute` 내에서 이 예는 2개의 열을 가진 `test_table`라는 테이블을 생성합니다. `col1`이라는 열에는 정수가 포함되며 `col2`이라는 열에는 문자열이 포함됩니다.

<!-- ------------------------ -->
## 데이터 삽입

Duration: 2

`test_table` 테이블을 생성했으니 여기에 데이터를 추가할 수 있습니다. `INSERT` 명령으로 추가할 수 있습니다.

```
conn.cursor().execute(
    "INSERT INTO test_table(col1, col2) "
    "VALUES(123, 'test string1'),(456, 'test string2')")
```

이 명령은 행별로 데이터를 `test_table`에 삽입합니다. 첫 열과 첫 행에서 찾은 값은 '123' 등과 같습니다.

그러나 행별로 데이터를 수동으로 삽입하고 싶지 않다면 대신 데이터를 로드할 수 있습니다. 이는 `PUT`과 `COPY INTO` 명령의 조합으로 가능합니다.

```
conn.cursor().execute("PUT file:///tmp/data/file* @%test_table")
conn.cursor().execute("COPY INTO test_table")
```

여기에서 `PUT` 명령은 파일을 스테이징하고, `COPY INTO` 명령은 해당 데이터를 파일에서 복사하여 지정된 테이블로 복사합니다. 또한 `COPY INTO` 명령을 사용하여 데이터를 외부 위치에서 복사할 수 있습니다.

<!-- ------------------------ -->
## 데이터 쿼리

Duration: 2

당연히 언젠가 여러분의 데이터를 쿼리하고 싶을 것입니다. Python Connector 내에서 이를 쉽게 진행할 수 있습니다. `print` 명령으로 쉽게 테이블에서 가져온 값을 확인할 수 있습니다.

```
col1, col2 = conn.cursor().execute("SELECT col1, col2 FROM test_table").fetchone()
print('{0}, {1}'.format(col1, col2))
```

이 코드 조각은 `SELECT col1, col2 FROM test_table` SQL 명령을 사용하여 특정 열을 선택한 다음 각각의 행 또는 첫 행에 있는 첫 값을 출력합니다.

비슷한 방식으로 전체 열을 출력할 수 있습니다.

```
for (col1, col2) in conn.cursor().execute("SELECT col1, col2 FROM test_table"):
	print('{0}, {1}'.format(col1, col2))
```

여러분의 리소스를 효율적으로 사용하려면 쿼리를 수행한 후 명시적으로 Snowflake와의 연결을 종료하는 것이 좋습니다.

```
connection.close()
```

보십시오! 이제 Snowflake 내에서 데이터를 조작하기 위해 필요한 모든 단계를 구현했습니다.

<!-- ------------------------ -->
## 다음 단계: Python으로 고급 조작

Duration: 1

이 단계에서는 Python Connector 사용의 기본 사항을 파악하셨을 것입니다. 알아차리셨을 수도 있지만 이는 이미 확립된 Snowflake SQL 명령에 상당히 의존합니다. 당연히 Connector로 수행할 수 있는 작업은 더 많습니다. 여러분의 사용 사례에 따라 관심을 가지실 만한 잠재적인 다음 단계는 다음과 같습니다.

* [데이터 바인딩](https://docs.snowflake.com/ko/user-guide/python-connector-example.html#binding-data)
* [Pandas Dataframes 사용](https://docs.snowflake.com/ko/user-guide/python-connector-pandas.html)
* [Snowflake SQLAlchemy 도구 키트](https://docs.snowflake.com/ko/user-guide/sqlalchemy.html)

이는 Snowflake로 수행할 수 있는 작업의 극히 일부입니다. 더 자세한 내용은 [Snowflake 설명서](https://docs.snowflake.com/ko/)를 확인하십시오.