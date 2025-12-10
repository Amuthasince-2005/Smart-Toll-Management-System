"""
Database Models for Smart Toll Management System
"""

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    """Enum for user roles"""
    ADMIN = 'admin'
    TOLL_OPERATOR = 'toll_operator'
    USER = 'user'

class VehicleType(enum.Enum):
    """Enum for vehicle types"""
    BIKE = 'bike'
    CAR = 'car'
    TRUCK = 'truck'
    BUS = 'bus'
    HEAVY_VEHICLE = 'heavy_vehicle'

class PaymentMode(enum.Enum):
    """Enum for payment modes"""
    WALLET = 'wallet'
    CASH = 'cash'
    UPI = 'upi'

class TransactionStatus(enum.Enum):
    """Enum for transaction status"""
    COMPLETED = 'completed'
    PENDING = 'pending'
    FAILED = 'failed'
    REFUNDED = 'refunded'

# ============================================================================
# User Model
# ============================================================================
class User(UserMixin, db.Model):
    """
    User Model - Represents system users (Admin, Toll Operators, Vehicle Owners)
    """
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')
    wallet = db.relationship('Wallet', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    toll_transactions = db.relationship('TollTransaction', foreign_keys='TollTransaction.operator_id', backref='operator', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Required by Flask-Login"""
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.email}>'

# ============================================================================
# Vehicle Model
# ============================================================================
class Vehicle(db.Model):
    """
    Vehicle Model - Represents vehicles in the system
    """
    __tablename__ = 'vehicle'
    
    vehicle_id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.Enum(VehicleType), nullable=False)
    rfid_tag_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    toll_transactions = db.relationship('TollTransaction', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Vehicle {self.vehicle_number}>'

# ============================================================================
# Toll Plaza Model
# ============================================================================
class TollPlaza(db.Model):
    """
    Toll Plaza Model - Represents toll plazas/booths
    """
    __tablename__ = 'toll_plaza'
    
    plaza_id = db.Column(db.Integer, primary_key=True)
    plaza_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    num_lanes = db.Column(db.Integer, default=4, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    toll_rates = db.relationship('TollRate', backref='plaza', lazy=True, cascade='all, delete-orphan')
    toll_transactions = db.relationship('TollTransaction', backref='plaza', lazy=True, cascade='all, delete-orphan')
    traffic_logs = db.relationship('TrafficLog', backref='plaza', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TollPlaza {self.plaza_name}>'

# ============================================================================
# Toll Rate Model
# ============================================================================
class TollRate(db.Model):
    """
    Toll Rate Model - Defines toll rates for different vehicle types and time slots
    """
    __tablename__ = 'toll_rate'
    
    rate_id = db.Column(db.Integer, primary_key=True)
    plaza_id = db.Column(db.Integer, db.ForeignKey('toll_plaza.plaza_id'), nullable=False)
    vehicle_type = db.Column(db.Enum(VehicleType), nullable=False)
    from_time = db.Column(db.String(5), nullable=False)  # HH:MM format
    to_time = db.Column(db.String(5), nullable=False)    # HH:MM format
    time_slot = db.Column(db.String(20), nullable=False)  # 'normal' or 'peak'
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('plaza_id', 'vehicle_type', 'from_time', 'to_time', name='unique_rate'),
    )
    
    def __repr__(self):
        return f'<TollRate {self.vehicle_type.value} @ Plaza {self.plaza_id}>'

# ============================================================================
# Wallet Model
# ============================================================================
class Wallet(db.Model):
    """
    Wallet Model - Represents user's wallet balance
    """
    __tablename__ = 'wallet'
    
    wallet_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    transactions = db.relationship('WalletTransaction', backref='wallet', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Wallet user_id={self.user_id} balance={self.balance}>'

# ============================================================================
# Wallet Transaction Model
# ============================================================================
class WalletTransaction(db.Model):
    """
    Wallet Transaction Model - Records all wallet transactions (recharge/deduction/refund)
    """
    __tablename__ = 'wallet_transaction'
    
    wallet_txn_id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.wallet_id'), nullable=False)
    txn_type = db.Column(db.String(20), nullable=False)  # 'recharge', 'deduction', 'refund'
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    reference_txn_id = db.Column(db.String(100), nullable=True)  # Link to toll transaction
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<WalletTransaction {self.txn_type} Rs.{self.amount}>'

# ============================================================================
# Toll Transaction Model
# ============================================================================
class TollTransaction(db.Model):
    """
    Toll Transaction Model - Records all toll crossing transactions
    """
    __tablename__ = 'toll_transaction'
    
    txn_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.vehicle_id'), nullable=False)
    plaza_id = db.Column(db.Integer, db.ForeignKey('toll_plaza.plaza_id'), nullable=False)
    lane_no = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.Enum(PaymentMode), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.COMPLETED, nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<TollTransaction vehicle_id={self.vehicle_id} amount={self.amount}>'

# ============================================================================
# Traffic Log Model
# ============================================================================
class TrafficLog(db.Model):
    """
    Traffic Log Model - Aggregated traffic data for ML analysis and predictions
    Used for Spark analytics and ML model training
    """
    __tablename__ = 'traffic_log'
    
    log_id = db.Column(db.Integer, primary_key=True)
    plaza_id = db.Column(db.Integer, db.ForeignKey('toll_plaza.plaza_id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    vehicle_count = db.Column(db.Integer, default=0, nullable=False)
    total_revenue = db.Column(db.Float, default=0.0, nullable=False)
    avg_speed = db.Column(db.Float, nullable=True)
    traffic_level = db.Column(db.String(20), default='normal', nullable=False)  # low, normal, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('plaza_id', 'date', 'hour', name='unique_traffic_log'),
        db.Index('idx_traffic_log_date_hour', 'date', 'hour'),
    )
    
    def __repr__(self):
        return f'<TrafficLog plaza={self.plaza_id} date={self.date} hour={self.hour}>'
