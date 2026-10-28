import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

API = os.getenv('API_URL', 'http://127.0.0.1:8000')
st.set_page_config(page_title='Supply Chain Intelligence', layout='wide')
st.title('Supply Chain Optimization & Inventory Forecasting')
st.caption('Advisory analytics only — purchase orders are never created automatically.')

def fetch(path):
    try:
        response = requests.get(API + path, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f'API unavailable: {exc}')
        st.stop()

def table(items):
    if items:
        st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
    else:
        st.info('No records yet. Add data through the API /docs page or seed script.')

page = st.sidebar.radio('Navigation', ['Overview', 'Inventory & Reorder', 'Demand Forecast', 'Suppliers', 'Records'])
if page == 'Overview':
    products = fetch('/products')
    risks = fetch('/analytics/inventory')
    suppliers = fetch('/suppliers')
    a,b,c,d = st.columns(4)
    a.metric('Products', len(products))
    b.metric('Suppliers', len(suppliers))
    c.metric('Stockout flags', sum(r['stockout_risk'] for r in risks))
    d.metric('Excess flags', sum(r['excess_risk'] for r in risks))
    table(risks)
elif page == 'Inventory & Reorder':
    days = st.slider('Demand lookback (days)', 14, 180, 30)
    excess = st.slider('Excess coverage threshold (days)', 15, 180, 60)
    rows = fetch(f'/analytics/inventory?days={days}&excess_days={excess}')
    table(rows)
    if rows:
        st.download_button('Download reorder report (CSV)', pd.DataFrame(rows).to_csv(index=False), 'reorder_report.csv', 'text/csv')
elif page == 'Demand Forecast':
    products = fetch('/products')
    if products:
        options = {f"{p['sku']} — {p['product_name']}": p['product_id'] for p in products}
        selected = st.selectbox('Product', list(options))
        days = st.slider('History days', 14, 180, 60)
        horizon = st.slider('Forecast days', 1, 30, 7)
        report = fetch(f'/analytics/forecast/{options[selected]}?days={days}&horizon={horizon}')
        st.write({k:v for k,v in report.items() if k != 'history'})
        history = pd.DataFrame(report['history'])
        history['date'] = pd.to_datetime(history['date'])
        fig, ax = plt.subplots(figsize=(10,4))
        ax.plot(history['date'], history['quantity'], label='Historical demand')
        ax.axhline(report['forecast_units_per_day'], linestyle='--', label='Forecast daily rate')
        ax.set_ylabel('Units / day')
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)
        st.download_button('Download demand history (CSV)', history.to_csv(index=False), 'demand_history.csv', 'text/csv')
    else:
        st.info('Create a product first.')
elif page == 'Suppliers':
    rows = fetch('/analytics/suppliers')
    table(rows)
    valid = [r for r in rows if r['on_time_rate_pct'] is not None]
    if valid:
        fig, ax = plt.subplots(figsize=(9,4))
        ax.bar([r['supplier_name'] for r in valid], [r['on_time_rate_pct'] for r in valid])
        ax.set_ylabel('On-time deliveries (%)')
        ax.set_ylim(0, 100)
        plt.xticks(rotation=20)
        st.pyplot(fig)
        plt.close(fig)
    if rows:
        st.download_button('Download supplier report (CSV)', pd.DataFrame(rows).to_csv(index=False), 'supplier_report.csv', 'text/csv')
else:
    for name in ['products', 'suppliers', 'purchase-orders', 'stock-transactions', 'demand-records']:
        st.subheader(name.replace('-', ' ').title())
        table(fetch('/' + name))
    st.info('Create, edit and delete records at http://127.0.0.1:8000/docs')
