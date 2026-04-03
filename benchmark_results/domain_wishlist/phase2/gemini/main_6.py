from pydantic import BaseModel
from typing import List

class WishlistItemBase(BaseModel):
    product_id: str

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItem(WishlistItemBase):
    id: int

    class Config:
        orm_mode = True

class WishlistBase(BaseModel):
    user_id: str

class Wishlist(WishlistBase):
    id: int
    items: List[WishlistItem] = []

    class Config:
        orm_mode = True