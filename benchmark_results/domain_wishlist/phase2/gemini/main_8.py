from sqlalchemy.orm import Session
from . import models, schemas

def get_wishlist_by_user_id(db: Session, user_id: str):
    return db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).first()

def get_wishlist_by_id(db: Session, wishlist_id: int):
    return db.query(models.Wishlist).filter(models.Wishlist.id == wishlist_id).first()

def create_wishlist(db: Session, user_id: str):
    db_wishlist = models.Wishlist(user_id=user_id)
    db.add(db_wishlist)
    db.commit()
    db.refresh(db_wishlist)
    return db_wishlist

def add_item_to_wishlist(db: Session, wishlist: models.Wishlist, item: schemas.WishlistItemCreate):
    # Check if item already exists
    existing_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.wishlist_id == wishlist.id,
        models.WishlistItem.product_id == item.product_id
    ).first()
    
    if existing_item:
        return existing_item # Idempotent: return existing if found

    db_item = models.WishlistItem(product_id=item.product_id, wishlist_id=wishlist.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_item_in_wishlist(db: Session, wishlist_id: int, product_id: str):
    return db.query(models.WishlistItem).filter(
        models.WishlistItem.wishlist_id == wishlist_id,
        models.WishlistItem.product_id == product_id
    ).first()

def remove_item_from_wishlist(db: Session, item: models.WishlistItem):
    db.delete(item)
    db.commit()