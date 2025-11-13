-- 01_create_tables.sql
-- Creates tables from uploaded CSV files in DuckDB
-- These placeholders (__ACCOUNT__, etc.) will be replaced at runtime by Streamlit

CREATE OR REPLACE TABLE account AS 
SELECT * FROM read_csv_auto('__ACCOUNT__');

CREATE OR REPLACE TABLE subsidiary AS 
SELECT * FROM read_csv_auto('__SUBSIDIARY__');

CREATE OR REPLACE TABLE transaction_header AS
SELECT * FROM read_csv_auto('__TRANSACTION__');

CREATE OR REPLACE TABLE transactionline AS
SELECT * FROM read_csv_auto('__TRANSACTIONLINE__');

CREATE OR REPLACE TABLE transactionaccountingline AS
SELECT * FROM read_csv_auto('__TRANSACTIONACCOUNTINGLINE__');

