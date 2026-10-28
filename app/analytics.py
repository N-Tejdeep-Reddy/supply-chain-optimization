from datetime import date, timedelta
from math import ceil
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Product, StockTransaction, DemandRecord, PurchaseOrder, Supplier

def daily_demand(db: Session, product_id: int, days: int = 30, as_of: date | None = None):
    as_of = as_of or date.today()
    start = as_of - timedelta(days=days - 1)
    rows = db.scalars(select(DemandRecord).where(DemandRecord.product_id == product_id, DemandRecord.demand_date >= start, DemandRecord.demand_date <= as_of)).all()
    series = pd.Series(0.0, index=pd.date_range(start, as_of), dtype=float)
    if rows:
        df = pd.DataFrame([{'day': r.demand_date, 'quantity': r.quantity} for r in rows])
        grouped = df.groupby('day')['quantity'].sum()
        for day, value in grouped.items():
            series.loc[pd.Timestamp(day)] = float(value)
    return series

def inventory_report(db: Session, days: int = 30, excess_days: int = 60, as_of: date | None = None):
    result = []
    for p in db.scalars(select(Product).order_by(Product.product_id)):
        movements = db.scalars(select(StockTransaction).where(StockTransaction.product_id == p.product_id)).all()
        stock = sum(t.quantity if t.transaction_type == 'in' else -t.quantity for t in movements)
        daily = daily_demand(db, p.product_id, days, as_of)
        average = float(np.mean(daily.to_numpy()))
        point = ceil(average * p.lead_time_days + p.safety_stock)
        shortage = stock <= point
        excess = stock > max(point, ceil(average * excess_days + p.safety_stock))
        suggested = max(0, ceil(average * (p.lead_time_days + days) + p.safety_stock - stock)) if shortage else 0
        result.append({'product_id': p.product_id, 'sku': p.sku, 'product_name': p.product_name, 'stock_units': stock, 'avg_demand_units_per_day': round(average, 3), 'lead_time_days': p.lead_time_days, 'safety_stock_units': p.safety_stock, 'reorder_point_units': point, 'stored_reorder_point_units': p.reorder_point, 'stockout_risk': shortage, 'excess_risk': excess, 'suggested_order_units': suggested, 'note': 'Decision support only; no order created'})
    return result

def supplier_report(db: Session):
    orders = db.scalars(select(PurchaseOrder)).all()
    suppliers = db.scalars(select(Supplier)).all()
    result = []
    for supplier in suppliers:
        received = [o for o in orders if o.supplier_id == supplier.supplier_id and o.status == 'received' and o.received_date]
        on_time = sum(o.received_date <= o.expected_date for o in received)
        lead = [float((o.received_date - o.order_date).days) for o in received]
        result.append({'supplier_id': supplier.supplier_id, 'supplier_name': supplier.supplier_name, 'received_orders': len(received), 'on_time_rate_pct': round(100 * on_time / len(received), 2) if received else None, 'avg_actual_lead_time_days': round(float(np.mean(lead)), 2) if lead else None})
    return result

def forecast_report(db: Session, product_id: int, days: int = 60, horizon: int = 7, as_of: date | None = None):
    series = daily_demand(db, product_id, days, as_of)
    values = series.to_numpy()
    split = max(7, int(len(values) * .8))
    if split >= len(values):
        raise ValueError('Not enough days for a holdout')
    train, test = values[:split], values[split:]
    baseline = float(np.mean(train))
    window = min(7, len(train))
    rolling = list(train)
    predictions = []
    for actual in test:
        predictions.append(float(np.mean(rolling[-window:])))
        rolling.append(float(actual))
    baseline_mae = float(np.mean(np.abs(test - baseline)))
    moving_mae = float(np.mean(np.abs(test - np.array(predictions))))
    selected = 'moving_average' if moving_mae < baseline_mae else 'historical_mean_baseline'
    current_prediction = float(np.mean(values[-window:])) if selected == 'moving_average' else float(np.mean(values))
    return {'product_id': product_id, 'history_days': days, 'test_days': len(test), 'horizon_days': horizon, 'baseline_mae_units_per_day': round(baseline_mae, 3), 'moving_average_mae_units_per_day': round(moving_mae, 3), 'selected_method': selected, 'forecast_units_per_day': round(current_prediction, 3), 'forecast_total_units': round(current_prediction * horizon, 2), 'history': [{'date': str(day.date()), 'quantity': float(v)} for day, v in series.items()], 'note': 'Simple constant-rate forecast, not an automated purchase decision'}
