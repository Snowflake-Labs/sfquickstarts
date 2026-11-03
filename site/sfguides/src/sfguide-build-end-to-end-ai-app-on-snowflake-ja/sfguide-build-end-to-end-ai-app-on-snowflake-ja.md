author: Ryusuke Niki, Dash Desai
id: sfguide-build-end-to-end-ai-app-on-snowflake-ja
summary: このガイドでは、Snowflake CoCo を使用して、データストリーミングからAIエージェントまでのエンドツーエンドAIアプリケーションを構築する方法を説明します。
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/data-engineering
language: ja
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Snowflake上でCoCoを使ったエンドツーエンドアプリケーションの構築

<!-- ------------------------ -->
## Overview

このハンズオンラボでは、Snowflake内で完全なAI搭載リテール分析プラットフォームを構築します。外部インフラは一切不要です。Snowflake CoCoをAI支援開発環境として使用し、データライフサイクル全体を通して作業します：Snowpipe Streamingによるリアルタイムオーダーのストリーミング、Gen2 Warehouseを使用した本番テーブルへのMERGE、3層Dynamic Tablesパイプラインによる変換、低レイテンシのポイントルックアップのためのInteractive Tablesによるサービング。

dbtによる分析モデルの構築、Data Metric Functionsによるデータ品質の監視、再利用可能なワークフロー用のカスタムCoCoスキルの作成を行います。最後に、Snowflake CoWork — Cortex AgentがCortex AnalystとAgentic Searchを連携させて、構造化データと非構造化データの両方から「何が起きたか」と「なぜ」に答える会話型AIインターフェースですべてを統合します。さらに、グラウンドトゥルースデータセットによるエージェント評価、行レベルセキュリティの実装、外部AIクライアント向けのマネージドMCPサーバーとしてエージェントを公開します。

### 学習内容

- Snowflake CoCo（AI支援SQL、デプロイ、データ探索）による開発の加速
- Snowpipe StreamingとDynamic Tablesによるリアルタイムデータのストリーミングと変換
- Interactive TablesとGen2 Warehousesによる低レイテンシクエリのサービング
- dbtによる分析モデルの構築
- Data Metric Functionsによるデータ品質の自動監視
- マネージドIceberg V3テーブルの作成とクエリ（削除ベクトル、行リネージ）（オプション）
- 再利用可能なチームワークフロー用のカスタムCoCoスキルの作成
- Cortex Agent（セマンティックビュー＋検証済みクエリによるCortex Analyst）とAgentic Search（マルチインデックスCortex Search）の構築
- グラウンドトゥルースデータセットとLLMジャッジによるエージェント品質の評価
- 外部AIクライアント向けマネージドMCPサーバーとしてのエージェント公開
- Row Access Policiesによる透過的な行レベルセキュリティの実装

### 構築するもの

Snowflake上のプロダクショングレードAI搭載リテール分析プラットフォーム — 生データから会話型AIインサイトまで、単一プラットフォーム内で完結します。動的変換パイプライン、インタラクティブ低レイテンシテーブル、dbt分析モデル、構造化・非構造化データにまたがる質問に回答するCortex Agent、AIを通じて透過的に動作する行レベルセキュリティ、外部クライアントにエージェントを公開するMCPサーバーを構築します。

### 前提条件

- [Snowflakeアカウント](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)へのアクセス
- ローカルにPython 3.8+がインストールされていること
- ローカルにGitがインストールされていること
- SQLとコマンドラインツールの基本的な知識

<!-- ------------------------ -->
## セットアップ

### Snowflake CLIのインストール

Snowflake CLI（`snow`）を使用すると、ターミナルからSQL実行、アプリのデプロイ、Snowflakeオブジェクトの管理が可能です。

macOS（Homebrewを使用）：

Homebrewがまだインストールされていない場合は、ターミナルを開いて以下を実行します：

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

次にSnowflake CLIをインストールします：

```
brew install snowflake-cli
```

Windows：

```
pip install snowflake-cli
```

Linux：

```
pip install snowflake-cli
```

