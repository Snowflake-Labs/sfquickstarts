author: Swathi Jasti
id: developing-tasty-bytes-react-native-application-with-snowflake-sql-api-it
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/native-apps, snowflake-site:taxonomy/solution-center/certification/community-sourced
language: en
summary: Sviluppare una data application React Native per Tasty Bytes con Snowflake, SQL API
environments: web
status: Pubblicato
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Tasty Bytes - Sviluppare una data application React Native con la SQL API
<!-- ------------------------ -->
## Panoramica

Nell’attuale panorama data-driven, la maggior parte delle applicazioni si è evoluta verso un impiego sempre più intenso dei dati. Tuttavia, sviluppare data application di successo può essere una sfida, soprattutto in vista della crescita sia del numero di utenti che del volume e della complessità dei dati. Snowflake è la forza motrice di numerose applicazioni basate sui dati e consente ai team specializzati in software di accelerare la progettazione e creare applicazioni scalabili evitando le complessità operative. Concentrandosi sull’incremento della velocità di progettazione, Snowflake offre prestazioni e scalabilità eccezionali per le applicazioni. 

Per accelerare lo sviluppo di data app, Snowflake offre la SQL API, un’API RESTful che consente di accedere ai dati e manipolarli in modo trasparente all’interno del database Snowflake. La SQL API fa da tramite tra la tua applicazione e Snowflake, consentendoti di recuperare e aggiornare i dati in modo programmatico.

In questo tutorial creerai un’applicazione il cui scopo è aiutare l’azienda di food truck fittizia Tasty Bytes e i suoi conducenti a visualizzare gli ordini dei clienti e consentire ai conducenti di completare gli ordini una volta effettuata la consegna. Questo tutorial ti guiderà nello sviluppo di un’applicazione React Native per i conducenti dei food truck utilizzando la SQL API. 

### Prerequisiti
- I privilegi necessari per creare un utente, un database e un warehouse in Snowflake
- La possibilità di installare ed eseguire software sul tuo computer
- Esperienza di base nell’uso di git
- Conoscenza di SQL a livello intermedio
- Accesso per eseguire SQL in Snowflake

### Cosa imparerai 
- Come sviluppare data application con Snowflake e la SQL API
- Come eseguire l’autenticazione in Snowflake con il metodo della coppia di chiavi
- Come generare un token JWT in Javascript

