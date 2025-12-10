"""
Authentication Routes - Login, Signup, Logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Wallet, UserRole
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET'])
def login():
    """
    Login choice page - redirect to admin or user login
    """
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == UserRole.TOLL_OPERATOR:
            return redirect(url_for('toll.booth'))
        else:
            return redirect(url_for('dashboard.home'))
    
    return render_template('auth/login_choice.html')

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page and handler
    """
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
        logout_user()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user is admin
            if user.role != UserRole.ADMIN:
                flash('Only administrators can access admin portal', 'danger')
                return redirect(url_for('auth.admin_login'))
            
            if not user.is_active:
                flash('Your account has been deactivated', 'danger')
                return redirect(url_for('auth.admin_login'))
            
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/admin_login.html')

@auth_bp.route('/user-login', methods=['GET', 'POST'])
def user_login():
    """
    User login page and handler
    """
    if current_user.is_authenticated:
        if current_user.role == UserRole.USER:
            return redirect(url_for('dashboard.home'))
        logout_user()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user is regular user (not admin)
            if user.role == UserRole.ADMIN:
                flash('Admins should use the Admin Login portal', 'info')
                return redirect(url_for('auth.admin_login'))
            
            if not user.is_active:
                flash('Your account has been deactivated', 'danger')
                return redirect(url_for('auth.user_login'))
            
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            
            # Redirect based on role
            if user.role == UserRole.TOLL_OPERATOR:
                return redirect(next_page or url_for('toll.booth'))
            else:
                return redirect(next_page or url_for('dashboard.home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/user_login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page and handler
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Create user
            user = User(
                name=name,
                email=email,
                phone=phone,
                address=address,
                role=UserRole.USER,
                created_at=datetime.utcnow()
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Get user_id
            
            # Create wallet for new user
            wallet = Wallet(user_id=user.user_id, balance=0.0)
            db.session.add(wallet)
            
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration error: {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Logout current user
    """
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
