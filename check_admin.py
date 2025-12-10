from app import create_app, db
from app.models import User, UserRole

app = create_app()
with app.app_context():
    users = User.query.all()
    print("All users in database:")
    for user in users:
        print(f"  Email: {user.email}, Role: {user.role}, Active: {user.is_active}")
    
    # Check if admin exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        print(f"\nAdmin user exists: {admin.email} with role {admin.role}")
    else:
        print("\nNo admin user found. Creating admin user...")
        admin = User(
            email='admin@example.com',
            name='Admin User',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@example.com / admin123")
