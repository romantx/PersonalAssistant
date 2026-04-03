import pytest
from app import create_app, db
from app.models import User, Product, Wishlist
from flask_jwt_extended import create_access_token
from config import TestConfig

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()

@pytest.fixture
def sample_user(app):
    """Create a sample user for testing"""
    user = User(username='testuser', email='test@example.com')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def sample_product(app):
    """Create a sample product for testing"""
    product = Product(name='Test Product', description='A test product', price=99.99)
    db.session.add(product)
    db.session.commit()
    return product

@pytest.fixture
def auth_token(app, sample_user):
    """Create authentication token for testing"""
    with app.app_context():
        return create_access_token(identity=sample_user.id)

@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers for testing"""
    return {'Authorization': f'Bearer {auth_token}'}