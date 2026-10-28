from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app import models, schemas, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title='Supply Chain Optimization API', version='1.0.0', lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

resources = [
    ('suppliers', models.Supplier, schemas.SupplierIn, schemas.SupplierOut, 'supplier_id'),
    ('products', models.Product, schemas.ProductIn, schemas.ProductOut, 'product_id'),
    ('purchase-orders', models.PurchaseOrder, schemas.PurchaseOrderIn, schemas.PurchaseOrderOut, 'po_id'),
    ('stock-transactions', models.StockTransaction, schemas.StockIn, schemas.StockOut, 'transaction_id'),
    ('demand-records', models.DemandRecord, schemas.DemandIn, schemas.DemandOut, 'demand_id'),
]

def register_resource(name, model, input_schema, output_schema, key):
    def list_items(db: Session = Depends(get_db)):
        return db.scalars(select(model).order_by(getattr(model, key))).all()
    def create_item(payload: input_schema, db: Session = Depends(get_db)):
        obj = model(**payload.model_dump())
        db.add(obj)
        try:
            db.commit()
            db.refresh(obj)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Duplicate value or missing related record')
        return obj
    def get_item(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, 'Not found')
        return obj
    def update_item(item_id: int, payload: input_schema, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, 'Not found')
        for k, v in payload.model_dump().items():
            setattr(obj, k, v)
        try:
            db.commit()
            db.refresh(obj)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Duplicate value or missing related record')
        return obj
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(404, 'Not found')
        db.delete(obj)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Record is referenced by another record')
        return {'deleted': True}
    app.add_api_route(f'/{name}', list_items, methods=['GET'], response_model=list[output_schema], name=f'list_{name}')
    app.add_api_route(f'/{name}', create_item, methods=['POST'], response_model=output_schema, status_code=201, name=f'create_{name}')
    app.add_api_route(f'/{name}/{{item_id}}', get_item, methods=['GET'], response_model=output_schema, name=f'get_{name}')
    app.add_api_route(f'/{name}/{{item_id}}', update_item, methods=['PUT'], response_model=output_schema, name=f'update_{name}')
    app.add_api_route(f'/{name}/{{item_id}}', delete_item, methods=['DELETE'], name=f'delete_{name}')

for resource in resources:
    register_resource(*resource)

@app.get('/analytics/inventory')
def inventory(days: int = 30, excess_days: int = 60, db: Session = Depends(get_db)):
    if not 14 <= days <= 365 or not 1 <= excess_days <= 365:
        raise HTTPException(422, 'days must be 14..365; excess_days must be 1..365')
    return analytics.inventory_report(db, days, excess_days)

@app.get('/analytics/suppliers')
def suppliers(db: Session = Depends(get_db)):
    return analytics.supplier_report(db)

@app.get('/analytics/forecast/{product_id}')
def forecast(product_id: int, days: int = 60, horizon: int = 7, db: Session = Depends(get_db)):
    if db.get(models.Product, product_id) is None:
        raise HTTPException(404, 'Product not found')
    if not 14 <= days <= 365 or not 1 <= horizon <= 90:
        raise HTTPException(422, 'days must be 14..365; horizon must be 1..90')
    return analytics.forecast_report(db, product_id, days, horizon)
