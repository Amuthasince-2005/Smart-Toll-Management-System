"""
Application Entry Point - Run the Flask application
"""

from app import create_app, db
from app.models import (
    User, Vehicle, TollPlaza, TollRate, Wallet, 
    UserRole, VehicleType, PaymentMode
)
from datetime import datetime

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Register database models and functions for Flask shell
    """
    return {
        'db': db,
        'User': User,
        'Vehicle': Vehicle,
        'TollPlaza': TollPlaza,
        'TollRate': TollRate,
        'Wallet': Wallet,
        'UserRole': UserRole,
        'VehicleType': VehicleType,
        'PaymentMode': PaymentMode
    }

@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create admin user
    admin = User.query.filter_by(email='admin@toll.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@toll.com',
            phone='9999999999',
            address='HQ, Toll Authority',
            role=UserRole.ADMIN
        )
        admin.set_password('password')
        db.session.add(admin)
    
    # Create toll operator
    operator = User.query.filter_by(email='operator@toll.com').first()
    if not operator:
        operator = User(
            name='Toll Operator',
            email='operator@toll.com',
            phone='9876543210',
            address='Toll Plaza 1',
            role=UserRole.TOLL_OPERATOR
        )
        operator.set_password('password')
        db.session.add(operator)
    
    # Create sample user
    user = User.query.filter_by(email='user@toll.com').first()
    if not user:
        user = User(
            name='Sample User',
            email='user@toll.com',
            phone='9111111111',
            address='Delhi',
            role=UserRole.USER
        )
        user.set_password('password')
        db.session.add(user)
        db.session.flush()
        
        # Create wallet for user
        wallet = Wallet(user_id=user.user_id, balance=1000.0)
        db.session.add(wallet)
        
        # Add sample vehicles
        vehicle1 = Vehicle(
            vehicle_number='DL01AB1234',
            vehicle_type=VehicleType.CAR,
            rfid_tag_id='TAG001',
            user_id=user.user_id,
            status='active'
        )
        
        vehicle2 = Vehicle(
            vehicle_number='DL02CD5678',
            vehicle_type=VehicleType.BIKE,
            rfid_tag_id='TAG002',
            user_id=user.user_id,
            status='active'
        )
        
        db.session.add(vehicle1)
        db.session.add(vehicle2)
    
    # Create toll plazas
    plazas = [
        TollPlaza(plaza_name='Highway Plaza - North', location='Delhi-Gurgaon Highway, Km 15', city='Delhi', state='Delhi', num_lanes=4),
        TollPlaza(plaza_name='Highway Plaza - South', location='Delhi-Chennai Highway, Km 250', city='Madhya Pradesh', state='Madhya Pradesh', num_lanes=6),
        TollPlaza(plaza_name='City Bypass - East', location='Eastern Bypass, Km 30', city='Delhi', state='Delhi', num_lanes=4),
        TollPlaza(plaza_name='City Bypass - West', location='Western Bypass, Km 25', city='Haryana', state='Haryana', num_lanes=4),
    ]
    
    for plaza in plazas:
        existing = TollPlaza.query.filter_by(plaza_name=plaza.plaza_name).first()
        if not existing:
            db.session.add(plaza)
    
    db.session.commit()
    
    # Add toll rates
    plazas = TollPlaza.query.all()
    for plaza in plazas:
        # Check if rates already exist
        existing_rates = TollRate.query.filter_by(plaza_id=plaza.plaza_id).count()
        if existing_rates == 0:
            rates = [
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.BIKE, time_slot='normal', from_time='00:00', to_time='23:59', amount=25),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.CAR, time_slot='normal', from_time='00:00', to_time='23:59', amount=50),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.TRUCK, time_slot='normal', from_time='00:00', to_time='23:59', amount=150),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.BUS, time_slot='normal', from_time='00:00', to_time='23:59', amount=100),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.HEAVY_VEHICLE, time_slot='normal', from_time='00:00', to_time='23:59', amount=200),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.BIKE, time_slot='peak', from_time='07:00', to_time='10:00', amount=30),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.CAR, time_slot='peak', from_time='07:00', to_time='10:00', amount=65),
                TollRate(plaza_id=plaza.plaza_id, vehicle_type=VehicleType.TRUCK, time_slot='peak', from_time='07:00', to_time='10:00', amount=180),
            ]
            for rate in rates:
                db.session.add(rate)
    
    db.session.commit()
    print(f"[{datetime.now()}] Database initialized successfully with sample data!")

if __name__ == '__main__':
    # Initialize database on first run
    with app.app_context():
        db.create_all()
    
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=5000)
