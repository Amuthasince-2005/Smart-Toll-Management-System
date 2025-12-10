"""
Toll Booth Routes - Toll transaction processing interface
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models import UserRole, Vehicle, PaymentMode
from app.services.toll_service import TollService
from datetime import datetime

toll_bp = Blueprint('toll', __name__, url_prefix='/toll')

@toll_bp.route('/booth', methods=['GET', 'POST'])
@login_required
def booth():
    """
    Toll booth interactive interface
    Only accessible to Toll Operators and Admins
    """
    if current_user.role not in [UserRole.TOLL_OPERATOR, UserRole.ADMIN]:
        return "Unauthorized", 403
    
    if request.method == 'POST':
        # AJAX request to process toll
        data = request.get_json()
        vehicle_number = data.get('vehicle_number')
        plaza_id = data.get('plaza_id')
        payment_mode = data.get('payment_mode', 'wallet')
        lane_no = data.get('lane_no', 1)
        
        # Fetch vehicle
        vehicle = TollService.get_vehicle_by_number(vehicle_number)
        
        if not vehicle:
            return jsonify({
                'success': False,
                'message': 'Vehicle not found in database',
                'receipt': None
            }), 404
        
        # Process transaction
        result = TollService.process_toll_transaction(
            vehicle.vehicle_id,
            plaza_id,
            payment_mode,
            operator_id=current_user.user_id,
            lane_no=lane_no
        )
        
        return jsonify(result)
    
    return render_template('toll/booth.html')

@toll_bp.route('/search-vehicle', methods=['POST'])
@login_required
def search_vehicle():
    """
    API endpoint to search and fetch vehicle details
    """
    if current_user.role not in [UserRole.TOLL_OPERATOR, UserRole.ADMIN]:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    vehicle_number = data.get('vehicle_number', '').strip()
    
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'Vehicle number required'})
    
    vehicle = TollService.get_vehicle_by_number(vehicle_number)
    
    if not vehicle:
        return jsonify({
            'success': False,
            'message': 'Vehicle not found'
        })
    
    return jsonify({
        'success': True,
        'vehicle': {
            'vehicle_id': vehicle.vehicle_id,
            'vehicle_number': vehicle.vehicle_number,
            'vehicle_type': vehicle.vehicle_type.value,
            'status': vehicle.status,
            'owner_name': vehicle.owner.name,
            'wallet_balance': vehicle.owner.wallet.balance if vehicle.owner.wallet else 0
        }
    })

@toll_bp.route('/process', methods=['POST'])
@login_required
def process_toll():
    """
    Process toll transaction
    """
    if current_user.role not in [UserRole.TOLL_OPERATOR, UserRole.ADMIN]:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    try:
        vehicle_id = int(data.get('vehicle_id'))
        plaza_id = int(data.get('plaza_id'))
        payment_mode = data.get('payment_mode', 'wallet')
        lane_no = int(data.get('lane_no', 1))
        
        result = TollService.process_toll_transaction(
            vehicle_id=vehicle_id,
            plaza_id=plaza_id,
            payment_mode=payment_mode,
            operator_id=current_user.user_id,
            lane_no=lane_no
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@toll_bp.route('/receipt/<int:txn_id>', methods=['GET'])
@login_required
def get_receipt(txn_id):
    """
    Get transaction receipt
    """
    from app.models import TollTransaction, TollPlaza
    
    txn = TollTransaction.query.get(txn_id)
    
    if not txn:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404
    
    # Check authorization
    if current_user.role == UserRole.USER:
        if txn.vehicle.user_id != current_user.user_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'receipt': {
            'txn_id': txn.txn_id,
            'vehicle_number': txn.vehicle.vehicle_number,
            'vehicle_type': txn.vehicle.vehicle_type.value,
            'plaza_name': txn.plaza.plaza_name,
            'plaza_location': txn.plaza.location,
            'lane_no': txn.lane_no,
            'amount': txn.amount,
            'payment_mode': txn.payment_mode.value,
            'timestamp': txn.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': txn.status.value
        }
    })
