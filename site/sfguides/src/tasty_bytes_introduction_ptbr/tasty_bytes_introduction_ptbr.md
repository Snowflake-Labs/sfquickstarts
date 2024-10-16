author: Jacob Kranzler
id: tasty_bytes_introduction_ptbr
summary: Este é o quickstart guide “Introdução à Tasty Bytes e base de dados“
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Introdução, Getting Started, Tasty Bytes, Zero to Snowflake, Do zero ao Snowflake, ptbr

# Introdução à Tasty Bytes
<!-- ------------------------ -->

## Introdução à Tasty Bytes 
Duration: 1 <img src="assets/tasty_bytes_header.png"/>

### Visão geral
Neste quickstart “Introdução à Tasty Bytes“, você vai conhecer a marca fictícia de food trucks Tasty Bytes, criada pela equipe frostbyte da Snowflake.

Após saber mais sobre a organização Tasty Bytes, vamos realizar o processo de configuração do modelo de dados funcional da Tasty Bytes, bem como de funções e armazenamentos específicos das cargas de trabalho e de todo o controle de acesso baseado em funções (role-based access control, RBAC) necessário. 

Ao finalizar este guia, você terá implementado os elementos básicos necessários para executar os quickstarts da seção [Powered by Tasty Bytes - quickstarts](/guide/tasty_bytes_introduction_ptbr/index.html#3).

### Quem é a Tasty Bytes?
<img src="assets/who_is_tasty_bytes.png"/>

### Pré-requisitos
- Um [navegador](https://docs.snowflake.com/pt/user-guide/setup#browser-requirements) compatível com Snowflake.
- Conta Snowflake Enterprise ou Business Critical.
    - Caso não possua uma conta Snowflake, [**inscreva-se para receber uma conta de avaliação gratuita de 30 dias**](https://signup.snowflake.com/?lang=pt-br). No ato da inscrição, escolha a opção **Enterprise**. É possível escolher qualquer [nuvem/região do Snowflake](https://docs.snowflake.com/pt/user-guide/intro-regions).
    - Após a inscrição, você receberá um email com um link de ativação e a URL da sua conta Snowflake.
    - <img src="assets/choose_edition.png" width="300"/>
    
### Você vai aprender 
- Criar uma planilha do Snowflake.
- Executar todas as consultas de uma planilha do Snowflake de forma síncrona.
- Explorar bancos de dados, esquemas, tabelas, funções e armazenamentos via SQL em uma planilha do Snowflake.

### O que será desenvolvido
- Elementos básicos para a Tasty Bytes que permitam executar os Powered by Tasty Bytes - quickstarts. 
    - Um banco de dados Snowflake.
    - Esquemas brutos, harmonizados e analíticos completos com tabelas e exibições.
    - Funções e armazenamentos Snowflake específicos das cargas de trabalho.
    - Controle de acesso baseado em funções (RBAC)

## Configuração da Tasty Bytes
Duration: 6

### Visão geral
Neste quickstart, você usará a interface da web do Snowflake, conhecida como Snowsight. Caso seja sua primeira vez usando o Snowsight, recomendamos consultar a [documentação do Snowsight](https://docs.snowflake.com/pt/user-guide/ui-snowsight) para obter orientações gerais.

### Etapa 1 - Acessar o Snowflake via URL
- Abra o navegador e insira a URL da sua conta Snowflake. Caso ainda não tenha uma conta Snowflake, volte à seção anterior para se inscrever em uma conta de avaliação gratuita. 

### Etapa 2 - Fazer login no Snowflake
- Acesse sua conta Snowflake.
    - <img src ="assets/log_into_snowflake.gif" width = "300"/>

### Etapa 3 - Acessar as planilhas
- Clique na guia Worksheets na barra de navegação à esquerda.
    - <img src ="assets/worksheet_tab.png" width="250"/>

### Etapa 4 - Criar uma planilha
- Dentro da guia Worksheets, clique no botão “+” no canto superior direito do Snowsight e escolha “SQL Worksheet”.
    - <img src = "assets/+_sqlworksheet.png" width ="200">

### Etapa 5 - Renomear uma planilha
- Renomeie a planilha clicando no carimbo de data/hora gerado automaticamente e digite “Tasty Bytes, configuração”.
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

### Etapa 6 - Acessar o Setup SQL armazenado no GitHub
- Clique no botão abaixo para acessar o arquivo Tasty Bytes Setup SQL hospedado no GitHub.

<button>[tb_introduction.sql](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/tasty_bytes/tb_introduction.sql)</button>

### Etapa 7 - Copiar o Setup SQL do GitHub
- No GitHub, navegue para a direita e clique em “Copy raw contents”. Todas as informações SQL necessárias serão copiadas para sua área de transferência.
    - <img src ="assets/github_copy_raw_contents.png"/>

### Etapa 8 - Colar o Setup SQL do GitHub para a sua planilha do Snowflake
- Volte para o Snowsight e sua planilha recém-criada e cole (*CMD + V no Mac ou CTRL + V no Windows*) o conteúdo copiado do GitHub.

### Etapa 9 - Executar de modo síncrono todo o Setup SQL
- Clique dentro da nova planilha Tasty Bytes - Setup, selecione tudo (*CMD + A no Mac ou CTRL + A no Windows*) e clique em "► Run". 
    - <img src ="assets/run_all_queries.gif"/>

### Etapa 10 - Concluir a configuração
- Após clicar em "► Run", as consultas começarão a ser executadas. As consultas vão ser executadas uma após a outra, com a conclusão da planilha em cerca de 5 minutos. Após a conclusão, você verá a seguinte mensagem: `frostbyte_tasty_bytes setup is now complete`.
    - <img src="assets/setup_complete.png">

### Etapa 11 - Clicar em Next -->

## Exploração dos elementos básicos da Tasty Bytes
Duration: 2

### Visão geral
Após configurar a Tasty Bytes com sucesso, podemos agora explorar o banco de dados, as funções e os armazenamentos que criamos. 

>aside negative **Observação:** dentro da planilha *Tasty Bytes - Setup* criada na seção anterior, vá até a parte inferior, copie, cole e execute o SQL incluído em cada etapa abaixo.
>

### Etapa 1 - Explorar o banco de dados Tasty Bytes
Essa consulta apresentará o banco de dados que criamos com o comando [SHOW DATABASES](https://docs.snowflake.com/pt/sql-reference/sql/show-databases.html). 
```
SHOW DATABASES LIKE 'frostbyte_tasty_bytes';
``` 
<img src = "assets/show_tb_db.png">. 

### Etapa 2 - Explorar os esquemas dentro do banco de dados Tasty Bytes
Essa consulta apresentará os esquemas dentro do banco de dados que criamos com o comando [SHOW SCHEMAS](https://docs.snowflake.com/pt/sql-reference/sql/show-schemas). 
```
SHOW SCHEMAS IN DATABASE frostbyte_tasty_bytes;
``` 
<img src = "assets/show_tb_schemas.png">. 

### Etapa 3 - Explorar as tabelas do esquema RAW_POS no banco de dados Tasty Bytes
Esta consulta apresentará as tabelas no esquema `raw_pos` com o comando [SHOW TABLES](https://docs.snowflake.com/pt/sql-reference/sql/show-tables) 
```
SHOW TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos;
``` 
<img src = "assets/show_tb_tables.png">. 

### Etapa 4 - Explorar as funções Tasty Bytes
Essa consulta apresentará as funções que criamos com o comando [SHOW ROLES](https://docs.snowflake.com/pt/sql-reference/sql/show-roles). 
```
SHOW ROLES LIKE 'tasty%';
``` 
<img src = "assets/show_tb_roles.png">. 

### Etapa 5 - Explorar os armazenamentos Tasty Bytes
Esta consulta apresentará os armazenamentos que criamos com o comando [SHOW WAREHOUSES](https://docs.snowflake.com/pt/sql-reference/sql/show-warehouses). 
```
SHOW WAREHOUSES LIKE 'tasty%';
``` 
<img src = "assets/show_tb_whs.png">. 

### Etapa 6 - Combinar todos os elementos
As próximas três consultas vão: 1\. Assumir a função `tasty_data_engineer` com o comando [USE ROLE](https://docs.snowflake.com/pt/sql-reference/sql/use-role.html). 2. Usar o armazenamento `tasty_de_wh` com o comando [USE WAREHOUSE](https://docs.snowflake.com/pt/sql-reference/sql/use-warehouse.html). 3. Consultar nossa tabela `raw_pos.menu` para saber quais itens do menu são vendidos em nossos food trucks com a marca Plant Palace.
    
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
<img src = "assets/plant_palace.png"> 

Incrível! Em poucos minutos temos um ambiente de demonstração Tasty Bytes completo com dados, funções e armazenamentos configurados na nossa conta Snowflake. Agora, vamos ver todos os outros Tasty Bytes Quickstarts que podemos usar.

### Etapa 7 - Clicar em Next -->

## Powered by Tasty Bytes - quickstarts
Duration: 1

### Visão geral
Parabéns! Você acaba de concluir a configuração dos elementos básicos para a Tasty Bytes!

O índice abaixo vai listar todos os Tasty Bytes Quickstarts que podem utilizar os elementos básicos que você acaba de criar.

<img src ="assets/pbtb_quickstarts.png"/>

### Do zero ao Snowflake

- #### [Governança financeira](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_financial_governance/)
    - Saiba mais sobre os armazenamentos virtuais Snowflake e suas opções de configuração, monitores de recursos e parâmetros de tempo limite no nível de conta e armazenamento.
- #### [Transformação](/guide/tasty_bytes_zero_to_snowflake_transformation_ptbr/)
    - Saiba mais sobre o Snowflake Zero Copy Cloning, cache de conjunto de resultados, manipulação de tabelas, Time-Travel e funcionalidades de troca, descarte e cancelamento de descarte de tabelas.
- #### [Dados semiestruturados](/guide/tasty_bytes_zero_to_snowflake_semi_structured_data_ptbr/)
    - Saiba mais sobre o formato VARIANT de dados do Snowflake, processamento de dados semiestruturados com uso de notação de pontos e nivelamento lateral, bem como criação de exibições e criação de gráficos com o Snowsight.
- #### [Governança de dados](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_data_governance/)
    - Saiba mais sobre as funções definidas pelo sistema Snowflake, crie e aplique permissões a uma função personalizada e implemente Dynamic Data Masking baseado em tags e políticas de acesso a linhas.
- #### [Colaboração](/guide/tasty_bytes_zero_to_snowflake_collaboration_ptbr/)
    - Saiba mais sobre o Snowflake Marketplace com dados ativos gratuitos, disponibilizados instantaneamente pelo Weather Source para conduzir análises baseadas em dados, harmonizando fontes primárias e terciárias.
- #### [Geoespacial](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_geospatial/)
    - Saiba mais sobre o suporte geoespacial do Snowflake, começando pela aquisição gratuita de dados ativos e disponíveis instantaneamente do SafeGraph, depois passando para a criação de pontos geográficos (ST_POINT), cálculos de distância (ST_DISTANCE), coleta de coordenadas (ST_COLLECT), criação de um polígono de delimitação mínimo (ST_ENVELOPE), cálculo de área (ST_AREA) e determinação de pontos centrais (ST_CENTROID).

### Guias detalhados das cargas de trabalho (*em breve*)
