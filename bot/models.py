from pydantic import BaseModel
from typing import List


class CategoryModel(BaseModel):
    title: str
    products: int

class Bulk(BaseModel):
    range: List[int]
    unit_price: float

class ProductModel(BaseModel):
    title: str
    price: float
    unit: str
    bulks: List[Bulk]
    url: str

class LobbyUserModel(BaseModel):
    id: int
    wants: int
    chat_id: int
    menu_id: int | None
    status: str

class LobbyModel(BaseModel):
    common_price: float
    bulk: float
    unit: str
    users: List[LobbyUserModel]