### Cosa ti serve 
- Un account [GitHub](https://github.com/) 
- [VS Code](https://code.visualstudio.com/download) installato (oppure il tuo IDE preferito) 
- [NodeJS](https://nodejs.org/en/download/) installato

### Cosa realizzerai 
- Una data application utilizzando la SQL API

<!-- ------------------------ -->
## Configurare i dati in Snowflake

Per questa demo utilizzeremo i dati sugli ordini di Tasty Bytes. Utilizzando i dati sugli ordini creerai un’applicazione per i conducenti dei food truck con le seguenti funzionalità:
- Il conducente può vedere gli ordini nella sua coda
- Il conducente può completare l’ordine aggiornando lo stato dell’ordine in Snowflake
- Il conducente può vedere gli ordini completati.

Utilizzerai [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), l’interfaccia web di Snowflake, per:
- Creare oggetti Snowflake (warehouse, database, schema)
- Caricare i dati da S3
- Creare viste unendo i dati

### Creare oggetti, caricare i dati e unire i dati

Vai a Worksheets, fai clic su “+” nell’angolo superiore destro per creare un nuovo foglio di lavoro e scegli “SQL Worksheet”.

Incolla ed esegui il seguente codice SQL nel foglio di lavoro per creare oggetti Snowflake (warehouse, database, schema), caricare i dati degli ordini grezzi da S3 e modellarli per l’uso a valle.

``` sql 
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
    unit_price NUMBER(19,3); 
);

-- create our virtual warehouse 
CREATE OR REPLACE WAREHOUSE tasty_app_wh AUTO_SUSPEND = 60;

-- use our TASTY_APP_WH virtual warehouse so we can load our data 
USE WAREHOUSE tasty_app_wh;

-- ingest from S3 into the app_order_header 
table COPY INTO frostbyte_tasty_bytes_app.raw.app_order_header 
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
## Creare un utente per l’applicazione

Per garantire l’efficacia delle misure di sicurezza, è essenziale stabilire un account utente dedicato per l’applicazione, separato dal tuo account personale. Questo nuovo account verrà utilizzato per interrogare Snowflake. Secondo le best practice di sicurezza, l’account utilizzerà l’autenticazione a coppia di chiavi e avrà un accesso limitato all’interno dell’ambiente Snowflake.

### Passaggio 1 -  Generare la chiave pubblica e privata per l’autenticazione
Esegui i seguenti comandi per creare una chiave pubblica e una chiave privata. Queste chiavi sono necessarie per autenticare l’utente in Snowflake.

``` Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_app_key 4096
$ openssl rsa -in snowflake_app_key -pubout -out snowflake_app_key.pub
```

### Passaggio 2 -  Creare l’utente e il ruolo in Snowflake e concedere l’accesso ai dati a questo nuovo ruolo

Esegui le seguenti istruzioni SQL per creare l’account utente e concedere l’accesso ai dati necessari per l’applicazione.

``` SQL 
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
DEFAULT_WAREHOUSE=tasty_app_wh MUST_CHANGE_PASSWORD=false;

-- use our securityadmin role 
USE ROLE securityadmin; 
GRANT ROLE tasty_bytes_data_app_demo TO USER data_app_demo; 
```

<!-- ------------------------ -->
## Data application con la SQL API

L’applicazione che eseguirai è scritta in React Native. 

### Passaggio 1 -  Ottenere il codice sorgente
1. Clona il repository utilizzando ``` git clone https://github.com/sf-gh-sjasti/TastyBytesReactNativeAppWithSnowflake-SQL_API.git reactNativeApp ```
2. Vai alla cartella ``` cd reactNativeApp ```
3. Esegui ``` npm install ``` per installare le dipendenze

### Passaggio 2 -  Configurare l’applicazione
1. Apri la cartella ``` reactNativeApp ``` in VS Code o nel tuo IDE preferito.
2. Apri il file ``` .env ``` e aggiorna il valore ``` PRIVATE_KEY ``` con la chiave privata. Copia e incolla l’intera chiave privata da ``` ~/.ssh/snowflake_app_key.pub ```, compresa l’intestazione (``` -----BEGIN RSA PRIVATE KEY----- ```) e il piè di pagina (``` -----END RSA PRIVATE KEY----- ```).
3. Se ti trovi nella regione US-West, aggiorna ``` SNOWFLAKE_ACCOUNT_IDENTIFIER ``` con il tuo account Snowflake oppure, se non ti trovi nella regione US-West, aggiorna ``` SNOWFLAKE_ACCOUNT_IDENTIFIER ``` con '<SNOWFLAKE ACCOUNT>.<REGION>'. Per recuperare il valore snowflake_account da Snowflake, esegui ``` SELECT CURRENT_ACCOUNT() ``` in Snowsight. Per recuperare il valore della regione da Snowflake, esegui ``` SELECT CURRENT_REGION() ``` in Snowsight. Per la regione US-West, SNOWFLAKE_ACCOUNT_IDENTIFIER e SNOWFLAKE_ACCOUNT sono uguali. 
4. Aggiorna ``` SNOWFLAKE_ACCOUNT ``` con il tuo account Snowflake.
5. Aggiorna ``` PUBLIC_KEY_FINGERPRINT ``` con l’impronta digitale della tua chiave pubblica. Per ottenere l’impronta digitale della chiave pubblica, esegui il seguente codice SQL in Snowsight ```DESCRIBE USER data_app_demo ``` e recupera il valore della proprietà RSA_PUBLIC_KEY_FP.

### Passaggio 3 -  Esaminare il codice sorgente
Stiamo utilizzando l’autenticazione a coppia di chiavi per eseguire l’autenticazione in Snowflake tramite la SQL API. Per capire come generiamo il token JWT, puoi fare riferimento a ``` Tokens.js ```. ``` Orders.js ``` contiene il codice sorgente per il rendering della schermata Locations. Puoi anche fare riferimento a questo file per scoprire come avviare una chiamata alla SQL API e le intestazioni necessarie. ``` OrderDetails.js ``` contiene il codice sorgente per il rendering della schermata Order Details.

### Passaggio 4 -  Testare l’applicazione
1. Esegui ``` npx expo start --clear ``` e premi il tasto ``` w ``` per eseguire l’applicazione in un browser web
2. L’applicazione viene avviata in un browser web
3. All’avvio viene visualizzata la schermata degli ordini in coda,

![assets/OrdersInQueue.png](assets/OrdersInQueue.png)

4. Ora fai clic su View Order per vedere i dettagli dell’ordine.

![assets/OrderDetails.png](assets/OrderDetails.png)

5. Fai clic sul pulsante ORDER READY per completare l’ordine. Questa azione aggiorna il valore Order Status per questo ordine impostandolo su Completed e ti riporta alla schermata degli ordini in coda
6. Ora fai clic sulla scheda Order History per vedere gli ordini completati.

![assets/OrderHistory.png](assets/OrderHistory.png)

<!-- ------------------------ -->
## Pulizia

Vai a Snowsight Worksheets, fai clic su “+” nell’angolo superiore destro per creare un nuovo foglio di lavoro e scegli “SQL Worksheet”. Incolla ed esegui il seguente codice SQL nel foglio di lavoro per eliminare gli oggetti Snowflake creati in questo quickstart.

``` sql 
USE ROLE accountadmin; 
DROP DATABASE frostbyte_tasty_bytes_app; 
DROP WAREHOUSE tasty_app_wh;

USE ROLE securityadmin; 
DROP USER data_app_demo; 
DROP ROLE tasty_bytes_data_app_demo; 
```

<!-- ------------------------ -->
## Conclusione

### Conclusione
**Ce l’hai fatta!** Hai completato il quickstart Tasty Bytes - Sviluppare una data application React Native con l’API SQL.

Completando questo quickstart hai:
- Sviluppato una data application utilizzando Snowflake e la SQL API
- Eseguito l’autenticazione in Snowflake con il metodo della coppia di chiavi
- Generato un token JWT in Javascript

### Fasi successive
Per continuare il tuo percorso nel Data Cloud di Snowflake, visita il link riportato sotto per vedere gli altri quickstart Powered by Tasty Bytes disponibili.

- ### [Quickstart Powered by Tasty Bytes - Sommario](/it/developers/guides/tasty-bytes-introduction-it/)
