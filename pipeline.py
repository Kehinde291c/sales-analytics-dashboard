"""
Northwind Commerce - Sales Analytics Pipeline
================================================
Fetches the real UCI Online Retail dataset (CC BY 4.0), cleans it,
runs the analysis in both SQL (SQLite) and pandas, and exports a
single dashboard_data.json that the front end reads.

Run:  python pipeline.py
Output: cleaned_retail.csv, retail.db, dashboard_data.json

Dataset: Chen, D. (2015). Online Retail. UCI Machine Learning Repository.
         https://doi.org/10.24432/C5BW33
"""

import json
import sqlite3
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent


# ---------------------------------------------------------------------------
# 1. EXTRACT — pull the real dataset
# ---------------------------------------------------------------------------
def load_raw() -> pd.DataFrame:
    print("[1/5] Loading dataset...")
    # Primary path: official UCI package
    try:
        from ucimlrepo import fetch_ucirepo
        ds = fetch_ucirepo(id=352)
        df = ds.data.features.copy()
        print(f"      pulled {len(df):,} rows from UCI repository")
        return df
    except Exception as e:
        print(f"      ucimlrepo unavailable ({e})")

    # Fallback: a local copy if you've downloaded the Excel/CSV from Kaggle
    # https://www.kaggle.com/datasets/jihyeseo/online-retail-data-set-from-uci-ml-repo
    for fname in ("online_retail.xlsx", "Online Retail.xlsx", "online_retail.csv"):
        p = OUT / fname
        if p.exists():
            print(f"      reading local file {fname}")
            return pd.read_excel(p) if p.suffix == ".xlsx" else pd.read_csv(p)

    raise SystemExit(
        "Could not load data. Install ucimlrepo (pip install ucimlrepo) "
        "or drop the Kaggle Excel file next to this script."
    )


# ---------------------------------------------------------------------------
# 2. TRANSFORM / CLEAN — this is the part interviewers ask about
# ---------------------------------------------------------------------------
def clean(df: pd.DataFrame) -> pd.DataFrame:
    print("[2/5] Cleaning...")
    n0 = len(df)

    # normalize column names (the dataset ships with a few variants)
    df.columns = [c.strip() for c in df.columns]
    rename = {
        "InvoiceNo": "invoice", "Invoice": "invoice",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price", "Price": "unit_price",
        "CustomerID": "customer_id", "Customer ID": "customer_id",
        "Country": "country",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # cancellations: invoices starting with 'C' are returns -> drop for revenue view
    df["is_cancel"] = df["invoice"].astype(str).str.startswith("C")

    # data quality filters
    df = df[~df["is_cancel"]]                       # remove cancellations
    df = df[df["quantity"] > 0]                     # no negative/zero qty
    df = df[df["unit_price"] > 0]                   # no free / error rows
    df = df.dropna(subset=["customer_id"])          # need a customer to analyze
    df = df.dropna(subset=["invoice_date"])
    df = df.drop_duplicates()

    # derived field
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["customer_id"] = df["customer_id"].astype(int)
    df["year"] = df["invoice_date"].dt.year
    df["month"] = df["invoice_date"].dt.month

    print(f"      {n0:,} -> {len(df):,} rows after cleaning "
          f"({(1 - len(df)/n0)*100:.1f}% removed)")
    return df


# ---------------------------------------------------------------------------
# 3. LOAD — push to SQLite so we can run real SQL
# ---------------------------------------------------------------------------
def to_sqlite(df: pd.DataFrame) -> sqlite3.Connection:
    print("[3/5] Loading into SQLite...")
    conn = sqlite3.connect(OUT / "retail.db")
    df.to_sql("orders", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON orders(invoice_date)")
    return conn


# ---------------------------------------------------------------------------
# 4. ANALYZE — answer real business questions with SQL
# ---------------------------------------------------------------------------
def analyze(conn: sqlite3.Connection) -> dict:
    print("[4/5] Running analysis queries...")
    q = lambda sql: pd.read_sql_query(sql, conn)

    # --- KPIs ---
    kpi = q("""
        SELECT
            ROUND(SUM(revenue))                      AS net_revenue,
            COUNT(DISTINCT invoice)                  AS orders,
            ROUND(SUM(revenue)*1.0/COUNT(DISTINCT invoice), 2) AS aov,
            COUNT(DISTINCT customer_id)              AS customers
        FROM orders
    """).iloc[0].to_dict()

    # --- monthly revenue trend ---
    trend = q("""
        SELECT year, month, ROUND(SUM(revenue)) AS revenue
        FROM orders GROUP BY year, month ORDER BY year, month
    """)

    # --- top products ---
    top = q("""
        SELECT description AS product,
               SUM(quantity)        AS units,
               ROUND(SUM(revenue))  AS revenue
        FROM orders
        GROUP BY description
        ORDER BY revenue DESC
        LIMIT 10
    """)

    # --- revenue by country (top markets) ---
    countries = q("""
        SELECT country, ROUND(SUM(revenue)) AS revenue
        FROM orders GROUP BY country ORDER BY revenue DESC LIMIT 8
    """)

    # --- customer segmentation via RFM-lite (revenue tiers) ---
    seg = q("""
        WITH c AS (
            SELECT customer_id, SUM(revenue) AS spend
            FROM orders GROUP BY customer_id
        ),
        ranked AS (SELECT spend, NTILE(4) OVER (ORDER BY spend DESC) AS tier FROM c)
        SELECT
            CASE tier WHEN 1 THEN 'VIP' WHEN 2 THEN 'Loyal'
                      WHEN 3 THEN 'Occasional' ELSE 'New' END AS segment,
            ROUND(SUM(spend)) AS revenue
        FROM ranked GROUP BY tier ORDER BY tier
    """)

    return {
        "kpi": kpi,
        "trend": trend.to_dict(orient="records"),
        "top_products": top.to_dict(orient="records"),
        "countries": countries.to_dict(orient="records"),
        "segments": seg.to_dict(orient="records"),
        "generated_from": "UCI Online Retail (real UK e-commerce data, 2010-2011)",
    }


# ---------------------------------------------------------------------------
# 5. EXPORT
# ---------------------------------------------------------------------------
def main():
    df = clean(load_raw())
    df.to_csv(OUT / "cleaned_retail.csv", index=False)
    conn = to_sqlite(df)
    results = analyze(conn)
    print("[5/5] Writing dashboard_data.json...")
    (OUT / "dashboard_data.json").write_text(json.dumps(results, indent=2))
    print("\nDone. Outputs: cleaned_retail.csv, retail.db, dashboard_data.json")
    print(f"Net revenue: £{results['kpi']['net_revenue']:,.0f} | "
          f"Orders: {results['kpi']['orders']:,} | "
          f"Customers: {results['kpi']['customers']:,}")


if __name__ == "__main__":
    main()
