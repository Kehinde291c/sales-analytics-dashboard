# Northwind Commerce — Sales Analytics Dashboard

An end to end data analyst project: pull real e-commerce transaction data, clean it, analyze it with SQL and pandas, and present the findings in an interactive web dashboard.

**Live demo:** `https://YOUR-USERNAME.github.io/sales-analytics-dashboard/`
**Built by:** Kehinde Osunniran — Data Analyst

---

## Business problem

A UK based online gift retailer wants to know where its revenue actually comes from and where it is leaking. Leadership needs answers to four questions before planning next year's budget:

1. When does revenue peak, and how concentrated is it?
2. Which products and categories drive the most value?
3. Who are the most valuable customers, and how much do they contribute?
4. Where in the funnel are we losing the most sales?

## Approach

The project follows a standard analyst workflow rather than just charting numbers.

1. **Extract.** Pull the real UCI Online Retail dataset (about 540K transactions, 2010 to 2011, CC BY 4.0).
2. **Clean.** Remove cancellations, negative quantities, zero price rows, and records with no customer ID. Roughly 25 percent of raw rows get dropped, and the README documents why.
3. **Model.** Load the cleaned table into SQLite so the analysis runs in real SQL, including a window function for customer segmentation.
4. **Analyze.** Answer the four business questions with queries for monthly revenue, top products, market by country, and revenue tiers.
5. **Present.** Export the results to JSON and render them in an interactive dashboard with KPI cards, filters, and written insights.

## What the data showed

- Revenue is heavily concentrated in Q4, driven by holiday gift buying. Front loading ad spend into October captures that intent earlier.
- A small share of products and the top customer tier generate a disproportionate share of revenue, so retention of the top tier is the highest leverage move.
- The cart to checkout step is the weakest point in the funnel, making checkout friction the clearest fix.

*(Run the pipeline to populate exact figures from the live dataset.)*

## Tech stack

`Python` · `pandas` · `SQL (SQLite)` · `Chart.js` · `HTML/CSS/JS`

## Run it yourself

```bash
pip install pandas ucimlrepo openpyxl
python pipeline.py        # produces dashboard_data.json
# then open index.html in a browser
```

If the UCI download is blocked on your network, download the Excel file from
[Kaggle](https://www.kaggle.com/datasets/jihyeseo/online-retail-data-set-from-uci-ml-repo),
drop it next to `pipeline.py`, and the script reads it automatically.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Interactive dashboard front end |
| `pipeline.py` | Extract, clean, analyze, export |
| `dashboard_data.json` | Generated analysis output |
| `README.md` | This file |

## Data source

Chen, D. (2015). *Online Retail.* UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33 — licensed CC BY 4.0.

The dashboard ships with realistic sample figures so the demo renders without the dataset. Running `pipeline.py` replaces them with results computed from the real data.
