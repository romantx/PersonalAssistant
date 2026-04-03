from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Wishlist, Product, WishlistItem
from app.auth import auth_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('main', __name__)

@bp.route('/wishlist', methods=['POST'])
@auth_required
def create_wishlist(current_user):
    """Create a new wishlist for the authenticated user"""
    try:
        data = request.get_json() or {}
        name = data.get('name', 'My Wishlist')
        
        wishlist = Wishlist(user_id=current_user.id, name=name)
        db.session.add(wishlist)
        db.session.commit()
        
        return jsonify({
            'id': wishlist.id,
            'name': wishlist.name,
            'created_at': wishlist.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create wishlist'}), 500

@bp.route('/wishlist', methods=['GET'])
@auth_required
def get_wishlist(current_user):
    """Get user's wishlists with their items"""
    try:
        wishlists = Wishlist.query.filter_by(user_id=current_user.id).all()
        
        result = []
        for wishlist in wishlists:
            wishlist_data = {
                'id': wishlist.id,
                'name': wishlist.name,
                'created_at': wishlist.created_at.isoformat(),
                'items': []
            }
            
            for item in wishlist.items:
                wishlist_data['items'].append({
                    'id': item.id,
                    'product_id': item.product_id,
                    'product_name': item.product.name,
                    'product_description': item.product.description,
                    'product_price': str(item.product.price) if item.product.price else None,
                    'added_at': item.added_at.isoformat()
                })
            
            result.append(wishlist_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve wishlists'}), 500

@bp.route('/wishlist/<int:wishlist_id>/items', methods=['POST'])
@auth_required
def add_product_to_wishlist(current_user, wishlist_id):
    """Add a product to the specified wishlist"""
    try:
        data = request.get_json()
        if not data or 'product_id' not in data:
            return jsonify({'error': 'Product ID is required'}), 400
        
        product_id = data['product_id']
        
        # Verify wishlist belongs to current user
        wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first()
        if not wishlist:
            return jsonify({'error': 'Wishlist not found'}), 404
        
        # Verify product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check if product is already in wishlist
        existing_item = WishlistItem.query.filter_by(
            wishlist_id=wishlist_id, 
            product_id=product_id
        ).first()
        if existing_item:
            return jsonify({'message': 'Product already in wishlist'}), 200
        
        # Add product to wishlist
        wishlist_item = WishlistItem(wishlist_id=wishlist_id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({
            'message': 'Product added to wishlist',
            'item_id': wishlist_item.id,
            'product_name': product.name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product to wishlist'}), 500

@bp.route('/wishlist/<int:wishlist_id>/items/<int:product_id>', methods=['DELETE'])
@auth_required
def remove_product_from_wishlist(current_user, wishlist_id, product_id):
    """Remove a product from the specified wishlist"""
    try:
        # Verify wishlist belongs to current user
        wishlist = Wishlist.query.filter_by(id=wishlist_id, user_id=current_user.id).first()
        if not wishlist:
            return jsonify({'error': 'Wishlist not found'}), 404
        
        # Find and remove the wishlist item
        wishlist_item = WishlistItem.query.filter_by(
            wishlist_id=wishlist_id,
            product_id=product_id
        ).first()
        
        if not wishlist_item:
            return jsonify({'error': 'Product not found in wishlist'}), 404
        
        db.session.delete(wishlist_item)
        db.session.commit()
        
        return jsonify({'message': 'Product removed from wishlist'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove product from wishlist'}), 500

# Health check endpoint
@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200