
WITH MOCK_DATA AS (
    SELECT * FROM VALUES
        (100.00, 'US'),
        (200.00, 'CA'),
        (300.00, 'UK'),
        (400.00, 'DE')
    AS T(amount, country)
),
EXPECTED_DATA AS (
    SELECT
        8.00 AS expected_tax
    UNION ALL
    SELECT
        24.00 AS expected_tax
    UNION ALL
    SELECT
        60.00 AS expected_tax
    UNION ALL
    SELECT
        20.00 AS expected_tax
)
SELECT
    ${MY_DB}.${MY_SCHEMA}.CALCULATE_TAX(m.amount, m.country) AS calculated_tax
FROM MOCK_DATA m;
