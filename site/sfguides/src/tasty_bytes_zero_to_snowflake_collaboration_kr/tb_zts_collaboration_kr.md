author: Jacob Kranzler
id: tasty_bytes_zero_to_snowflake_collaboration_kr
summary: Tasty Bytes - Zero to Snowflake - Collaboration Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, kr

# Tasty Bytes - 제로부터 Snowflake까지 - 협업

<!-- ------------------------ -->
## Snowflake 마켓플레이스를 통한 서드 파티 데이터에 대한 직접 액세스

Duration: 1 <img src = "assets/collaboration_header.png">

### 개요

협업을 집중적으로 다루는 Tasty Bytes - 제로부터 Snowflake까지 Quickstart에 오신 것을 환영합니다! 이 Quickstart에서는 Snowflake 마켓플레이스를 통해 자사 데이터를 날씨 데이터로 보강하는 방법을 집중적으로 다루겠습니다. Snowflake 마켓플레이스는 그 어떠한 ETL, 데이터 파이프라인 또는 통합도 설정하지 않고 서드 파티 데이터와 앱을 찾고, 체험하고, 구매하는 장소입니다.

### 사전 필요 조건 및 지식

- 시작하기 전에 평가판 계정 설정과 이 Quickstart를 완료하기 위해 필요한 Tasty Bytes 기초를 배포하는 것을 안내하는 [**Tasty Bytes 소개 Quickstart**](/guide/tasty_bytes_introduction_kr/index.html)를 완료하십시오.

### 알아볼 내용

- Snowflake 마켓플레이스에 액세스하기
- 계정에서 라이브 Weather Source 데이터 획득하기
- 뷰 생성하기
- SQL 함수 생성하기
- 시각적 인사이트를 탐색하기 위해 Snowsight 그래프 활용하기

### 구축할 것

- 자사 매출 및 서드 파티 날씨 데이터 조정
- 원활한 화씨 섭씨 변환 가능성
- 원활한 인치 밀리미터 변환 가능성
- Snowflake 마켓플레이스를 통해 추가 인사이트를 얻는 방법 이해

## 워크시트 생성 및 SQL 복사

Duration: 1

### 개요

이 Quickstart에서는 Snowsight SQL 워크시트를 통해 테마가 Tasty Bytes인 스토리를 따라갈 것입니다. 이 페이지에는 추가 해설, 이미지 및 설명서 링크가 포함되어 있으며 나란히 사용할 수 있는 가이드입니다.

이 섹션은 Snowflake에 로그인하고, 새로운 워크시트를 생성하고, 워크시트의 이름을 바꾸고, SQL을 GitHub에서 복사하고, 이 Quickstart에서 활용할 SQL을 붙여넣는 방법을 안내합니다.

### 1단계 - URL을 통해 Snowflake에 액세스

- 브라우저 창을 열고 Snowflake 계정 URL을 입력합니다.

### 2단계 - Snowflake에 로그인

- Snowflake 계정에 로그인합니다.
  - <img src ="assets/log_into_snowflake.gif" width = "300"/>


### 3단계 - Worksheets로 이동

- 왼쪽 탐색 메뉴에 있는 Worksheets 탭을 클릭합니다.
  - <img src ="assets/worksheet_tab.png" width="250"/>


### 4단계 - 워크시트 생성

- Worksheets 내에서 Snowsight 오른쪽 상단 모서리에 있는 ‘+’ 버튼을 클릭하고 ‘SQL Worksheet’를 선택합니다.
  - <img src = "assets/+_sqlworksheet.png" width ="200">


### 5단계 - 워크시트 이름 바꾸기

- 자동으로 생성된 Timestamp 이름을 클릭하고 ‘Tasty Bytes - Collaboration’을 입력하여 워크시트의 이름을 바꿉니다.
  - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>


### 6단계 - GitHub에서 Quickstart SQL에 액세스

- GitHub에서 호스팅된 Tasty Bytes SQL 파일과 연결된 아래 버튼을 클릭합니다.

<button>[tb_zts_collaboration.sql](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/tasty_bytes/tb_zts_collaboration.sql)</button>

### 7단계 - GitHub에서 설정 SQL 복사

- GitHub 내에서 오른쪽으로 이동하여 ‘Copy raw contents’를 클릭합니다. 이렇게 하면 모든 필수 SQL이 클립보드로 복사됩니다.
  - <img src ="assets/github_copy_raw_contents.png"/>


