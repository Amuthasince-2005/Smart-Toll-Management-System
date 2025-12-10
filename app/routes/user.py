"""
User Routes - User profile and account management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    """
    User profile page
    """
    return render_template('user/profile.html', user=current_user)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit user profile
    """
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        try:
            current_user.name = name
            current_user.phone = phone
            current_user.address = address
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('user/edit_profile.html', user=current_user)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Change user password
    """
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_user.check_password(old_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('user.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('user.change_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('user.change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('user.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('user/change_password.html')
