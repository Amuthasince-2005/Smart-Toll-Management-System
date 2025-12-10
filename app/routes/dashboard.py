"""
User Dashboard Routes - User-facing pages for viewing vehicles, wallet, toll history
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Vehicle, Wallet, VehicleType, UserRole
from app.services.toll_service import TollService
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@dashboard_bp.route('/home')
@login_required
def home():
    """
    User home/dashboard page
    Shows overview of vehicles, wallet, and recent transactions
    """
    if current_user.role == UserRole.ADMIN:
        return redirect(url_for('admin.dashboard'))
    
    # Get user statistics
    user_summary = TollService.get_user_toll_summary(current_user.user_id)
    vehicles = Vehicle.query.filter_by(user_id=current_user.user_id).all()
    wallet = Wallet.query.filter_by(user_id=current_user.user_id).first()
    
    return render_template('dashboard/home.html',
                          summary=user_summary,
                          vehicles=vehicles,
                          wallet=wallet)

@dashboard_bp.route('/vehicles')
@login_required
def vehicles():
    """
    List user's vehicles
    """
    vehicles = Vehicle.query.filter_by(user_id=current_user.user_id).all()
    return render_template('dashboard/vehicles.html', vehicles=vehicles)

@dashboard_bp.route('/vehicle/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    """
    Add new vehicle
    """
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        vehicle_type = request.form.get('vehicle_type')
        rfid_tag_id = request.form.get('rfid_tag_id', '').strip() or None
        
        # Validation
        if not vehicle_number or not vehicle_type:
            flash('Vehicle number and type are required', 'danger')
            return redirect(url_for('dashboard.add_vehicle'))
        
        # Check if vehicle already exists
        if Vehicle.query.filter_by(vehicle_number=vehicle_number).first():
            flash('Vehicle number already registered', 'danger')
            return redirect(url_for('dashboard.add_vehicle'))
        
        try:
            vehicle = Vehicle(
                vehicle_number=vehicle_number,
                vehicle_type=VehicleType(vehicle_type),
                rfid_tag_id=rfid_tag_id,
                user_id=current_user.user_id,
                status='active',
                registration_date=datetime.utcnow()
            )
            db.session.add(vehicle)
            db.session.commit()
            
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('dashboard.vehicles'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding vehicle: {str(e)}', 'danger')
    
    return render_template('dashboard/add_vehicle.html', vehicle_types=VehicleType)

@dashboard_bp.route('/wallet')
@login_required
def wallet():
    """
    User wallet page - view balance and transaction history
    """
    from app.models import WalletTransaction
    
    wallet = Wallet.query.filter_by(user_id=current_user.user_id).first()
    
    if not wallet:
        wallet = Wallet(user_id=current_user.user_id, balance=0.0)
        db.session.add(wallet)
        db.session.commit()
    
    wallet_transactions = WalletTransaction.query.filter_by(wallet_id=wallet.wallet_id).order_by(
        WalletTransaction.timestamp.desc()
    ).limit(20).all()
    
    return render_template('dashboard/wallet.html',
                          wallet=wallet,
                          wallet_transactions=wallet_transactions)

@dashboard_bp.route('/wallet/recharge', methods=['GET', 'POST'])
@login_required
def recharge_wallet():
    """
    Recharge wallet
    """
    if request.method == 'POST':
        amount = request.form.get('amount')
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0', 'danger')
                return redirect(url_for('dashboard.recharge_wallet'))
            
            result = TollService.recharge_wallet(current_user.user_id, amount)
            
            if result['success']:
                flash(f'Wallet recharged with Rs. {amount}', 'success')
                return redirect(url_for('dashboard.wallet'))
            else:
                flash(result['message'], 'danger')
        
        except ValueError:
            flash('Invalid amount', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    wallet = Wallet.query.filter_by(user_id=current_user.user_id).first()
    return render_template('dashboard/wallet.html', wallet=wallet)

@dashboard_bp.route('/toll-history')
@login_required
def toll_history():
    """
    View toll transaction history for all user vehicles
    """
    from app.models import TollTransaction
    
    vehicles = Vehicle.query.filter_by(user_id=current_user.user_id).all()
    vehicle_ids = [v.vehicle_id for v in vehicles]
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if vehicle_ids:
        pagination = TollTransaction.query.filter(
            TollTransaction.vehicle_id.in_(vehicle_ids)
        ).order_by(TollTransaction.timestamp.desc()).paginate(page=page, per_page=per_page)
    else:
        pagination = None
    
    return render_template('dashboard/toll_history.html',
                          pagination=pagination,
                          vehicles=vehicles)

@dashboard_bp.route('/api/vehicle/<int:vehicle_id>/history')
@login_required
def api_vehicle_history(vehicle_id):
    """
    API endpoint to get vehicle toll history
    """
    vehicle = Vehicle.query.get(vehicle_id)
    
    if not vehicle or vehicle.user_id != current_user.user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    transactions = TollService.get_vehicle_toll_history(vehicle_id, limit=50)
    
    return jsonify({
        'success': True,
        'vehicle_number': vehicle.vehicle_number,
        'transactions': [
            {
                'txn_id': t.txn_id,
                'plaza': t.plaza.plaza_name,
                'amount': t.amount,
                'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_mode': t.payment_mode.value,
                'status': t.status.value
            }
            for t in transactions
        ]
    })
