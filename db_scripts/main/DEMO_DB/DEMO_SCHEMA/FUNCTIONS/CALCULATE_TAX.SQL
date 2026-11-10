
CREATE OR REPLACE FUNCTION ${MY_DB}.${MY_SCHEMA}.CALCULATE_TAX(amount NUMBER, country VARCHAR)
RETURNS NUMBER
LANGUAGE SQL
AS
$$
  CASE
    WHEN country = 'US' THEN amount * 0.08
    WHEN country = 'CA' THEN amount * 0.12
    WHEN country = 'UK' THEN amount * 0.20
    ELSE amount * 0.05
  END
$$;
