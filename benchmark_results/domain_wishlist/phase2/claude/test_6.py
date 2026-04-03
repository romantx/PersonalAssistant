from app import create_app, db
from app.models import User, Product
from flask_jwt_extended import create_access_token

app = create_app()

@app.before_first_request
def create_tables():
    """Create database tables and add sample data"""
    db.create_all()
    
    # Add sample user if none exists
    if not User.query.first():
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        
        # Add sample products
        products = [
            Product(name='iPhone 15', description='Latest Apple smartphone', price=999.99),
            Product(name='MacBook Pro', description='Professional laptop', price=1999.99),
            Product(name='AirPods Pro', description='Wireless earphones', price=249.99),
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        print("Sample data added!")

@app.cli.command()
def get_test_token():
    """Generate a test JWT token for the sample user"""
    user = User.query.filter_by(username='testuser').first()
    if user:
        token = create_access_token(identity=user.id)
        print(f"Test token for user '{user.username}': {token}")
    else:
        print("No test user found. Please run the app first to create sample data.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)