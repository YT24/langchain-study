from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    id: int
    order_no: str
    user_id: str
    status: str
    total_amount: float
    created_at: str


@dataclass
class User:
    id: int
    user_id: str
    name: str
    phone: Optional[str]
    level: str
    balance: float
    created_at: str


@dataclass
class Inventory:
    id: int
    sku: str
    warehouse: str
    quantity: int
    updated_at: str