### 8단계 - 설정 SQL을 GitHub에서 Snowflake 워크시트로 붙여넣기

- Snowsight 및 새롭게 생성한 워크시트로 되돌아가 방금 GitHub에서 복사한 것을 붙여넣습니다(*Mac 바로 가기 키 CMD + V, Windows 바로 가기 키 CTRL + V*).

### 9단계 - 다음 클릭 -->

## 자사 데이터에서 매출이 0인 날짜 조사

Duration: 1

### 개요

Tasty Bytes 금융 분석가는 전년 대비 분석을 실행할 때 여러 도시에서 트럭 매출이 0인 설명할 수 없는 날짜가 존재한다고 알려왔습니다. 금융 분석가가 제시한 하나의 사례는 2022년 2월 독일 함부르크입니다.

### 1단계 - 추세를 위해 판매 시점 데이터 쿼리

초기에 역할과 웨어하우스 콘텍스트를 `tasty_data_engineer` 및 `tasty_de_wh`로 설정하기 위해 이 단계에서 3개의 쿼리를 실행하며 시작하겠습니다. 콘텍스트가 설정되면 분석 `orders_v` 뷰를 쿼리하여 2022년 독일 함부르크의 매출 결과 세트를 제공하겠습니다.

```
USE ROLE tasty_data_engineer;
USE WAREHOUSE tasty_de_wh;

SELECT 
    o.date,
    SUM(o.price) AS daily_sales
FROM frostbyte_tasty_bytes.analytics.orders_v o
WHERE 1=1
    AND o.country = 'Germany'
    AND o.primary_city = 'Hamburg'
    AND DATE(o.order_ts) BETWEEN '2022-02-10' AND '2022-02-28'
GROUP BY o.date
ORDER BY o.date ASC;
```

<img src = "assets/3.1.orders_v.png">
위에서 확인한 내용에 따르면 2월의 몇몇 날짜에 일일 매출 기록이 없다는 점에서 분석가의 의견에 동의할 수 있습니다. 따라서 분석가는 확실히 문제가 있는 부분을 지적했습니다. 다음 섹션에서는 이러한 현상이 발생한 이유를 조금 더 자세히 알아보겠습니다.

### 2단계 - 다음 클릭 -->

## Snowflake 마켓플레이스의 Weather Source 데이터 활용

Duration: 2

### 개요

이전 섹션을 보면 2월 16일부터 2월 21일까지의 독일 함부르크에서 발생한 매출이 누락된 것 같습니다.  자사 데이터 내에서는 이 부분을 조사하기 위해 사용할 수 있는 것이 거의 없습니다. 하지만 더 큰 요인이 여기에 영향을 줬을 것입니다.

