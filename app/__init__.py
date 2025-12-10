"""
Smart Toll Management System - Flask Application Initialization
"""

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
import os
from datetime import datetime

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config=None):
    """
    Application factory function to create and configure Flask app.
    
    Args:
        config: Configuration dictionary (optional)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///smart_toll_system.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app)
    
    # Create database tables
    with app.app_context():
        from app.models import User, Vehicle, TollPlaza, TollRate, Wallet, WalletTransaction, TollTransaction, TrafficLog
        db.create_all()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.toll import toll_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(toll_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Root route - redirect to login or dashboard
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models import UserRole
            if current_user.role == UserRole.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == UserRole.TOLL_OPERATOR:
                return redirect(url_for('toll.booth'))
            else:
                return redirect(url_for('dashboard.home'))
        return redirect(url_for('auth.login'))
    
    print(f"[{datetime.now()}] Flask app initialized successfully!")
    
    return app
