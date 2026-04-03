from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)

    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id"))

    wishlist = relationship("Wishlist", back_populates="items")