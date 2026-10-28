# Supply Chain Optimization and Inventory Forecasting System

A Python/FastAPI + MySQL + Streamlit application for descriptive demand analysis, supplier delivery tracking, threshold-based reorder recommendations, and baseline-evaluated forecasts. **No automatic purchasing.**

## Folder structure

```text
supply-chain-optimization/
├── app/
│   ├── __init__.py
│   ├── settings.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── analytics.py
│   └── main.py
├── scripts/
│   └── seed.py
├── tests/
│   └── test_analytics.py
├── dashboard.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Run locally

1. Install Python 3.11+ and MySQL 8. In MySQL Workbench or mysql CLI run:

   ```sql
   CREATE DATABASE supply_chain CHARACTER SET utf8mb4;
   ```

2. In a terminal inside the project folder:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```

   On macOS/Linux use `python3 -m venv .venv`, `source .venv/bin/activate`, and `cp .env.example .env`.

3. Edit `.env` to use your actual MySQL username/password. URL-encode reserved characters in passwords. For a quick local-only demo without MySQL, use `DATABASE_URL=sqlite:///./supply_chain.db`.

4. From the project root seed the database:

   ```bash
   python -m scripts.seed
   ```

5. Start the API (terminal 1):

   ```bash
   uvicorn app.main:app --reload
   ```

   Open http://127.0.0.1:8000/docs for interactive REST CRUD API documentation.

6. Start the dashboard (terminal 2, same virtual environment):

   ```bash
   streamlit run dashboard.py
   ```

   Open http://localhost:8501.

7. Run tests:

   ```bash
   pytest -q
   ```

## Assumptions and units

- Demand is in **units per calendar day**. A lookback of N days includes zero-demand days. The source of truth for demand is `demand_records`; stock movements are tracked separately. Do not duplicate sales when importing data.
- On-hand stock (units) = cumulative `in` movements minus cumulative `out` movements. Negative stock indicates a data or fulfillment issue; records are not automatically reconciled.
- Average daily demand = total demand units / number of calendar days in the lookback window.
- Lead time is a configurable product-level **calendar-day** assumption, not automatically overwritten by supplier history.
- Reorder point (units) = ceil(average demand [units/day] × lead time [days] + safety stock [units]).
- Stockout risk: on-hand stock <= reorder point; this is a **threshold flag**, not a probability.
- Excess risk: stock > max(reorder point, ceil(average demand × excess coverage days + safety stock)). This is a heuristic.
- Suggested order (units), only when flagged: max(0, ceil(average demand × (lead time + lookback days) + safety stock − on-hand stock)). This uses the lookback length as an illustrative replenishment coverage period, **not** an economic order quantity. Review before acting.
- Supplier on-time % = received orders with received_date <= expected_date / all received orders × 100. Pending/cancelled excluded. Actual lead time = received_date − order_date in calendar days. Empty sample returns null.
- Forecast: chronological 80% training / 20% holdout; compare constant historical-mean baseline against 7-day trailing moving average using MAE (units/day). The moving average uses actual observations available before each holdout prediction (one-step-ahead rolling evaluation). Ties select baseline. Forecast assumes a constant daily rate over the chosen horizon. Zero days are included. **No future demand information is used in predictions.**
- The forecast is descriptive decision support, not guaranteed accuracy. Holidays, promotions, seasonality, capacity, backorders, and incoming open purchase-order quantities are not modeled.
- `products.reorder_point` is a legacy/stored field; analytics calculates the current point from lookback and safety stock and returns both values. The stored value is not updated automatically.
- No supplier-product or PO-line mapping is included in this scope; purchase orders are tracked at supplier/header level and do not increase inventory automatically. Record actual receipts with stock `in` transactions.
- `unit_cost` is stored for future cost analysis; stock turnover is not computed because consistent opening/closing valuation and cost of goods sold are not in this MVP.
- The API has no authentication; run locally or add authentication before public deployment. `create_all` is a simple local bootstrap; production needs schema migrations.

## REST endpoints

Each of `/products`, `/suppliers`, `/purchase-orders`, `/stock-transactions`, `/demand-records` supports GET list, POST, GET by ID, PUT by ID, and DELETE by ID. Analysis: `/analytics/inventory?days=30&excess_days=60`, `/analytics/suppliers`, `/analytics/forecast/{product_id}?days=60&horizon=7`.

## Push to GitHub

Create a **new empty** repository in GitHub, then run from this folder:

```bash
git init
git add .
git commit -m "Initial supply chain optimization application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/supply-chain-optimization.git
git push -u origin main
```

Authenticate with Git Credential Manager or GitHub CLI as prompted; GitHub account passwords are not accepted as HTTPS Git passwords. `.env` is ignored and should never be committed. Confirm with `git status` and `git ls-files` before pushing.
