from typing import TypedDict


class Product(TypedDict):
    sku: str
    description: str
    family: str
    current_stock: int


class EditableProduct(TypedDict):
    sku: str
    description: str
    family: str
    current_stock: int


class StockByFamily(TypedDict):
    name: str
    stock: int


class DashboardStats(TypedDict):
    total_products: int
    total_stock: int
    family_count: int
    low_stock_count: int


class SpecialFamily(TypedDict):
    id: int
    name: str


class DiscontinuedSKU(TypedDict):
    id: int
    sku: str
    reason: str | None