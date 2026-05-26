USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 1. fn_FormatPhoneNumber — STUFF, PATINDEX
-- --------------------------------------------------------------------------
CREATE FUNCTION TastyBytes.fn_FormatPhoneNumber
(
    @RawPhone VARCHAR(20)
)
RETURNS VARCHAR(20)
AS
BEGIN
    DECLARE @CleanPhone VARCHAR(20);
    DECLARE @Formatted VARCHAR(20);

    -- Strip non-numeric characters
    SET @CleanPhone = @RawPhone;
    WHILE PATINDEX('%[^0-9]%', @CleanPhone) > 0
        SET @CleanPhone = STUFF(@CleanPhone, PATINDEX('%[^0-9]%', @CleanPhone), 1, '');

    IF LEN(@CleanPhone) = 10
        SET @Formatted = '(' + LEFT(@CleanPhone, 3) + ') ' +
                          SUBSTRING(@CleanPhone, 4, 3) + '-' +
                          RIGHT(@CleanPhone, 4);
    ELSE IF LEN(@CleanPhone) = 11
        SET @Formatted = '+' + LEFT(@CleanPhone, 1) + ' (' +
                          SUBSTRING(@CleanPhone, 2, 3) + ') ' +
                          SUBSTRING(@CleanPhone, 5, 3) + '-' +
                          RIGHT(@CleanPhone, 4);
    ELSE
        SET @Formatted = @CleanPhone;

    RETURN @Formatted;
END