[Snowflake 마켓플레이스](https://www.snowflake.com/ko/data-cloud/marketplace/)를 활용하여 바로 탐색할 수 있는 하나의 아이디어는 기상 이변과 Weather Source에서 제공한 무료 공개 목록입니다.

### 1단계 - Weather Source LLC: frostbyte Snowflake 마켓플레이스 목록 획득

Snowflake 마켓플레이스는 혁신적인 비즈니스 솔루션을 지원하기 위해 필요한 데이터와 애플리케이션을 찾고, 체험하고, 구매하기 가장 좋은 장소입니다. 이 단계에서는 [Weather Source LLC: frostbyte](https://app.snowflake.com/marketplace/listing/GZSOZ1LLEL/weather-source-llc-weather-source-llc-frostbyte) 목록에 액세스하여 함부르크 매출 하락에 대한 추가 분석을 수행하는 것을 돕겠습니다.

아래 단계와 동영상에 따라 Snowflake 계정에서 이 목록을 획득합니다.

- 클릭 -> 홈
- 클릭 -> Marketplace
- 검색 -> frostbyte
- 클릭 -> Weather Source LLC: frostbyte
- 클릭 -> Get
- 데이터베이스 이름 바꾸기 -> FROSTBYTE_WEATHERSOURCE(전부 대문자)
- 추가 역할에 부여 -> PUBLIC

<img src = "assets/4.1.acquire_weather_source.gif">
> aside positive Weather Source는 선도적인 전 세계 날씨 및 기후 데이터 공급자입니다. 이 회사의 OnPoint Product Suite는 비즈니스가 여러 산업에 걸쳐 다양한 사용 사례에 대한 의미 있고 실행 가능한 인사이트를 빠르게 생성하는 데 필요한 날씨 및 기후 데이터를 제공합니다.

### 2단계 - 자사 및 서드 파티 데이터 조정

공유 `frostbyte_weathersource` 데이터베이스를 사용하는 상태로 이 단계의 쿼리를 실행하여 `harmonized.daily_weather_v` 뷰를 생성하십시오. 그러면 2개의 Weather Source 테이블과 Tasty Bytes 푸드 트럭이 운영되는 국가와 도시에 대한 국가 테이블을 결합할 수 있습니다.

```
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.harmonized.daily_weather_v
    AS
SELECT 
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM frostbyte_weathersource.onpoint_id.history_day hd
JOIN frostbyte_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN frostbyte_tasty_bytes.raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;
```

<img src = "assets/4.2.daily_weather_v.png">
위 뷰 정의에서 확인할 수 있듯이 `onpoint_id` 스키마 내 2개의 `frostbyte_weathersource` 테이블을 결합한 다음 `frostbyte_tasty_bytes` 데이터베이스 및 `raw_pos` 스키마의 `country` 테이블과 이를 조정하고 있습니다.

이러한 작업은 일반적으로 조정 계층(실버 영역이라고도 함)에서 찾아볼 수 있습니다.

### 3단계 - 일일 기온 시각화

조정 스키마에서 `daily_weather_v` 뷰를 사용하는 상태로 다음 쿼리를 실행하여 2022년 2월 함부르크의 일평균 기온을 살펴보겠습니다.

이 과정에서 [AVG](https://docs.snowflake.com/ko/sql-reference/functions/avg), [YEAR](https://docs.snowflake.com/ko/sql-reference/functions/year) 및 [MONTH](https://docs.snowflake.com/ko/sql-reference/functions/year) 함수를 활용하겠습니다.

```
SELECT 
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS avg_temperature_air_2m_f
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v dw
WHERE 1=1
    AND dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = '2022'
    AND MONTH(date_valid_std) = '2'
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<img src = "assets/4.3.results.png">

추세를 추가적으로 조사하기 위해 Snowsight 그래프 생성을 활용하여 시간의 흐름에 따른 평균 기온의 선 그래프를 생성하겠습니다.

<img src = "assets/4.3.chart.png">

위에서 확인한 내용에 따르면 트럭에서 매출이 없는 날짜가 발생한 명백한 이유를 아직 찾지 못했습니다. 다음 단계에서 이유를 설명할 수도 있는 다른 요인을 찾아보겠습니다.

### 4단계 - 바람 데이터 가져오기

이전 단계에서 확인했듯이 일평균 기온은 함부르크에서 매출이 0인 날짜가 발생한 이유가 아닌 것 같습니다. 다행히 Weather Source는 심층적으로 알아볼 수 있는 다른 날씨 지표를 제공합니다.

이제 바람 지표를 가져오기 위해 조정 뷰를 활용할 다음 쿼리를 실행하십시오. 이 쿼리에서는 [MAX](https://docs.snowflake.com/ko/sql-reference/functions/min) 함수가 사용됩니다.

```
SELECT 
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    MAX(dw.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v dw
WHERE 1=1
    AND dw.country_desc IN ('Germany')
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = '2022'
    AND MONTH(date_valid_std) = '2'
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<img src = "assets/4.4.result.png">

여기서도 빠른 Snowsight 그래프를 통해 이러한 데이터의 추세를 더 잘 나타낼 수 있습니다. 결과에서 그래프로 이동하기 위해 아래 스크린샷에 있는 화살표를 따르십시오.

<img src = "assets/4.4.chart.png">

**찾았습니다!** 매출이 0인 날짜에는 바람이 태풍 수준이었습니다. 이것이 바로 트럭이 이러한 날짜에 아무것도 판매할 수 없었던 더 타당한 이유인 것 같습니다. 하지만 조정에서 이 분석을 실행했기에 이제 분석가가 이러한 인사이트에 스스로 액세스할 수 있도록 분석에 이 내용을 제공하기 위한 여정을 시작하겠습니다.

### 5단계 - 다음 클릭 -->

## 데이터 인사이트 민주화

Duration: 3

### 개요

이제 태풍 수준의 바람이 아마도 금융 분석가가 언급했던 매출이 0인 날짜에 영향을 준 것 같다고 판단했습니다.

모든 Tasty Bytes 직원이 액세스할 수 있는 분석 뷰를 배포하여 이제 이러한 연구를 조직 내 모두에게 제공하겠습니다.

### 1단계- SQL 함수 생성

세계적인 회사로서 우선 화씨 섭씨 변환 및 인치 밀리미터 변환을 위한 2개의 SQL 함수를 생성하며 프로세스를 시작하겠습니다.

이 단계에서는 [CREATE FUNCTION](https://docs.snowflake.com/ko/sql-reference/sql/create-function) 명령을 활용하는 `fahrenheit_to_celsius` 및 `inch_to_millimeter` 함수를 생성하기 위해 2개의 쿼리를 하나씩 실행하십시오.

```
CREATE OR REPLACE FUNCTION frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(temp_f NUMBER(35,4))
RETURNS NUMBER(35,4)
AS
$$
    (temp_f - 32) * (5/9)
$$;
```

<img src = "assets/5.1.f_to_c.png">

```
CREATE OR REPLACE FUNCTION frostbyte_tasty_bytes.analytics.inch_to_millimeter(inch NUMBER(35,4))
RETURNS NUMBER(35,4)
    AS
$$
    inch * 25.4
$$;
```

<img src = "assets/5.1.inch_to_mm.png">

> aside positive UDF를 생성할 때 지원되는 언어 중 하나로 코드가 작성된 핸들러를 지정합니다. 핸들러의 언어에 따라 CREATE FUNCTION 문이 포함된 핸들러 소스 코드 인라인을 포함하거나 핸들러가 미리 컴파일되었거나 스테이지의 소스 코드인 경우에 CREATE FUNCTION에서 핸들러 위치를 참조할 수 있습니다.

### 2단계 - 뷰를 위한 SQL 생성

분석 뷰를 배포하기 전에 일일 매출과 날씨를 결합하기 위해 뷰에서 사용할 SQL을 생성하고 SQL 변환 함수를 활용하겠습니다.

독일 함부르크를 필터링하고 [ZEROIFNULL](https://docs.snowflake.com/ko/sql-reference/functions/zeroifnull), [ROUND](https://docs.snowflake.com/ko/sql-reference/functions/round) 및 [DATE](https://docs.snowflake.com/ko/sql-reference/functions/to_date)와 같이 아직 확인하지 않은 몇몇 함수를 활용하는 다음 쿼리를 실행하십시오.

```
SELECT 
    fd.date_valid_std AS date,
    fd.city_name,
    fd.country_desc,
    ZEROIFNULL(SUM(odv.price)) AS daily_sales,
    ROUND(AVG(fd.avg_temperature_air_2m_f),2) AS avg_temperature_fahrenheit,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(fd.avg_temperature_air_2m_f)),2) AS avg_temperature_celsius,
    ROUND(AVG(fd.tot_precipitation_in),2) AS avg_precipitation_inches,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.inch_to_millimeter(fd.tot_precipitation_in)),2) AS avg_precipitation_millimeters,
    MAX(fd.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v fd
LEFT JOIN frostbyte_tasty_bytes.harmonized.orders_v odv
    ON fd.date_valid_std = DATE(odv.order_ts)
    AND fd.city_name = odv.primary_city
    AND fd.country_desc = odv.country
WHERE 1=1
    AND fd.country_desc = 'Germany'
    AND fd.city = 'Hamburg'
    AND fd.yyyy_mm = '2022-02'
GROUP BY fd.date_valid_std, fd.city_name, fd.country_desc
ORDER BY fd.date_valid_std ASC;
```

<img src = "assets/5.2.SQL.png">

방금 수신한 결과가 만족스럽습니다. 이제 다음 단계에서는 뷰에서 이 SQL을 래핑할 수 있습니다.

### 3단계 - 분석 뷰 배포

방금 탐색한 동일한 쿼리를 사용하여 WHERE 절에서 필터를 제거하고, [COMMENT](https://docs.snowflake.com/ko/sql-reference/sql/comment)를 추가하고, 이를 `daily_city_metrics_v` 뷰로 `analytics` 스키마에 전달해야 합니다.

이 작업을 수행하기 위해 이제 이 섹션의 마지막 쿼리를 실행하십시오.

```
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.analytics.daily_city_metrics_v
COMMENT = 'Daily Weather Source Metrics and Orders Data for our Cities'
    AS
SELECT 
    fd.date_valid_std AS date,
    fd.city_name,
    fd.country_desc,
    ZEROIFNULL(SUM(odv.price)) AS daily_sales,
    ROUND(AVG(fd.avg_temperature_air_2m_f),2) AS avg_temperature_fahrenheit,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(fd.avg_temperature_air_2m_f)),2) AS avg_temperature_celsius,
    ROUND(AVG(fd.tot_precipitation_in),2) AS avg_precipitation_inches,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.inch_to_millimeter(fd.tot_precipitation_in)),2) AS avg_precipitation_millimeters,
    MAX(fd.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v fd
LEFT JOIN frostbyte_tasty_bytes.harmonized.orders_v odv
    ON fd.date_valid_std = DATE(odv.order_ts)
    AND fd.city_name = odv.primary_city
    AND fd.country_desc = odv.country
WHERE 1=1
GROUP BY fd.date_valid_std, fd.city_name, fd.country_desc;
```

<img src = "assets/5.3.view.png">

이제 이러한 인사이트를 Tasty Bytes 조직을 대상으로 민주화했습니다. 다음 섹션에서 모두 결합하여 작업을 검증하겠습니다.

### 4단계 - 다음 클릭 -->

## 매출 및 마켓플레이스 날씨 데이터에서 인사이트 도출

Duration: 1

### 개요

푸드 트럭이 운영되는 모든 도시에 대한 사용 가능한 매출 및 날씨 데이터를 통해 이제 금융 분석가에게 인사이트를 제공하는 데 걸리는 시간을 단축한 방법을 알아보겠습니다.

### 1단계 - 분석 간소화

앞서 함부르크 매출 이슈를 조사하기 위해 판매 시점 및 Weather Source 데이터를 수동으로 결합했지만, `analytics.daily_city_metrics_v` 뷰를 통해 이 프로세스를 크게 간소화했습니다.

단일 뷰에서 이를 단순한 SELECT 문으로 만들어 이 분석을 얼마나 더 단순하게 만들었는지를 보여주는 다음 쿼리를 실행하십시오.

```
SELECT 
    dcm.date,
    dcm.city_name,
    dcm.country_desc,
    dcm.daily_sales,
    dcm.avg_temperature_fahrenheit,
    dcm.avg_temperature_celsius,
    dcm.avg_precipitation_inches,
    dcm.avg_precipitation_millimeters,
    dcm.max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.analytics.daily_city_metrics_v dcm
WHERE 1=1
    AND dcm.country_desc = 'Germany'
    AND dcm.city_name = 'Hamburg'
    AND dcm.date BETWEEN '2022-02-01' AND '2022-02-26'
ORDER BY date DESC;
```

<img src = "assets/6.1.results.png">

**좋습니다!** 금융 분석가가 초기에 연구를 진행할 때 이것이 제공되었다면 인사이트를 바로 확인할 수 있기에 데이터 팀에 도움을 요청하지 않아도 되었을 것입니다.

이 Quickstart를 완료하면서 작업을 통해 실제 비즈니스 가치를 얼마나 빠르게 도출할 수 있는지 그리고 추가적인 데이터 인사이트를 확보하기 위해 Snowflake 마켓플레이스를 사용하는 것이 얼마나 쉬운지 확인했습니다.

### 2단계 - 다음 클릭 -->

## 종료 및 다음 단계

Duration: 1

### 결론

훌륭합니다! Tasty Bytes - 제로부터 Snowflake까지 - 협업 Quickstart를 성공적으로 완료하셨습니다.

이를 완료하면서 진행한 내용은 다음과 같습니다.

- Snowflake 마켓플레이스에 액세스
- 계정에서 라이브 Weather Source 데이터 획득
- 뷰 생성
- SQL 함수 생성
- 시각적 인사이트를 탐색하기 위해 Snowsight 그래프 활용

이 Quickstart를 다시 실행하려면 관련 워크시트 하단에 있는 초기화 스크립트를 활용하십시오.

### 다음 단계

Snowflake 데이터 클라우드에서의 여정을 계속하려면 이제 아래 링크를 방문하여 사용 가능한 모든 Tasty Bytes 활용 - Quickstart를 확인하십시오.

- ### [Tasty Bytes 사용 - Quickstarts 목차](/guide/tasty_bytes_introduction_kr/index.html#3)
