from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .models import db
from .auth import register_user, login_user, get_current_user
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register routes
    @app.route('/register', methods=['POST'])
    def register():
        return register_user()
    
    @app.route('/login', methods=['POST'])
    def login():
        return login_user()
    
    @app.route('/me', methods=['GET'])
    def me():
        return get_current_user()
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy'}, 200
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Token is required'}, 401
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)