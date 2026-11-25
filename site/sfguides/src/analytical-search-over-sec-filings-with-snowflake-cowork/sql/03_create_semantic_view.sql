USE ROLE ACCOUNTADMIN;
USE DATABASE SEC_FILINGS;
USE SCHEMA FILING_DATA;
USE WAREHOUSE FILING_WH;

CREATE OR REPLACE SEMANTIC VIEW SEC_FILING_ANALYTICS
  TABLES (
    signals AS FILING_SIGNALS
      PRIMARY KEY (SIGNAL_ID)
      WITH SYNONYMS = ('investment signals', 'filing signals', 'EDGAR signals', 'SEC filings')
      COMMENT = 'AI-extracted investment signals from SEC EDGAR filings.',
    meta AS FILING_INDEX
      PRIMARY KEY (ACCESSION_NO)
      WITH SYNONYMS = ('filing metadata', 'EDGAR index', 'filing registry')
      COMMENT = 'SEC EDGAR filing metadata: accession numbers, CIKs, filing URLs, dates'
  )
  RELATIONSHIPS (
    signals_to_meta AS signals(ACCESSION_NO) REFERENCES meta(ACCESSION_NO)
  )
  FACTS (
    signals.accession_no AS signals.ACCESSION_NO
      WITH SYNONYMS = ('accession number', 'filing id')
      COMMENT = 'EDGAR accession number uniquely identifying the filing',
    signals.revenue AS signals.REVENUE
      WITH SYNONYMS = ('total revenue', 'sales', 'top line')
      COMMENT = 'Revenue in millions USD. NULL if not extractable.',
    signals.net_income AS signals.NET_INCOME
      WITH SYNONYMS = ('net income', 'profit', 'bottom line')
      COMMENT = 'Net income figure extracted from filing.',
    signals.eps AS signals.EPS
      WITH SYNONYMS = ('earnings per share', 'diluted EPS')
      COMMENT = 'Normalized EPS value.',
    signals.yoy_change AS signals.YOY_CHANGE
      WITH SYNONYMS = ('year over year', 'YoY growth', 'growth rate')
      COMMENT = 'Year-over-year change percentage.',
    signals.forward_guidance AS signals.FORWARD_GUIDANCE
      WITH SYNONYMS = ('guidance', 'outlook', 'forecast')
      COMMENT = 'Forward-looking financial guidance from MD&A.'
  )
  DIMENSIONS (
    signals.company_name AS signals.COMPANY_NAME
      WITH SYNONYMS = ('company', 'filer', 'issuer')
      COMMENT = 'Company that filed the SEC document',
    signals.ticker AS signals.TICKER
      WITH SYNONYMS = ('stock ticker', 'symbol')
      COMMENT = 'Stock ticker symbol. May be NULL for non-public filers.',
    signals.form_type AS signals.FORM_TYPE
      WITH SYNONYMS = ('filing type', 'SEC form')
      COMMENT = '10-K (annual), 10-Q (quarterly), 8-K (current report)',
    signals.event_type AS COALESCE(signals.EVENT_TYPE_NORMALIZED, signals.EVENT_TYPE)
      WITH SYNONYMS = ('event', 'signal type', 'event classification')
      COMMENT = 'AI-classified event type: Earnings, M&A, Leadership Change, Risk Disclosure, Guidance Update, Regulatory, Capital Markets, Bankruptcy, Annual Report, Quarterly Report, Current Report, Other.',
    signals.sentiment AS signals.SENTIMENT
      WITH SYNONYMS = ('tone', 'filing sentiment')
      COMMENT = 'AI-assessed sentiment: POSITIVE, NEGATIVE, NEUTRAL, MIXED.',
    signals.industry_sector AS COALESCE(signals.INDUSTRY_SECTOR, 'Other')
      WITH SYNONYMS = ('sector', 'industry')
      COMMENT = 'SEC Office-based industry sector: Technology, Life Sciences, Finance, Real Estate & Construction, Energy & Transportation, Manufacturing, Trade & Services, Other.',
    signals.industry_title AS signals.INDUSTRY_TITLE
      WITH SYNONYMS = ('specific industry', 'sub-sector')
      COMMENT = 'Specific SEC industry title.',
    signals.is_amendment AS signals.IS_AMENDMENT
      WITH SYNONYMS = ('amendment', 'restated')
      COMMENT = 'TRUE if this is an amended filing.',
    meta.cik AS meta.CIK
      WITH SYNONYMS = ('SEC CIK', 'central index key')
      COMMENT = 'SEC Central Index Key',
    signals.signal_date AS signals.SIGNAL_DATE
      WITH SYNONYMS = ('filing date', 'date filed', 'when filed')
      COMMENT = 'The date the SEC received the filing.',
    signals.period_of_report AS signals.PERIOD_OF_REPORT
      WITH SYNONYMS = ('fiscal period', 'report period', 'period end')
      COMMENT = 'Fiscal period end date the filing covers.'
  )
  METRICS (
    signals.filing_count AS COUNT(signals.SIGNAL_ID)
      WITH SYNONYMS = ('number of filings', 'total filings', 'how many filings')
      COMMENT = 'Total number of filings matching filters',
    signals.positive_signals AS COUNT(CASE WHEN signals.SENTIMENT = 'POSITIVE' THEN 1 END)
      WITH SYNONYMS = ('positive filings', 'bullish signals')
      COMMENT = 'Count of filings with positive sentiment',
    signals.negative_signals AS COUNT(CASE WHEN signals.SENTIMENT = 'NEGATIVE' THEN 1 END)
      WITH SYNONYMS = ('negative filings', 'bearish signals')
      COMMENT = 'Count of filings with negative sentiment',
    signals.ma_count AS COUNT(CASE WHEN signals.EVENT_TYPE = 'M&A' THEN 1 END)
      WITH SYNONYMS = ('merger filings', 'M&A events', 'deals')
      COMMENT = 'Count of merger and acquisition events',
    signals.leadership_change_count AS COUNT(CASE WHEN signals.EVENT_TYPE = 'Leadership Change' THEN 1 END)
      WITH SYNONYMS = ('leadership events', 'management changes')
      COMMENT = 'Count of leadership change events',
    signals.negative_sentiment_pct AS
      ROUND(100.0 * COUNT(CASE WHEN signals.SENTIMENT = 'NEGATIVE' THEN 1 END)
            / NULLIF(COUNT(signals.SIGNAL_ID), 0), 2)
      WITH SYNONYMS = ('negative rate', 'percent negative')
      COMMENT = 'Percentage of filings with negative sentiment (0-100 scale)'
  )
  COMMENT = 'Investment signal analytics over SEC EDGAR filing corpus.'
  AI_SQL_GENERATION 'This semantic view covers SEC EDGAR filings. SIGNAL_DATE is the authoritative filing timestamp. EVENT_TYPE and SENTIMENT are AI-extracted.';