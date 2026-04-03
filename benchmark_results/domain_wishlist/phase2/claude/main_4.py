from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from app.models import User
from flask import jsonify

def get_current_user():
    """Get the current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def auth_required(f):
    """Decorator to require authentication and inject current user"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        return f(current_user, *args, **kwargs)
    return decorated_function