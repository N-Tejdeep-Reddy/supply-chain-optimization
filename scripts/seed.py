from datetime import date, timedelta
from random import Random
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import Supplier, Product, PurchaseOrder, StockTransaction, DemandRecord

Base.metadata.create_all(engine)
rng = Random(24)
with SessionLocal() as db:
    if db.scalar(select(Supplier.supplier_id).limit(1)) is not None:
        print('Seed skipped: suppliers already exist')
    else:
        suppliers = [Supplier(supplier_name=n) for n in ['North Logistics', 'Rapid Wholesale', 'Reliable Distributors']]
        db.add_all(suppliers)
        db.flush()
        products = [Product(sku='SKU-100', product_name='Wireless Mouse', unit_cost=450, lead_time_days=5, safety_stock=20), Product(sku='SKU-200', product_name='USB-C Cable', unit_cost=120, lead_time_days=8, safety_stock=30), Product(sku='SKU-300', product_name='Laptop Stand', unit_cost=850, lead_time_days=4, safety_stock=15)]
        db.add_all(products)
        db.flush()
        today = date.today()
        for idx, p in enumerate(products):
            db.add(StockTransaction(product_id=p.product_id, transaction_date=today-timedelta(days=90), transaction_type='in', quantity=[280,900,110][idx]))
            for day in range(90):
                day_date = today - timedelta(days=89-day)
                demand = max(0, round([5,12,3][idx] + rng.gauss(0,2)))
                db.add(DemandRecord(product_id=p.product_id, demand_date=day_date, quantity=demand))
                db.add(StockTransaction(product_id=p.product_id, transaction_date=day_date, transaction_type='out', quantity=max(1,demand))) if demand else None
        for idx in range(15):
            order_date = today - timedelta(days=70-idx*4)
            expected = order_date + timedelta(days=6)
            received = expected + timedelta(days=rng.choice([-2,-1,0,0,1,3]))
            db.add(PurchaseOrder(supplier_id=suppliers[idx%3].supplier_id, order_date=order_date, expected_date=expected, received_date=received, status='received'))
        db.commit()
        print('Demo data inserted')
