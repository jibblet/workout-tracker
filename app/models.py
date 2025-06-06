from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Float

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    units = db.Column(db.String(10), nullable=False, default='metric')
    workouts = db.relationship('Exercise', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    exercise = db.Column(db.String(100), nullable=False)
    duration = db.Column(Float)  # allows for integers and floats e.g. 30 or 27.5

    # Type of workout
    type = db.Column(db.String(20), nullable=False, default='strength')  # strength or cardio

    # Strength fields
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weights = db.Column(db.String(100))

    # Cardio fields
    distance = db.Column(Float)  # allows for integers and floats e.g. 10 or 7.5

    # Comments field
    comments = db.Column(db.Text, nullable=True)  # Optional workout notes
    
    # Structured feedback for AI analysis
    difficulty_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    pain_level = db.Column(db.Integer, nullable=True)        # 0-5 scale
    tags = db.Column(db.String(200), nullable=True)          # JSON string of selected tags

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
