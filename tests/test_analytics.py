from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import Product, StockTransaction, DemandRecord, Supplier, PurchaseOrder
from app.analytics import inventory_report, forecast_report, supplier_report

def test_reports():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        p = Product(sku='T1', product_name='Test', unit_cost=10, lead_time_days=3, safety_stock=5)
        s = Supplier(supplier_name='Test Supplier')
        db.add_all([p,s]); db.flush()
        today = date.today()
        db.add(StockTransaction(product_id=p.product_id, transaction_date=today, transaction_type='in', quantity=20))
        for n in range(60):
            db.add(DemandRecord(product_id=p.product_id, demand_date=today-timedelta(days=n), quantity=2))
        db.add(PurchaseOrder(supplier_id=s.supplier_id, order_date=today-timedelta(days=10), expected_date=today-timedelta(days=5), received_date=today-timedelta(days=6), status='received'))
        db.commit()
        report = inventory_report(db)
        assert report[0]['reorder_point_units'] == 11
        assert report[0]['stockout_risk'] is False
        forecast = forecast_report(db,p.product_id)
        assert forecast['baseline_mae_units_per_day'] == 0
        assert forecast['forecast_total_units'] == 14
        assert supplier_report(db)[0]['on_time_rate_pct'] == 100
