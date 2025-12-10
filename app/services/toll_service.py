"""
Toll Processing Service - Core business logic for toll transactions
"""

from app import db
from app.models import (
    TollTransaction, TollRate, Vehicle, Wallet, WalletTransaction, 
    PaymentMode, TransactionStatus, VehicleType
)
from datetime import datetime
import json

class TollService:
    """
    Service class to handle toll processing and calculations
    """
    
    @staticmethod
    def get_vehicle_by_number(vehicle_number):
        """
        Fetch vehicle details by vehicle number or RFID tag
        
        Args:
            vehicle_number: Vehicle registration number or RFID tag ID
        
        Returns:
            Vehicle object or None
        """
        vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
        
        if not vehicle:
            vehicle = Vehicle.query.filter_by(rfid_tag_id=vehicle_number).first()
        
        return vehicle
    
    @staticmethod
    def calculate_toll_amount(plaza_id, vehicle_type, timestamp=None):
        """
        Calculate toll amount based on vehicle type, plaza, and time of day
        
        Args:
            plaza_id: ID of the toll plaza
            vehicle_type: Type of vehicle (bike, car, truck, bus, heavy_vehicle)
            timestamp: Datetime of toll crossing (default: current time)
        
        Returns:
            Dictionary with toll details or None if rate not found
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        current_time = timestamp.strftime('%H:%M')
        
        # Determine time slot (peak: 7-10 AM, 5-8 PM; normal: rest)
        hour = int(timestamp.strftime('%H'))
        if (7 <= hour < 10) or (17 <= hour < 20):
            time_slot = 'peak'
        else:
            time_slot = 'normal'
        
        # Query toll rate - find a rate that covers the current time
        toll_rate = TollRate.query.filter(
            TollRate.plaza_id == plaza_id,
            TollRate.vehicle_type == vehicle_type,
            TollRate.time_slot == time_slot
        ).first()
        
        if not toll_rate:
            # Fallback to normal rate if peak not found
            toll_rate = TollRate.query.filter(
                TollRate.plaza_id == plaza_id,
                TollRate.vehicle_type == vehicle_type,
                TollRate.time_slot == 'normal'
            ).first()
        
        if toll_rate:
            return {
                'amount': toll_rate.amount,
                'time_slot': toll_rate.time_slot,
                'rate_id': toll_rate.rate_id,
                'from_time': toll_rate.from_time,
                'to_time': toll_rate.to_time
            }
        
        return None
    
    @staticmethod
    def process_toll_transaction(vehicle_id, plaza_id, payment_mode, operator_id=None, lane_no=1):
        """
        Process a complete toll transaction
        
        Args:
            vehicle_id: ID of the vehicle
            plaza_id: ID of the toll plaza
            payment_mode: 'wallet', 'cash', or 'upi'
            operator_id: ID of toll operator processing the transaction
            lane_no: Lane number where toll was collected
        
        Returns:
            Dictionary with transaction result (success, message, transaction details)
        """
        try:
            # Fetch vehicle and validate
            vehicle = Vehicle.query.get(vehicle_id)
            if not vehicle or vehicle.status != 'active':
                return {
                    'success': False,
                    'message': 'Vehicle not found or inactive',
                    'transaction_id': None
                }
            
            # Calculate toll amount
            toll_details = TollService.calculate_toll_amount(plaza_id, vehicle.vehicle_type)
            if not toll_details:
                return {
                    'success': False,
                    'message': 'Toll rate not configured for this vehicle type',
                    'transaction_id': None
                }
            
            toll_amount = toll_details['amount']
            
            # Validate payment mode and process payment
            if payment_mode == PaymentMode.WALLET or payment_mode == 'wallet':
                payment_result = TollService._process_wallet_payment(
                    vehicle.user_id, toll_amount
                )
                if not payment_result['success']:
                    return {
                        'success': False,
                        'message': payment_result['message'],
                        'transaction_id': None
                    }
            
            # Create toll transaction record
            toll_txn = TollTransaction(
                vehicle_id=vehicle_id,
                plaza_id=plaza_id,
                lane_no=lane_no,
                amount=toll_amount,
                payment_mode=payment_mode if isinstance(payment_mode, PaymentMode) else PaymentMode(payment_mode),
                status=TransactionStatus.COMPLETED,
                operator_id=operator_id,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(toll_txn)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Toll transaction completed successfully',
                'transaction_id': toll_txn.txn_id,
                'amount': toll_amount,
                'vehicle_number': vehicle.vehicle_number,
                'vehicle_type': vehicle.vehicle_type.value,
                'timestamp': toll_txn.timestamp,
                'payment_mode': payment_mode,
                'toll_details': toll_details
            }
        
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error processing toll: {str(e)}',
                'transaction_id': None
            }
    
    @staticmethod
    def _process_wallet_payment(user_id, amount):
        """
        Process payment from user's wallet
        
        Args:
            user_id: ID of the user
            amount: Amount to deduct
        
        Returns:
            Dictionary with result (success, message)
        """
        try:
            wallet = Wallet.query.filter_by(user_id=user_id).first()
            
            if not wallet:
                return {'success': False, 'message': 'Wallet not found'}
            
            if wallet.balance < amount:
                return {'success': False, 'message': 'Insufficient wallet balance'}
            
            # Deduct from wallet
            wallet.balance -= amount
            wallet.last_updated = datetime.utcnow()
            
            # Create wallet transaction record
            wallet_txn = WalletTransaction(
                wallet_id=wallet.wallet_id,
                txn_type='deduction',
                amount=amount,
                description=f'Toll deduction at plaza {wallet.wallet_id}',
                timestamp=datetime.utcnow()
            )
            
            db.session.add(wallet_txn)
            db.session.commit()
            
            return {'success': True, 'message': 'Payment processed', 'balance': wallet.balance}
        
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Payment error: {str(e)}'}
    
    @staticmethod
    def recharge_wallet(user_id, amount):
        """
        Recharge user's wallet
        
        Args:
            user_id: ID of the user
            amount: Amount to recharge
        
        Returns:
            Dictionary with result
        """
        try:
            wallet = Wallet.query.filter_by(user_id=user_id).first()
            
            if not wallet:
                wallet = Wallet(user_id=user_id, balance=0.0)
                db.session.add(wallet)
                db.session.commit()
            
            wallet.balance += amount
            wallet.last_updated = datetime.utcnow()
            
            wallet_txn = WalletTransaction(
                wallet_id=wallet.wallet_id,
                txn_type='recharge',
                amount=amount,
                description='Wallet recharge',
                timestamp=datetime.utcnow()
            )
            
            db.session.add(wallet_txn)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Wallet recharged successfully',
                'balance': wallet.balance
            }
        
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Recharge error: {str(e)}'}
    
    @staticmethod
    def get_vehicle_toll_history(vehicle_id, limit=50):
        """
        Get toll transaction history for a vehicle
        
        Args:
            vehicle_id: ID of the vehicle
            limit: Number of records to fetch
        
        Returns:
            List of toll transactions
        """
        return TollTransaction.query.filter_by(vehicle_id=vehicle_id).order_by(
            TollTransaction.timestamp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_user_toll_summary(user_id):
        """
        Get toll transaction summary for a user's vehicles
        
        Args:
            user_id: ID of the user
        
        Returns:
            Dictionary with summary statistics
        """
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        vehicle_ids = [v.vehicle_id for v in vehicles]
        
        if not vehicle_ids:
            return {
                'total_transactions': 0,
                'total_amount_paid': 0,
                'vehicles': 0,
                'last_transaction': None
            }
        
        transactions = TollTransaction.query.filter(
            TollTransaction.vehicle_id.in_(vehicle_ids)
        ).all()
        
        total_amount = sum(t.amount for t in transactions)
        last_txn = TollTransaction.query.filter(
            TollTransaction.vehicle_id.in_(vehicle_ids)
        ).order_by(TollTransaction.timestamp.desc()).first()
        
        return {
            'total_transactions': len(transactions),
            'total_amount_paid': total_amount,
            'vehicles': len(vehicles),
            'last_transaction': last_txn.timestamp if last_txn else None
        }
