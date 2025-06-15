import os
from app import create_app, db
from app.models import User, WorkoutTemplate, TemplateExercise
from werkzeug.security import generate_password_hash
from flask_migrate import upgrade
from sqlalchemy import inspect

def initialise_app():
    app = create_app()
    with app.app_context():

        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            print("No tables found — initialising database...")
            db.create_all()
        else:
            print("Database already initialised.")

        try:
            upgrade()
        except Exception as e:
            print("Migration error or unnecessary:", e)

        # Admin details from environment or defaults
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'adminpass123')

        # Create admin user if not already present
        existing = User.query.filter_by(username=admin_username).first()
        if not existing:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    initialise_app()