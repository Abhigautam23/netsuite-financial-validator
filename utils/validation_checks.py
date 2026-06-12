"""
Validation Checks
Four targeted GL anomaly detectors for the Close Health Check tab.
Each function returns an empty DataFrame on error rather than raising.

Design notes
------------
* Duplicate detection fingerprints WHOLE transactions (all lines, sorted)
  rather than individual lines. Two genuinely separate same-day charges for
  the same amount are normal business; the same complete journal posted
  under two transaction IDs is a double-post.
* Accrual reversal detection compares credits accrued in period N against
  debits posted in period N+1, and never evaluates the final period in the
  file (its reversal window hasn't happened yet — flagging it would be a
  guaranteed false positive on every upload).
* Volume anomalies flag above-mean spikes only. Quiet periods are not a
  duplicate-batch-import signal.
"""

import pandas as pd

# Reversal in N+1 must cover at least this share of the amount accrued in N.
ACCRUAL_REVERSAL_TOLERANCE = 0.5


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
    deviations ABOVE the dataset mean — a signal for duplicate batch imports.
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
                    COUNT(DISTINCT transaction_id) AS txn_count,
                    ROUND(SUM(debit + credit), 2)  AS total_volume
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
                   (p.txn_count    - s.mean_count)  / NULLIF(s.sd_count,  0) > 2
                OR (p.total_volume - s.mean_volume) / NULLIF(s.sd_volume, 0) > 2
            ORDER BY GREATEST(
                COALESCE(count_z_score,  0),
                COALESCE(volume_z_score, 0)
            ) DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()


def check_duplicate_postings(con):
    """
    Complete transactions whose full line set (account, subsidiary, debit,
    credit for every line) is identical to another transaction posted on the
    same date under a different transaction ID — the signature of a
    double-posted journal or a batch imported twice.

    Fingerprinting whole transactions avoids the classic false positive of
    two legitimate, separate same-day charges that happen to share an
    account and amount.
    """
    try:
        return con.execute("""
            WITH txn_fingerprints AS (
                SELECT
                    transaction_id,
                    MIN(date) AS date,
                    STRING_AGG(
                        account_name || '|' || subsidiary || '|'
                            || CAST(debit AS VARCHAR) || '|' || CAST(credit AS VARCHAR),
                        ';' ORDER BY account_name, debit, credit
                    )                                       AS fingerprint,
                    STRING_AGG(DISTINCT account_name, ', ' ORDER BY account_name)
                                                            AS account_name,
                    STRING_AGG(DISTINCT subsidiary, ', ' ORDER BY subsidiary)
                                                            AS subsidiary,
                    ROUND(SUM(debit), 2)                    AS debit,
                    ROUND(SUM(credit), 2)                   AS credit
                FROM gl_transactions
                GROUP BY transaction_id
            )
            SELECT
                date,
                account_name,
                subsidiary,
                debit,
                credit,
                COUNT(*)                                                 AS num_transactions,
                STRING_AGG(transaction_id, ', ' ORDER BY transaction_id) AS transaction_ids
            FROM txn_fingerprints
            GROUP BY date, fingerprint, account_name, subsidiary, debit, credit
            HAVING COUNT(*) > 1
            ORDER BY num_transactions DESC, debit DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()


def check_missing_accrual_reversals(con):
    """
    Accrual accounts where period N booked a net credit (an accrual) but
    period N+1 contains insufficient debits to reverse it.

    Rules applied to avoid false positives:
      * The final period in the file is never evaluated — its reversal
        window hasn't occurred yet.
      * The reversal must cover at least ACCRUAL_REVERSAL_TOLERANCE of the
        accrued amount; partial true-ups are accepted.
    """
    try:
        return con.execute(f"""
            WITH period_order AS (
                SELECT
                    period,
                    ROW_NUMBER() OVER (ORDER BY MIN(date)) AS period_seq
                FROM gl_transactions
                GROUP BY period
            ),
            period_next AS (
                SELECT p1.period AS period, p2.period AS next_period
                FROM period_order p1
                LEFT JOIN period_order p2 ON p2.period_seq = p1.period_seq + 1
            ),
            accrual_activity AS (
                SELECT
                    period,
                    account_name,
                    ROUND(SUM(credit), 2)              AS total_credits,
                    ROUND(SUM(debit),  2)              AS total_debits,
                    ROUND(SUM(debit) - SUM(credit), 2) AS net_amount
                FROM gl_transactions
                WHERE account_name ILIKE '%accru%'
                GROUP BY period, account_name
            )
            SELECT
                a.period,
                a.account_name,
                a.total_credits                    AS total_credits,
                COALESCE(n.total_debits, 0.0)      AS total_debits,
                ROUND(COALESCE(n.total_debits, 0.0) - a.total_credits, 2)
                                                   AS net_amount
            FROM accrual_activity a
            JOIN period_next pn ON a.period = pn.period
            LEFT JOIN accrual_activity n
                ON  n.account_name = a.account_name
                AND n.period       = pn.next_period
            WHERE pn.next_period IS NOT NULL
              AND a.total_credits > 0.01
              AND COALESCE(n.total_debits, 0.0)
                    < a.total_credits * {ACCRUAL_REVERSAL_TOLERANCE}
            ORDER BY a.total_credits DESC
        """).fetchdf()
    except Exception:
        return pd.DataFrame()