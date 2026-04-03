from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import Base, engine, get_db

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Wishlist API",
    version="1.0.0",
)

@app.post("/wishlist", response_model=schemas.Wishlist, status_code=status.HTTP_201_CREATED)
def create_wishlist_for_user(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(security.get_current_user_id),
):
    db_wishlist = crud.get_wishlist_by_user_id(db, user_id=current_user_id)
    if db_wishlist:
        raise HTTPException(status_code=409, detail="Wishlist already exists for this user")
    return crud.create_wishlist(db=db, user_id=current_user_id)

@app.get("/wishlist", response_model=schemas.Wishlist)
def read_own_wishlist(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(security.get_current_user_id),
):
    db_wishlist = crud.get_wishlist_by_user_id(db, user_id=current_user_id)
    if db_wishlist is None:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return db_wishlist

@app.post("/wishlist/{wishlist_id}/items", response_model=schemas.WishlistItem)
def add_product_to_wishlist(
    wishlist_id: int,
    item: schemas.WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(security.get_current_user_id),
):
    db_wishlist = crud.get_wishlist_by_id(db, wishlist_id=wishlist_id)
    if db_wishlist is None:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    if db_wishlist.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this wishlist")
    
    crud.add_item_to_wishlist(db=db, wishlist=db_wishlist, item=item)
    return {"description": "Added", "product_id": item.product_id} # Spec says "Added"

@app.delete("/wishlist/{wishlist_id}/items/{product_id}", response_model=Dict[str, str])
def remove_product_from_wishlist(
    wishlist_id: int,
    product_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(security.get_current_user_id),
):
    db_wishlist = crud.get_wishlist_by_id(db, wishlist_id=wishlist_id)
    if db_wishlist is None:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    if db_wishlist.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this wishlist")

    item_to_delete = crud.get_item_in_wishlist(db, wishlist_id=wishlist_id, product_id=product_id)
    if item_to_delete is None:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")

    crud.remove_item_from_wishlist(db, item=item_to_delete)
    return {"description": "Removed"}