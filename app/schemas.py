from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class SupplierIn(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=150)
class SupplierOut(SupplierIn, ORMModel):
    supplier_id: int

class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    product_name: str = Field(min_length=1, max_length=150)
    unit_cost: float = Field(ge=0)
    lead_time_days: int = Field(ge=0)
    safety_stock: int = Field(default=10, ge=0)
class ProductOut(ProductIn, ORMModel):
    product_id: int
    reorder_point: int

class PurchaseOrderIn(BaseModel):
    supplier_id: int
    order_date: date
    expected_date: date
    received_date: date | None = None
    status: Literal['pending', 'received', 'cancelled'] = 'pending'
    @model_validator(mode='after')
    def dates_valid(self):
        if self.expected_date < self.order_date:
            raise ValueError('expected_date must be on or after order_date')
        if self.received_date and self.received_date < self.order_date:
            raise ValueError('received_date must be on or after order_date')
        if (self.status == 'received') != (self.received_date is not None):
            raise ValueError('received status requires received_date, and other statuses must not have it')
        return self
class PurchaseOrderOut(PurchaseOrderIn, ORMModel):
    po_id: int

class StockIn(BaseModel):
    product_id: int
    transaction_date: date
    transaction_type: Literal['in', 'out']
    quantity: int = Field(gt=0)
class StockOut(StockIn, ORMModel):
    transaction_id: int

class DemandIn(BaseModel):
    product_id: int
    demand_date: date
    quantity: int = Field(ge=0)
class DemandOut(DemandIn, ORMModel):
    demand_id: int
