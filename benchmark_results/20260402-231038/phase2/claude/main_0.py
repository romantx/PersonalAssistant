# app.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

security = HTTPBearer()

class Wishlist(BaseModel):
    id: str
    items: List[str]

wishlist_data = {}

@app.post("/wishlist", status_code=201)
async def create_wishlist(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = credentials.credentials
    wishlist = Wishlist(id=user_id, items=[])
    wishlist_data[user_id] = wishlist
    return wishlist

@app.get("/wishlist", status_code=200)
async def view_wishlist(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = credentials.credentials
    if user_id not in wishlist_data:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return wishlist_data[user_id]

@app.post("/wishlist/{wishlist_id}/items", status_code=200)
async def add_product(wishlist_id: str, product_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = credentials.credentials
    if user_id != wishlist_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this wishlist")
    if user_id not in wishlist_data:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    wishlist_data[user_id].items.append(product_id)
    return {"message": "Product added to wishlist"}

@app.delete("/wishlist/{wishlist_id}/items/{product_id}", status_code=200)
async def remove_product(wishlist_id: str, product_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = credentials.credentials
    if user_id != wishlist_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this wishlist")
    if user_id not in wishlist_data:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    if product_id not in wishlist_data[user_id].items:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")
    wishlist_data[user_id].items.remove(product_id)
    return {"message": "Product removed from wishlist"}