インストールを確認します：

```
snow --version
```

`Snowflake CLI version: 3.x.x` のような出力が表示されるはずです。

### Snowflake CoCoのインストール

Snowflake CoCoは、ターミナルで動作するAI搭載コーディングアシスタントです。自然言語プロンプトを使用して、SQL作成、パイプライン構築、アプリのデプロイ、データ探索を支援します。

macOSおよびLinux：

```
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

Windows（PowerShell）：

```
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

インストールを確認します：

```
cortex --version
```

### 代替手段：Snowflake CoCo Desktop（プレビュー）

ビジュアルIDE体験を好む場合は、CLIの代わりに（または併用して）[CoCo Desktop](https://www.snowflake.com/en/product/limited-access/cortex-code/)をダウンロードしてください。ファイルエディター、統合ターミナル、エージェントブラウザ、同じAI機能を備えたネイティブMac/Windowsアプリです。

> CoCo Desktopは現在、すべてのアカウントで利用可能な[プレビュー機能](https://docs.snowflake.com/release-notes/preview-features)です。

初回起動時は、オンボーディングウィザードに従います：

1. Welcomeスクリーンで「Next」をクリック
2. 接続を追加（上記と同じアカウント識別子と認証情報を使用）するか、`connections.toml`から検出された既存のものを選択
3. Agentモードを選択
4. テーマを選択し、「Get Started」をクリック

> ヒント：`snow connection add`（以下）で既に接続を設定している場合、CoCo Desktopは自動的に検出します — リストから選択するだけです。

詳細は[CoCo Desktopドキュメント](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/index)をご覧ください。

### Snowflake接続の設定

Snowflakeに対してコマンドを実行する前に、接続の設定が必要です。これにより、CLIがどのSnowflakeアカウントに接続し、どのように認証するかを指定します。

対話型接続ウィザードを実行します：

```
snow connection add
```

以下の値の入力を求められます（1つずつ入力）：

| 項目 | 説明 | 例 |
|------|------|-----|
| Connection name | この接続の短い名前 | hol |
| Account identifier | SnowflakeアカウントURL（.snowflakecomputing.comを除く） | myorg-myaccount |
| User | Snowflakeユーザー名 | jsmith |
| Password | Snowflakeパスワード | (非表示) |
| Role | ACCOUNTADMIN | ACCOUNTADMIN |
| Warehouse | 空白のまま（セットアップで作成されます） | (空白) |
| Database | 空白のまま（セットアップで作成されます） | (空白) |

> ヒント：アカウント識別子は、SnowflakeのURLで`.snowflakecomputing.com`の前の部分です。例えば、`https://myorg-myaccount.snowflakecomputing.com`でログインする場合、アカウント識別子は`myorg-myaccount`です。

接続をテストします：

```
snow connection test -c hol
```

`Status: OK` と表示されるはずです。

### ラボリポジトリのクローン

```
git clone https://github.com/Snowflake-Labs/automated-intelligence-dev-day-2026-hol.git
cd automated-intelligence-dev-day-2026-hol
```

### インフラストラクチャセットアップの実行

Snowflake CoCoを起動して接続を確認します：

```
cortex
```

> 期待される動作：CoCoはターミナルで対話セッションを開始します。アクティブな接続、ロール、ウェアハウスが表示されます。自然言語プロンプトを入力すると、CoCoがSQLやアクションに変換します。

次に、コアインフラストラクチャスクリプトを実行します（約10-15分かかります）：

```
snow sql -f setup.sql -c hol
```

これにより、データベース、スキーマ、ウェアハウス、テーブル、Dynamic Tablesパイプライン、Interactive Tables、Cortex Search Services、セマンティックビュー、シードデータ（1,000万注文、2,500万注文アイテム、200万顧客）、Row Access Policyが作成されます。

> CoCo Desktopをご使用の場合：以下の「CoCoにプロンプト」の指示は、CLIとDesktopの両方で同じように動作します — チャット入力に同じテキストを入力してください。ターミナルコマンドとして`cortex`が表示される箇所では、Desktopの組み込みターミナルまたはチャットを使用してください。

<!-- ------------------------ -->
## データの探索

セットアップが完了したので、作成されたものを確認しましょう。CoCoとの最初のインタラクションです — データについて自然言語で質問してみてください。

CoCoにプロンプト：

> 「データベースにはどんなスキーマとテーブルがありますか？」

CoCoが`INFORMATION_SCHEMA`をクエリし、データベース構造を表示します：RAW（ソーステーブル＋ビュー）、STAGING（ストリーミングランディングゾーン）、DYNAMIC_TABLES（パイプライン）、INTERACTIVE（低レイテンシ）、SEMANTIC（AIレイヤー）。

> 「ordersテーブルから5行サンプルを見せてください」

> 「注文数、顧客数、製品数はいくつですか？」

期待される結果：約1,000万注文、約2,500万注文アイテム、200万顧客、10製品、1,200レビュー、1,200サポートチケット。

> 「注文データの日付範囲は？」

期待される結果：2025年6月から2025年9月。

これにより、変換と分析を開始する前にデータセットのメンタルモデルが形成されます。

<!-- ------------------------ -->
## データ品質

[Data Metric Functions (DMFs)](https://docs.snowflake.com/en/user-guide/data-quality-intro)を使用すると、テーブルの列に直接自動品質チェックを付加できます。Snowflakeはスケジュールに従ってそれらを実行し、結果を`SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS`に保存します。組み込みDMFには`NULL_COUNT`、`DUPLICATE_COUNT`、`UNIQUE_COUNT`、`FRESHNESS`が含まれます。カスタムDMFも作成可能です。

セットアップスクリプトは`orders.total_amount`と`order_items.quantity`に約200のNULL値、`order_items.product_name`に約150のNULL値を注入しました。DMFは最初の2つを検出しますが、ギャップがあります。

### ギャップの発見

CoCoにプロンプト：

> 「データ品質モニタリングの結果を確認して、どの列にNULL違反があるか見せてください」

CoCoが`TOTAL_AMOUNT`（200 NULLs）と`QUANTITY`（200 NULLs）に違反があることを表示しますが、`product_name`のNULLは検出されていません。

> 「order_items.product_nameにNULL値はありますか？その列は監視されていますか？」

CoCoが約150のNULLを見つけ、DMFが`product_name`ではなく`product_category`に誤って付加されていることを明らかにします。

### カバレッジの修正

> 「DMFを修正してください — product_categoryからNULLチェックを削除し、代わりにproduct_nameに追加してください」

```sql
ALTER TABLE order_items DROP DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (product_category);
ALTER TABLE order_items ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (product_name);
```

これは実際のワークフローを示しています：監視、ギャップの発見、カバレッジの修正。

<!-- ------------------------ -->
## Dynamic Tablesパイプライン

[Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)は宣言的データパイプラインです — ターゲット状態をSQLクエリとして定義すると、Snowflakeが自動的にインクリメンタルリフレッシュを処理します。`TARGET_LAG`パラメータで鮮度を制御します：Tier 1テーブルには時間ベースのラグ（例：`1 minute`）を設定し、Tier 2以降には`DOWNSTREAM`を使用して上流ソースが変更された場合にのみリフレッシュします。

CoCoにプロンプト：

> 「Dynamic Tablesパイプラインのステータスを見せてください — 各ティアの名前、ターゲットラグ、最終リフレッシュ時刻、行数」

CoCoが3層パイプラインを表示します：

- Tier 1（1分ラグ）：`enriched_orders`（1,000万行）、`enriched_order_items`（2,500万行）
- Tier 2（DOWNSTREAM）：`fact_orders`（2,500万行）
- Tier 3（DOWNSTREAM）：`daily_business_metrics`（118行）、`product_performance_metrics`（4行）

> 注意：表示される行数はデフォルトの`data_scale = '10M'`のものです。`setup.sql`で`'50M'`を選択した場合、約5,000万enriched_orders、約1.61億order_items、365日分のメトリクスが予想されます。

### 結果の探索

CoCoに質問：

> 「日次ビジネスメトリクスのサンプルを見せてください — 収益上位5日」

期待される結果：上位5日は2025年9月（新学期のピーク）で、各日約$183Mの収益と約117K注文。

<!-- ------------------------ -->
## dbtアナリティクス

[dbt-snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)は、SQL SELECTステートメントを使用して生データを分析可能なモデルに変換します。dbt-snowflakeアダプターはSnowflakeとネイティブに統合され、インクリメンタルモデル、スナップショット、組み込みテストをサポートします。このHOLでは、dbtが顧客生涯価値、セグメンテーション、製品パフォーマンス、サポート分析のためのステージングビューとマートテーブルを作成します。

> 前提条件：`dbt-core`と`dbt-snowflake`がインストールされている必要があります（`pip install dbt-snowflake`）。CoCoがまだインストールされていない場合は自動的に処理します。

CoCoにプロンプト：

> 「dbt-analyticsプロジェクトのdbt依存関係をインストールし、すべてのモデルをビルドしてください」

CoCoが`dbt deps`を実行し、次に`dbt build`ですべてのステージングビューとマートテーブル（9以上のモデル）を作成します。CoCoはアクティブなSnowflake接続をdbtプロファイルに自動的に注入します — 手動設定は不要です。

> 期待される出力：71テストがパス、1つの警告（`source_not_null_raw_orders_total_amount`テストがData Quality演習で注入した200のNULLを検出 — これは設計通りの動作です）。

### 結果の探索

> 「顧客生涯価値セグメントを見せてください — 各価値ティアに何人の顧客がいますか？」

<!-- ------------------------ -->
## Gen2 Warehouse：Optima Indexing

[Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-gen2)はOptima Indexingを導入します — 明示的なクラスタリングキーなしにクエリ時にパーティションをプルーニングする自動インデックスレイヤーです。Gen2ウェアハウスはクエリパターンから学習し、ポイントルックアップやフィルタスキャンを高速化する内部インデックスを構築します。

Optima Indexingの動作を実証します：

CoCoにプロンプト：

> 「Gen2ウェアハウスでcustomer_id 5000のポイントルックアップを実行してください」

Snowsightでクエリプロファイルを開き、パーティションプルーニングを確認してください — 明示的なクラスタリングキーがないにもかかわらず、スキャンされるパーティションはごく一部です。これがGen2のOptima Indexingの動作です。

<!-- ------------------------ -->
## Interactive Tables

[Interactive Tables](https://docs.snowflake.com/en/user-guide/interactive)は、低レイテンシ・高並行性のポイントルックアップ専用に構築されています。等価述語に最適化されたクラスタリングで事前計算結果を維持し、ダッシュボードフィルターやフルテーブルスキャンが必要なアプリケーションクエリにサブ秒のレスポンス時間を提供します。

### ポイントルックアップ

Snowsightでクエリを実行し、サブ秒のレイテンシを観察します：

```sql
USE WAREHOUSE hol_interactive_wh;
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- 顧客IDによるポイントルックアップ
SELECT * FROM dash_automated_intelligence_db.interactive.customer_order_analytics
WHERE customer_id = 1;

-- 注文IDによるポイントルックアップ
-- 実行: SELECT order_id FROM dash_automated_intelligence_db.interactive.order_lookup LIMIT 5; でUUIDを取得
SELECT * FROM dash_automated_intelligence_db.interactive.order_lookup
WHERE order_id = '<any-order-uuid>';
```

### 並行負荷テスト

CoCoにプロンプト：

> 「interactive/load_test.pyでInteractive Tablesの負荷テストを実行してください」

200並行セッション（合計1000クエリ）をInteractiveとStandardの両方のウェアハウスに対して実行し、P50/P90/P99レイテンシを比較します。Interactiveウェアハウスで顕著に低いレイテンシと高いスループットが見られるはずです。

ウォームキャッシュの効果を観察するため、負荷テストをもう一度実行してみてください。結果はアカウント、リージョン、データスケールによって異なる場合があります。

<!-- ------------------------ -->
## CoCoカスタムスキル

[CoCoカスタムスキル](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility#skills)を使用すると、繰り返し可能なワークフローを名前付きコマンドにパッケージ化し、チームメンバーが呼び出せるようにできます。スキルはMarkdownファイル（`.cortex/skills/<name>/SKILL.md`）で、トリガー、パラメータ、CoCoがスキル起動時に従うステップバイステップの指示を定義します。

テーブルプロファイリングを自動化する再利用可能なスキルを作成します：

CoCoにプロンプト：

> 「テーブル名を受け取り、行数をカウントし、NULL列をチェックし、ユニーク値数を表示し、潜在的なデータ品質問題をフラグする'profile-table'というカスタムCoCoスキルを作成してください」

CoCoが`.cortex/skills/profile-table/SKILL.md`にスキル定義、トリガー、ステップバイステップの指示を作成します。

> 注意：スキル作成後、新しいスキルを有効にするにはCoCoセッションを再起動してください。CLI：`/quit`を入力してから`cortex`。Desktop：サイドバーから新しいセッションを開きます。

### テスト

> 「$profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS」

チームが再利用可能なワークフローを共有可能なCoCoスキルとしてパッケージ化する方法を実証しています。

<!-- ------------------------ -->
## Snowflake CoWork

[Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)は、質問を適切なデータソースにルーティングするマルチツールAIオーケストレーターです。[Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)（[セマンティックビュー](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)を介したtext-to-SQL）と[Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)（非構造化データに対するベクトル＋キーワード検索）を組み合わせ、単一の会話インターフェースから「何が起きたか」と「なぜ」の両方に回答します。

### エージェントの作成

CoCoにプロンプト：

> 「snowflake-cowork/create_agent.sqlを実行してBusiness Insights Agentを作成してください」

### エージェントルーティングのテスト

SnowsightでSnowflake CoWorkインターフェースを開きます：AI & ML → CoWork に移動（またはグローバル検索バーで「CoWork」を検索）。`BUSINESS_INSIGHTS_AGENT`エージェントを選択します。各質問を試して、異なるツールルーティングを実証します：

| 質問 | ルーティング先 |
|------|------------|
| 「2025年6月から9月の月次収益トレンドを見せてください」 | Cortex Analyst (text-to-SQL) |
| 「どの月が最も収益が低く、その時期の顧客レビューは何と言っていますか？」 | Cortex Analyst + Agentic Search |
| 「サイズ間違いに言及しているレビューで評価3未満のものを見つけてください」 | Agentic Search (フィルタ付き) |
| 「なぜ顧客がスキーブーツを返品しているのですか？」 | Agentic Search (レビュー＋チケット) |
| 「州別の総収益と顧客数は？」 | Cortex Analyst (text-to-SQL) |
| 「サポートチケットの上位苦情テーマは何ですか？」 | Agentic Search (フィルタ + AI_AGG) |
| 「サイズの問題に言及しているレビューは何件で、最も影響を受けている製品は？」 | Agentic Search (検索＋ブレークダウン) |

これがクライマックスです — エージェントが構造化データ（text-to-SQL）と非構造化データ（Cortex Search）にまたがってルーティングし、「何が起きたか」と「なぜ」に回答します。

<!-- ------------------------ -->
## セキュリティとガバナンス

[Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)は宣言的に行レベルセキュリティを施行します — どの行がどのロールに表示されるかを決定するブール式を定義すると、Snowflakeがすべてのクエリ（AIエージェントが生成したものを含む）に透過的に適用します。アプリケーションコードの変更は不要です。

Row Access PolicyとWEST_COAST_MANAGERロールは`setup.sql`で作成済みです。ロールに基づいて行レベルセキュリティがデータを透過的にフィルタリングする方法を実証します：

ACCOUNTADMIN（フルアクセス）として：

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE HOL_WH;
SELECT c.state, SUM(o.total_amount) AS total_revenue, COUNT(DISTINCT c.customer_id) AS customer_count
FROM dash_automated_intelligence_db.raw.orders o
JOIN dash_automated_intelligence_db.raw.customers c ON o.customer_id = c.customer_id
GROUP BY c.state ORDER BY total_revenue DESC;
```

結果：全10州が表示されます。

WEST_COAST_MANAGER（制限付き）として：

```sql
USE ROLE WEST_COAST_MANAGER;
USE WAREHOUSE HOL_WH;
SELECT c.state, SUM(o.total_amount) AS total_revenue, COUNT(DISTINCT c.customer_id) AS customer_count
FROM dash_automated_intelligence_db.raw.orders o
JOIN dash_automated_intelligence_db.raw.customers c ON o.customer_id = c.customer_id
GROUP BY c.state ORDER BY total_revenue DESC;
```

結果：CA、OR、WAのみが表示されます — Row Access Policyが透過的にデータをフィルタリングします。

重要なポイント：同じクエリ、同じテーブル — 誰が質問しているかによって異なる結果。行レベルセキュリティは、アプリケーションロジックを変更せずにデータ境界を施行します。

### CoWorkを通じた検証

Snowsightで WEST_COAST_MANAGER ロールに切り替え、CoWorkを開いてエージェントに質問します：

> 「州別の総収益と顧客数は？」

エージェントはCA、OR、WAのみの結果を返します — Row Access PolicyはAI生成SQLを通じても透過的にデータをフィルタリングします。

<!-- ------------------------ -->
## Streamlitダッシュボード

[Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)を使用すると、Snowflakeアカウント内で直接インタラクティブなデータアプリケーションを構築・デプロイできます — 外部インフラは不要です。アプリはSnowflake内で安全に実行され、データへのネイティブアクセスと同じロールベースのアクセス制御が適用されます。

> 前提条件：dbtモデルが先にビルドされている必要があります（dbtアナリティクスセクション参照）。ダッシュボードは`DBT_ANALYTICS`と`DBT_STAGING`テーブルをクエリします。

CoCoにプロンプト：

> 「StreamlitダッシュボードをSnowflakeにデプロイしてください」

CoCoが`streamlit-dashboard/`ディレクトリから`snow streamlit deploy`を実行します。デプロイ後、SnowsightでアプリURLを開いて探索します：

- サマリー — 収益KPI、注文トレンド、顧客数
- 顧客＆製品アナリティクス — 生涯価値セグメント、製品パフォーマンス
- パイプラインヘルス — Dynamic Tablesリフレッシュステータス、データ鮮度監視

<!-- ------------------------ -->
## エージェント評価

[エージェント評価](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#evaluating-agents)を使用すると、グラウンドトゥルースデータセットとLLM-as-judgeスコアリングでエージェント品質を測定できます。入力クエリと期待される回答を定義し、Snowflakeが各質問に対してエージェントを実行し、回答の正確性（レスポンスがグラウンドトゥルースと一致するか？）と論理的一貫性（推論ステップが内部的に一貫しているか？）でスコアリングします。

評価データセット（7問＋グラウンドトゥルース）は`setup.sql`で作成済みです。Snowsightで評価を実行します：

### Snowsight UIで実行

1. Snowsightで ACCOUNTADMINロールに切り替え（左上のロールセレクター）
2. AI and ML > Agents > BUSINESS_INSIGHTS_AGENT > Evaluationsタブに移動
3. 「New evaluation run」をクリック、名前を付け（例：`hol-eval-run-1`）、「Next」をクリック
4. 「Create new dataset from table」を選択
5. Source tableで、Database and schemaを`DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC`に設定し、`AGENT_EVALUATION_DATA`を選択
6. New dataset locationは`DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC`のまま
7. Dataset name：`hol_eval_dataset`
8. 「Next」をクリック
9. Define metricsで、Input query = `INPUT_QUERY`を確認
10. Answer Correctnessをオンにし、Expected answer = `GROUND_TRUTH`を設定
11. Logical Consistencyをオンに
12. 「Create」をクリック — 評価が自動的に開始されます（約3分）

### 結果の解釈

- Answer Correctness — エージェントのレスポンスがグラウンドトゥルースと一致したか？質問ごとに0-1でスコアリング。
- Logical Consistency — プランニングステップ、ツール呼び出し、レスポンスが内部的に一貫しているか？（参照不要）
- 質問ごとのドリルダウン — 任意の行を選択して完全なスレッドを表示：プランニング、ツール呼び出し、レスポンス生成。

### スコアの改善（応用）

論理的一貫性で低スコアの質問がある場合：

1. 低スコアの行をクリックし、Thread detailsを表示
2. Planningステップでのツール選択に関する曖昧な推論を探す
3. エージェントの指示をより明確に更新
4. エージェントを再作成し、評価を再実行

<!-- ------------------------ -->
## MCPサーバー

[Snowflake MCPサーバー](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#managed-mcp-servers)は、Cortex Agents、セマンティックビュー、Search Servicesをオープンなモデルコンテキストプロトコル（MCP）で発見可能なツールとして公開します。MCP互換クライアント（CoCo CLI、Claude Desktop、カスタムアプリ）がサーバーエンドポイントに接続し、プログラム的にツールを呼び出せます — SnowflakeのAIスタックを再利用可能なサービスレイヤーにします。

Business Insights AgentをマネージドMCPサーバーとして公開します：

CoCoにプロンプト：

> 「Business Insights Agent、セマンティックビュー、顧客フィードバック検索をツールとして公開するSnowflakeマネージドMCPサーバーを作成してください」

CoCoがMCPサーバーを作成します：

> 注意：CoCoはプロンプトに基づいてツール名（`revenue-analytics`、`customer-feedback-search`など）を生成します。名前は異なる場合があります — 重要なのは`type`と`identifier`が正しいオブジェクトを指していることです。

```sql
CREATE MCP SERVER business_insights_mcp
  FROM SPECIFICATION $$
    tools:
      - name: "business-insights-agent"
        type: "CORTEX_AGENT_RUN"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC.BUSINESS_INSIGHTS_AGENT"
        description: "構造化データと顧客フィードバックを使用してビジネスの質問に回答するAIエージェント"
        title: "Business Insights Agent"

      - name: "revenue-analytics"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC.BUSINESS_ANALYTICS_SEMANTIC"
        description: "収益、注文、顧客、製品メトリクスのText-to-SQL"
        title: "Revenue Analytics"

      - name: "customer-feedback-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.RAW.CUSTOMER_FEEDBACK_SEARCH"
        description: "製品レビューとサポートチケットの検索"
        title: "Customer Feedback Search"
  $$;
```

### CoCoから接続

```
cortex mcp add business-insights https://<account_url>/api/v2/databases/DASH_AUTOMATED_INTELLIGENCE_DB/schemas/SEMANTIC/mcp-servers/BUSINESS-INSIGHTS-MCP --type http
```

> Desktop：CoCo DesktopでMCPサーバーを追加するには、Settings → MCPに移動し、上記のエンドポイントURLで新しいHTTPサーバーを追加します。またはチャットで`/mcp`と入力します。

これでMCP互換クライアント（CoCo、Claude Desktop、カスタムアプリ）が標準MCPプロトコルでこれらのツールを発見・呼び出しできます。

<!-- ------------------------ -->
## オプション：Iceberg V3機能

> 注意：このセクションはオプションです。CoCo生成SQLを使用してIceberg V3機能（削除ベクトル、デフォルト値）を実証します。他のセクションはこのセクションに依存していません。

> 注意：Iceberg V3機能は新しいAPIのため、CoCoが正しいSQLを生成するまでに数回の試行が必要な場合があります。「error executing SQL」が表示されたら、CoCoに再試行させてください — 自己修正して最終的に動作します。

### マネージドIcebergテーブルの作成

CoCoにプロンプト：

> 「RAW.ORDERSから年月でクラスタリングしたマネージドIcebergテーブルを作成し、クエリしてパーティションプルーニングを見せてください」

CoCoが`CATALOG='SNOWFLAKE'`（外部ボリューム不要）でテーブルを作成し、フィルタクエリでパーティションプルーニングを実証します。

### V3を探索：削除ベクトル

> 「RAW.ORDERSからIceberg V3テーブル（ICEBERG_VERSION=3）をmerge-on-read有効で作成し、1000行を挿入してから10行を更新して削除ベクトルを実証してください」

CoCoが`ENABLE_ICEBERG_MERGE_ON_READ = TRUE`でV3テーブルを作成し、データを挿入し、完全なファイル書き換えの代わりに削除ベクトルを使用するUPDATEを実行します。

### V3を探索：デフォルト値

> 「V3テーブルにデフォルト値'STANDARD'で新しい列'priority'を追加し、バックフィルなしで既存の行がデフォルトを取得することを見せてください」

データファイルを書き換えずにV3スキーマエボリューションを実証します。

<!-- ------------------------ -->
## オプション：ストリーミング取り込み

> 注意：このセクションはオプションです。`setup.sql`スクリプトは既に5,000万注文すべてを直接ロードしています。このセクションでは、Snowpipe Streaming Python SDKを使用して本番環境でデータをストリーミングする方法を実証します。

### RSA鍵ペアの生成

Snowpipe Streaming認証用の鍵を生成します：

```bash
# 秘密鍵の生成（暗号化なしPEM）
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# 公開鍵の生成
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# 公開鍵をSnowflakeユーザーにアップロード（<your-username>を置き換え）
snow sql -q "ALTER USER <your-username> SET RSA_PUBLIC_KEY='$(grep -v -- '-----' rsa_key.pub | tr -d '\n')'" -c hol

# 確認
snow sql -q "DESC USER <your-username>" -c hol | grep RSA_PUBLIC_KEY_FP
```

### データのストリーミング

```bash
cd snowpipe-streaming-python
pip install -r requirements.txt

# プロファイルのコピーと設定
cp profile.json.template profile.json
```

`profile.json`を編集し、`account`、`user`、`private_key`（rsa_key.p8の内容）、`role`を設定します。

```bash
# 10,000注文をストリーミング
python src/automated_intelligence_streaming.py 10000
```

### データの着地確認

```sql
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.orders_staging;
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.order_items_staging;
```

ステージングに10,000注文と約50,000注文アイテムが見られるはずです。

### 本番へのマージ

CoCoを使用してストリームデータをマージします：

> 「Gen2ウェアハウスに切り替え、ステージングの行数を確認してから、RAWにマージして結果を見せてください」

<!-- ------------------------ -->
## まとめとリソース

おめでとうございます！ストリーミング取り込みから会話型AI、MCPサーバー公開まで、Snowflake上の完全なAI搭載リテール分析プラットフォームの構築に成功しました。

### 学んだこと

- Snowpipe StreamingとGen2 Warehousesによるリアルタイムデータのストリーミングとマージ
- Dynamic Tablesによるインクリメンタル変換パイプラインの構築
- Interactive Tablesによるサブ秒ポイントルックアップのサービング
- 削除ベクトルとデフォルト値を持つIceberg V3テーブルの作成とクエリ
- Data Metric Functionsによるデータ品質ギャップの監視と修正
- Snowflake上のdbt分析モデルの構築
- 繰り返し可能なワークフロー用のカスタムCoCoスキルの作成
- 構造化データ（Analyst）と非構造化データ（Search）にまたがるCortex Agentの構築
- グラウンドトゥルースデータセットによるエージェント品質の評価
- AIエージェントを通じた透過的な行レベルセキュリティの実装
- マネージドMCPサーバーとしてのAI機能の公開

### 関連リソース

ドキュメント：

- [Snowpipe Streaming SDK](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Interactive Tables](https://docs.snowflake.com/en/user-guide/interactive)
- [Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-gen2)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Semantic Views](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Data Metric Functions](https://docs.snowflake.com/en/user-guide/data-quality-intro)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Snowflake CoCo](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
