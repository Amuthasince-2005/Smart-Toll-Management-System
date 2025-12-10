from app import create_app, db
from app.models import User, UserRole

app = create_app()
with app.app_context():
    # Update admin user role
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        admin.role = UserRole.ADMIN
        db.session.commit()
        print(f"Updated {admin.email} to ADMIN role ✓")
    else:
        # Create admin user if it doesn't exist
        admin = User(
            email='admin@example.com',
            name='Admin User',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin user: admin@example.com / admin123 ✓")
    
    # Verify
    admin = User.query.filter_by(email='admin@example.com').first()
    print(f"\nVerification: {admin.email} has role {admin.role}")
