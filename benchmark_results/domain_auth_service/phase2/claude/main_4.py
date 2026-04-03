from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from .models import User, db
import re

class UserRegistrationSchema(Schema):
    username = fields.Str(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 6)

class UserLoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def register_user():
    """Register a new user"""
    try:
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'messages': err.messages}), 400
    except Exception:
        return jsonify({'error': 'Invalid JSON data'}), 400

    username = data['username']
    email = data['email']
    password = data['password']

    # Validate password strength
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    # Create new user
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

def login_user():
    """Login user"""
    try:
        schema = UserLoginSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'messages': err.messages}), 400
    except Exception:
        return jsonify({'error': 'Invalid JSON data'}), 400

    username = data['username']
    password = data['password']

    # Find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@jwt_required()
def get_current_user():
    """Get current user information"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200