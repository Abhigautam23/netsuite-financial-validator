"""
Validation Checks
Four targeted GL anomaly detectors for the Close Health Check tab.
Each function returns an empty DataFrame on error rather than raising.
"""

import pandas as pd


def check_period_balance_errors(con):
    """Periods where total debits != total credits (variance > $0.01)."""
    try:
        return con.execute("""
            SELECT
                period,
                ROUND(SUM(debit),  2)              AS total_debits,
                ROUND(SUM(credit), 2)              AS total_credits,
                ROUND(SUM(debit) - SUM(credit), 2) AS variance
            FROM gl_transactions
            GROUP BY period
            HAVING ABS(SUM(debit) - SUM(credit)) > 0.01
            ORDER BY ABS(SUM(debit) - SUM(credit)) DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()


def check_volume_anomalies(con):
    """
    Periods whose transaction count or posting volume is more than 2 standard
    deviations above the dataset mean — a signal for duplicate batch imports.
    Returns empty DataFrame when fewer than 3 periods exist (std undefined).
    """
    try:
        period_count = con.execute(
            "SELECT COUNT(DISTINCT period) FROM gl_transactions"
        ).fetchone()[0]
        if period_count < 3:
            return pd.DataFrame()
        return con.execute("""
            WITH period_counts AS (
                SELECT
                    period,
                    COUNT(DISTINCT transaction_id)     AS txn_count,
                    ROUND(SUM(debit + credit), 2)      AS total_volume
                FROM gl_transactions
                GROUP BY period
            ),
            stats AS (
                SELECT
                    AVG(txn_count)       AS mean_count,
                    STDDEV(txn_count)    AS sd_count,
                    AVG(total_volume)    AS mean_volume,
                    STDDEV(total_volume) AS sd_volume
                FROM period_counts
            )
            SELECT
                p.period,
                p.txn_count,
                p.total_volume,
                ROUND((p.txn_count    - s.mean_count)  / NULLIF(s.sd_count,  0), 2) AS count_z_score,
                ROUND((p.total_volume - s.mean_volume) / NULLIF(s.sd_volume, 0), 2) AS volume_z_score
            FROM period_counts p, stats s
            WHERE
                   ABS((p.txn_count    - s.mean_count)  / NULLIF(s.sd_count,  0)) > 2
                OR ABS((p.total_volume - s.mean_volume) / NULLIF(s.sd_volume, 0)) > 2
            ORDER BY ABS(count_z_score) DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()


def check_duplicate_postings(con):
    """
    Lines sharing the same (date, account_name, subsidiary, debit, credit) across
    two or more distinct transaction IDs — classic double-post signature.
    """
    try:
        return con.execute("""
            SELECT
                date,
                account_name,
                subsidiary,
                debit,
                credit,
                COUNT(DISTINCT transaction_id)                                    AS num_transactions,
                STRING_AGG(DISTINCT transaction_id, ', ' ORDER BY transaction_id) AS transaction_ids
            FROM gl_transactions
            WHERE debit > 0 OR credit > 0
            GROUP BY date, account_name, subsidiary, debit, credit
            HAVING COUNT(DISTINCT transaction_id) > 1
            ORDER BY num_transactions DESC, (debit + credit) DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()


def check_missing_accrual_reversals(con):
    """
    Accrual accounts with a net balance in period N but no offsetting entry in
    period N+1.  Standard practice requires month-end accruals to be reversed
    on the first working day of the following period.
    """
    try:
        return con.execute("""
            WITH accrual_net AS (
                SELECT
                    period,
                    account_name,
                    ROUND(SUM(debit) - SUM(credit), 2) AS net_amount
                FROM gl_transactions
                WHERE account_name ILIKE '%accru%'
                GROUP BY period, account_name
                HAVING ABS(SUM(debit) - SUM(credit)) > 0.01
            ),
            period_order AS (
                SELECT
                    period,
                    ROW_NUMBER() OVER (ORDER BY MIN(date)) AS period_seq
                FROM gl_transactions
                GROUP BY period
            ),
            period_next AS (
                -- Pre-compute each period's successor to avoid subqueries in JOIN
                SELECT p1.period AS period, p2.period AS next_period
                FROM period_order p1
                LEFT JOIN period_order p2 ON p2.period_seq = p1.period_seq + 1
            )
            SELECT
                a.period,
                a.account_name,
                a.net_amount
            FROM accrual_net a
            JOIN period_next pn ON a.period = pn.period
            LEFT JOIN accrual_net b
                ON  b.account_name = a.account_name
                AND b.period        = pn.next_period
                AND SIGN(b.net_amount) != SIGN(a.net_amount)
            WHERE b.account_name IS NULL
            ORDER BY a.period, a.account_name
        """).fetchdf()
    except Exception:
        return pd.DataFrame()
