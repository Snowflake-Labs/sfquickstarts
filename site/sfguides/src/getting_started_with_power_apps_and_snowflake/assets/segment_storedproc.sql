CREATE OR REPLACE PROCEDURE segmentize(Table_Name STRING, Target_Name String)
RETURNS VARCHAR NOT NULL
LANGUAGE SQL
AS
$$
BEGIN
    CREATE OR REPLACE VIEW IDENTIFIER(:Target_Name)  AS SELECT a.*, (KMODES_MODEL_9_9_2024!predict(a.* )['output_feature_0'])::number as prediction from IDENTIFIER(:table_name) a;
    RETURN 'VIEW CREATED';
END;
$$;

