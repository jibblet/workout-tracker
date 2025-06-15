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

    @property
    def total_volume(self):
        """Calculate total volume for strength exercises (sets × reps × weight)"""
        if self.type != 'strength' or not self.sets or not self.reps or not self.weights:
            return 0

        try:
            # Handle multiple weights separated by '/'
            weights = [float(w.strip()) for w in self.weights.split('/') if w.strip()]
            if not weights:
                return 0

            # Calculate volume per set and sum them up
            total_vol = 0
            for i, weight in enumerate(weights):
                # If fewer weights than sets, use the last weight for remaining sets
                if i < self.sets:
                    total_vol += self.reps * weight
                else:
                    # Use the last available weight for remaining sets
                    total_vol += self.reps * weights[-1] * (self.sets - len(weights))
                    break

            # If we have fewer weight entries than sets, multiply the remaining sets
            if len(weights) < self.sets:
                remaining_sets = self.sets - len(weights)
                total_vol += remaining_sets * self.reps * weights[-1]

            return total_vol
        except (ValueError, IndexError):
            return 0

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "A Day", "B Day", "C Day"
    description = db.Column(db.String(200), nullable=True)  # e.g., "Bicep and Chest"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercises = db.relationship('TemplateExercise', backref='template', lazy=True, cascade='all, delete-orphan')

class TemplateExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='strength')  # strength or cardio
    default_sets = db.Column(db.Integer, nullable=True)
    default_reps = db.Column(db.Integer, nullable=True)
    default_weight = db.Column(db.String(100), nullable=True)
    default_distance = db.Column(Float, nullable=True)
    default_duration = db.Column(Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Exercise-specific notes/reminders
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id'), nullable=False)