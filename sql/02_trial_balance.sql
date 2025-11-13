-- 02_trial_balance.sql
-- Trial Balance: Shows all accounts with their balances grouped by subsidiary
-- Join path: transactionaccountingline → account, transactionaccountingline → transactionline → subsidiary

WITH joined AS (
  SELECT
    s.name             AS subsidiary_name,
    a.fullname         AS account_name,
    a.accttype         AS account_type,
    tal.amount         AS amount
  FROM transactionaccountingline tal
  LEFT JOIN account a
    ON tal.account = a.id
  LEFT JOIN transactionline l
    ON tal.transaction = l.transaction
  LEFT JOIN subsidiary s
    ON l.subsidiary = s.id
  WHERE s.name IS NOT NULL
)
SELECT
  subsidiary_name,
  account_name,
  account_type,
  ROUND(SUM(amount), 2) AS total_amount
FROM joined
GROUP BY 1, 2, 3
ORDER BY subsidiary_name, account_name;




