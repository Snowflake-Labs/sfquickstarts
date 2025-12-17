author: Jacob Kranzler
id: tasty-bytes-introduction-it
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: it
summary: This is the Tasty Bytes Introduction and Data Foundation Quickstart guide
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Introduzione a Tasty Bytes
<!-- ------------------------ -->

## Introduzione a Tasty Bytes 

### Panoramica
In questo quickstart Introduzione a Tasty Bytes per prima cosa farai la conoscenza del marchio fittizio di food truck Tasty Bytes, creato dal team frostbyte di Snowflake.

Dopo avere conosciuto l’organizzazione Tasty Bytes, completeremo la configurazione del suo modello dati di base, dei ruoli e dei warehouse specifici per i workload e di tutti i controlli degli accessi basati sui ruoli (RBAC) necessari. 

Al termine di questo quickstart avrai implementato l’ambiente base necessario per eseguire i quickstart contenuti nella sezione [Quickstart Powered by Tasty Bytes](/it/developers/guides/tasty-bytes-introduction-it/).

### Che cos’è Tasty Bytes?
![assets/who_is_tasty_bytes.png](assets/who_is_tasty_bytes.png)

### Prerequisiti
- Un [browser](https://docs.snowflake.com/en/user-guide/setup#browser-requirements) supportato da Snowflake
- Un account Snowflake Enterprise o Business Critical
    - Se non hai un account Snowflake, [**richiedi la tua prova gratuita di 30 giorni**](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides). Al momento della registrazione, assicurati di selezionare **Enterprise** Edition. Puoi scegliere qualsiasi [cloud o regione di Snowflake](https://docs.snowflake.com/en/user-guide/intro-regions).
    - Al termine della registrazione, riceverai un’email con un link per l’attivazione e l’URL del tuo account Snowflake.
    - ![assets/choose_edition.png](assets/choose_edition.png)
    
### Cosa imparerai 
- Come creare un foglio di lavoro Snowflake
- Come eseguire tutte le query in un foglio di lavoro Snowflake in modo sincrono
- Come esplorare database, schemi, tabelle, ruoli e warehouse tramite SQL in un foglio di lavoro Snowflake

### Cosa realizzerai
- L’ambiente base di Tasty Bytes che ti consentirà di eseguire i quickstart Powered by Tasty Bytes. 
    - Un database Snowflake
    - Schemi di dati grezzi, armonizzati e analitici completi di tabelle e viste
    - Ruoli e warehouse di Snowflake specifici per i workload
    - Controllo degli accessi basato sui ruoli (RBAC)

## Configurare Tasty Bytes

### Panoramica
Per questo quickstart utilizzerai l’interfaccia web di Snowflake nota come Snowsight. Se questa è la prima volta che utilizzi Snowsight, ti consigliamo caldamente di dare un’occhiata alla [documentazione di Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight) per una spiegazione a livello generale.

### Passaggio 1 - Accedere a Snowflake tramite URL
- Apri una finestra del browser e inserisci l’URL del tuo account Snowflake. Se non hai già un account Snowflake, torna alla sezione precedente e registrati per provare Snowflake gratuitamente. 

### Passaggio 2 - Effettuare l’accesso a Snowflake
- Accedi al tuo account Snowflake.
    - ![assets/log_into_snowflake.gif](assets/log_into_snowflake.gif)

### Passaggio 3 - Accedere ai fogli di lavoro
- Fai clic sulla scheda Worksheets nella barra di navigazione sulla sinistra.
    - ![assets/worksheet_tab.png](assets/worksheet_tab.png)

### Passaggio 4 - Creare un foglio di lavoro
- Nella scheda Worksheets, fai clic sul pulsante “+” nell’angolo superiore destro di Snowsight e scegli “SQL Worksheet”
    - ![assets/+_sqlworksheet.png](assets/+_sqlworksheet.png)

### Passaggio 5 - Rinominare un foglio di lavoro
- Rinomina il foglio di lavoro facendo clic sul nome generato automaticamente (data e ora) e inserendo “Tasty Bytes - Setup”.
    - ![assets/rename_worksheet_tasty_bytes_setup.gif](assets/rename_worksheet_tasty_bytes_setup.gif)

### Passaggio 6 - Accedere al file di configurazione SQL su GitHub
- Fai clic sul pulsante qui sotto, che ti porterà al file di configurazione SQL di Tasty Bytes archiviato su GitHub.

<button>[tb\_introduction.sql](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/tasty_bytes/tb_introduction.sql)</button>

### Passaggio 7 - Copiare la configurazione SQL da GitHub
- In GitHub, vai sul lato destro e fai clic su “Copy raw contents”. Tutto il codice SQL necessario verrà copiato nei tuoi Appunti.
    - ![assets/github_copy_raw_contents.png](assets/github_copy_raw_contents.png)

### Passaggio 8 - Incollare la configurazione SQL da GitHub nel tuo foglio di lavoro Snowflake
- Torna a Snowsight e al foglio di lavoro che hai appena creato e incolla (*CMD + V per Mac o CTRL + V per Windows*) il codice che abbiamo appena copiato da GitHub.

### Passaggio 9 - Eseguire in modo sincrono tutto il codice SQL di configurazione
- Fai clic nel foglio di lavoro “Tasty Bytes - Setup” appena creato, seleziona tutto (*CMD + A per Mac o CTRL + A per Windows*) e fai clic su “► Run” 
    - ![assets/run_all_queries.gif](assets/run_all_queries.gif)

### Passaggio 10 - Completare la configurazione
- Dopo avere fatto clic su “► Run” inizierà l’esecuzione delle query. Queste query verranno eseguite una dopo l’altra e l’intero foglio di lavoro richiederà circa 5 minuti. Al termine comparirà il seguente messaggio: `frostbyte_tasty_bytes setup is now complete` .
    - ![assets/setup_complete.png](assets/setup_complete.png)

### Passaggio 11 - Fai clic su Next -->

## Esplorare l’ambiente base di Tasty Bytes

### Panoramica
Dopo avere completato correttamente la configurazione di Tasty Bytes, possiamo esplorare il database, i ruoli e i warehouse che abbiamo creato. 

> 
>

### Passaggio 1 - Esplorare il database Tasty Bytes
Questa query restituisce il database che abbiamo creato tramite [SHOW DATABASES](https://docs.snowflake.com/en/sql-reference/sql/show-databases.html).
 ```
USE ROLE sysadmin;
SHOW DATABASES LIKE 'frostbyte_tasty_bytes';
``` 
![assets/show_tb_db.png](assets/show_tb_db.png) 

### Passaggio 2 - Esplorare gli schemi nel database Tasty Bytes
Questa query restituisce gli schemi all’interno del database che abbiamo creato tramite [SHOW SCHEMAS](https://docs.snowflake.com/en/sql-reference/sql/show-schemas). 
```
SHOW SCHEMAS IN DATABASE frostbyte_tasty_bytes;
``` 
![assets/show_tb_schemas.png](assets/show_tb_schemas.png) 

### Passaggio 3 - Esplorare le tabelle nello schema RAW\_POS all’interno del database Tasty Bytes
Questa query restituisce le tabelle all’interno dello schema `raw_pos` tramite [SHOW TABLES](https://docs.snowflake.com/en/sql-reference/sql/show-tables) 
```
SHOW TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos;
``` 
![assets/show_tb_tables.png](assets/show_tb_tables.png) 

### Passaggio 4 - Esplorare i ruoli di Tasty Bytes
Questa query restituisce i ruoli che abbiamo creato tramite [SHOW ROLES](https://docs.snowflake.com/en/sql-reference/sql/show-roles). 
```
SHOW ROLES LIKE 'tasty%';
``` 
![assets/show_tb_roles.png](assets/show_tb_roles.png) 

### Passaggio 5 - Esplorare i warehouse Tasty Bytes
Questa query restituisce i warehouse che abbiamo creato tramite [SHOW WAREHOUSES](https://docs.snowflake.com/en/sql-reference/sql/show-warehouses). 
```
SHOW WAREHOUSES LIKE 'tasty%';
``` 
![assets/show_tb_whs.png](assets/show_tb_whs.png) 

### Passaggio 6 - Combinare tutti gli elementi
Le prossime tre query: 
1. Assumono il ruolo `tasty_data_engineer` tramite [USE ROLE](https://docs.snowflake.com/en/sql-reference/sql/use-role.html) 
2. Utilizzano il warehouse `tasty_de_wh` tramite [USE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/use-warehouse.html) 
3. Interrogano la tabella `raw_pos.menu` per trovare quali voci di menu sono vendute nei food truck con il marchio Plant Palace.
    
```
USE ROLE tasty_data_engineer;
USE WAREHOUSE tasty_de_wh;

SELECT
    m.menu_type_id,
    m.menu_type,
    m.truck_brand_name,
    m.menu_item_name
FROM frostbyte_tasty_bytes.raw_pos.menu m
WHERE m.truck_brand_name = 'Plant Palace';
```
![assets/plant_palace.png](assets/plant_palace.png) 

Fantastico! In pochi minuti abbiamo configurato un ambiente demo Tasty Bytes completo di dati, ruoli e warehouse nel nostro account Snowflake. Ora diamo un’occhiata a tutti gli altri quickstart Tasty Bytes a nostra disposizione.

### Passaggio 7 - Fai clic su Next -->

## Quickstart Powered by Tasty Bytes

### Panoramica
Congratulazioni! Hai completato la configurazione dell’ambiente base di Tasty Bytes.

Il sommario riportato di seguito descrive tutti i quickstart Tasty Bytes disponibili che utilizzano l’ambiente base che hai appena creato.

![assets/pbtb_quickstarts.png](assets/pbtb_quickstarts.png)

### Da zero a Snowflake

- #### [Governance finanziaria](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_financial_governance/)
    - Scopri i Virtual Warehouse di Snowflake con le loro configurabilità, i monitor delle risorse e i parametri di timeout a livello di account e di warehouse.
- #### [Trasformazione](/it/developers/guides/tasty-bytes-zero-to-snowflake-transformation-it/)
    - Scopri le funzionalità di cache dei set di risultati, Zero-Copy Cloning, manipolazione delle tabelle, Time Travel e swap, drop e undrop delle tabelle di Snowflake.
- #### [Dati semi-strutturati](/it/developers/guides/tasty-bytes-zero-to-snowflake-semi-structured-data-it/)
    - Scopri il tipo di dati VARIANT di Snowflake, l’elaborazione dei dati semi-strutturati tramite notazione punto e appiattimento laterale, la creazione di viste e i grafici Snowsight.
- #### [Governance dei dati](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_data_governance/)
    - Scopri i ruoli definiti dal sistema di Snowflake, crea e concedi privilegi a un ruolo personalizzato e implementa Dynamic Data Masking basato sui tag e Row Access Policies.
- #### [Collaborazione](/it/developers/guides/tasty-bytes-zero-to-snowflake-collaboration-it/)
    - Scopri il Marketplace Snowflake utilizzando dati aggiornati gratuiti e immediatamente disponibili forniti da Weather Source per svolgere analisi data-driven armonizzando le fonti di dati interne ed esterne.
- #### [Analisi geospaziale](/en/developers/guides/tasty-bytes-zero-to-snowflake-geospatial/)
    - Scopri il supporto per l’analisi geospaziale di Snowflake, iniziando dall’acquisizione di dati aggiornati gratuiti e immediatamente disponibili da SafeGraph per poi creare punti geografici (ST\_POINT), calcolare distanze (ST\_DISTANCE), raccogliere coordinate (ST\_COLLECT), disegnare un poligono di delimitazione minimo (ST\_ENVELOPE), calcolare aree (ST\_AREA) e trovare i punti centrali (ST\_CENTROID).

### Approfondimenti sui workload (*disponibili a breve*)



