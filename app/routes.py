from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash, Response
from .models import db, Exercise, User, WorkoutTemplate, TemplateExercise
from .utils import *
from datetime import datetime, timedelta
import csv
from io import StringIO
import string
import secrets

main = Blueprint('main', __name__)


@main.route('/')
def index():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    date_str = request.args.get("date", datetime.today().strftime("%Y-%m-%d"))
    formatted_date = format_date_pretty(date_str)
    workouts = Exercise.query.filter_by(date=date_str, user_id=user.id).all()
    templates = WorkoutTemplate.query.filter_by(user_id=user.id).all()

    prev_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    return render_template("index.html", date=date_str, formatted_date=formatted_date, workouts=workouts, templates=templates, prev_date=prev_date, next_date=next_date)


@main.route('/add', methods=['GET', 'POST'])
def add_workout():
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        exercise = request.form['exercise']
        workout_type = request.form['type']
        user_id = session['user_id']
        comments = request.form.get('comments', '').strip() or None
        
        # Structured feedback
        difficulty_rating = int(request.form.get('difficulty_rating')) if request.form.get('difficulty_rating') else None
        pain_level = int(request.form.get('pain_level')) if request.form.get('pain_level') else None
        selected_tags = request.form.getlist('tags')
        tags = ','.join(selected_tags) if selected_tags else None

        if workout_type == 'cardio':
            # Only get duration for cardio workouts
            duration = float(request.form.get('duration', 0)) if request.form.get('duration') else None
            new_workout = Exercise(
                date=date,
                exercise=exercise,
                type='cardio',
                distance=float(request.form.get('distance', 0)),
                duration=duration,
                sets=0,
                reps=0,
                weights=None,
                comments=comments,
                difficulty_rating=difficulty_rating,
                pain_level=pain_level,
                tags=tags,
                user_id=user_id
            )
        else:
            # Strength workouts do not have duration
            sets = int(request.form['sets']) if request.form['sets'] else 0
            reps = int(request.form['reps']) if request.form['reps'] else 0
            weight_inputs = [
                request.form.get(f'weight{i+1}', '').strip()
                for i in range(sets)
            ]
            weights = '/'.join([w for w in weight_inputs if w])
            new_workout = Exercise(
                date=date,
                exercise=exercise,
                type='strength',
                sets=sets,
                reps=reps,
                weights=weights if weights else None,
                distance=None,
                duration=None,  # No duration for strength exercises
                comments=comments,
                difficulty_rating=difficulty_rating,
                pain_level=pain_level,
                tags=tags,
                user_id=user_id
            )

        print(f"New Workout: {new_workout}")
        print(new_workout.__dict__)

        db.session.add(new_workout)
        db.session.commit()

        return redirect(url_for('main.index', date=date.isoformat()))

    date_str = request.args.get("date", datetime.today().strftime("%Y-%m-%d"))
    formatted_date = format_date_pretty(date_str)
    return render_template("new_workout.html", date=date_str, formatted_date=formatted_date)


@main.route('/edit/<int:workout_id>', methods=['GET', 'POST'])
def edit_workout(workout_id):
    workout = Exercise.query.get_or_404(workout_id)
    if workout.user_id != session['user_id']:
        abort(403)

    if request.method == 'POST':
        workout.exercise = request.form['exercise']
        workout.type = request.form['type']
        workout.comments = request.form.get('comments', '').strip() or None
        
        # Update structured feedback
        workout.difficulty_rating = int(request.form.get('difficulty_rating')) if request.form.get('difficulty_rating') else None
        workout.pain_level = int(request.form.get('pain_level')) if request.form.get('pain_level') else None
        selected_tags = request.form.getlist('tags')
        workout.tags = ','.join(selected_tags) if selected_tags else None

        if workout.type == 'strength':
            # Strength workouts do not have duration
            workout.duration = None
            workout.sets = int(request.form['sets']) if request.form['sets'] else 0
            workout.reps = int(request.form['reps']) if request.form['reps'] else 0

            weight_inputs = [
                request.form.get(f'weight{i+1}', '').strip()
                for i in range(workout.sets)
            ]
            workout.weights = '/'.join([w for w in weight_inputs if w]) or None

            # Clear cardio fields
            workout.distance = None

        elif workout.type == 'cardio':
            # Only cardio workouts have duration
            workout.duration = float(request.form.get('duration', 0)) if request.form.get('duration') else None
            workout.sets = 0
            workout.reps = 0
            workout.weights = None
            workout.distance = float(request.form.get('distance', 0))

        db.session.commit()
        return redirect(url_for('main.index', date=workout.date.isoformat()))

    date_str = workout.date.strftime('%Y-%m-%d')
    formatted_date = format_date_pretty(date_str)
    return render_template("new_workout.html", date=date_str, formatted_date=formatted_date, workout=workout)


@main.route('/delete/<int:workout_id>', methods=['POST'])
def delete_workout(workout_id):
    workout = Exercise.query.get_or_404(workout_id)
    if workout.user_id != session['user_id']:
        abort(403)

    date = workout.date.isoformat()
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for('main.index', date=date))

# ---------- Admin Page ----------

@main.route('/admin')
def admin():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    if not user.is_admin:
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

@main.route('/admin/reset_password/<int:user_id>', methods=['POST'])
def reset_user_password(user_id):
    from .models import User 
    user = User.query.get_or_404(user_id)

    # Only allow if current user is admin
    from flask import session
    admin_user = User.query.get(session.get('user_id'))
    if not admin_user or not admin_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.admin'))

    # Generate a secure random password
    characters = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(characters) for _ in range(10))

    # Set and hash the password
    user.set_password(new_password)
    db.session.commit()

    flash(f"Password for {user.username} has been reset to: {new_password}", "success")
    return redirect(url_for('main.admin'))

@main.route('/admin/make_admin/<int:user_id>', methods=['POST'])
def make_admin(user_id):
    from .models import User
    user = User.query.get_or_404(user_id)

    admin_user = User.query.get(session.get('user_id'))
    if not admin_user or not admin_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))

    user.is_admin = True
    db.session.commit()
    flash(f"{user.username} is now an admin.", "success")
    return redirect(url_for('main.admin'))

@main.route('/admin/revoke/<int:user_id>', methods=['POST'])
def revoke_admin(user_id):
    from .models import User
    user = User.query.get_or_404(user_id)

    admin_user = User.query.get(session.get('user_id'))
    if not admin_user or not admin_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    admin_count = User.query.filter_by(is_admin=True).count()
    if admin_count <= 1:
        flash('Cannot revoke admin privileges from the last remaining admin.', 'error')
        return redirect(url_for('main.admin'))

    user.is_admin = False
    db.session.commit()
    flash(f"{user.username}'s admin privilegs have been revoked.", "success")
    return redirect(url_for('main.admin'))

@main.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    from .models import User
    user = User.query.get_or_404(user_id)

    admin_user = User.query.get(session.get('user_id'))
    if not admin_user or not admin_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.admin'))

    if user.id == admin_user.id:
        flash("You can't delete your own account while logged in.", 'error')
        return redirect(url_for('main.admin'))

    db.session.delete(user)
    db.session.commit()
    flash(f"{user.username}'s account has been deleted.", 'success')
    return redirect(url_for('main.admin'))

# ---------- Settings Page ----------
@main.route('/settings', methods=['GET', 'POST'])
def settings():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Handle password change
        if 'current_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                flash('Please fill in all password fields.', 'error')
                return redirect(url_for('main.settings'))

            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('main.settings'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('main.settings'))

            user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('main.settings'))

        # Handle units change
        elif 'units' in request.form:
            selected_units = request.form.get('units')
            if selected_units in ['metric', 'imperial']:
                user.units = selected_units
                db.session.commit()
                flash('Units updated successfully.', 'success')
            else:
                flash('Invalid units selected.', 'error')
            return redirect(url_for('main.settings'))

        # Handle username/email updates
        elif request.form.get('form_type') == 'update_account':
            update_field = request.form.get('update_field')

            if update_field == 'username':
                new_username = request.form.get('new_username')
                if not new_username:
                    flash('Username cannot be empty.', 'error')
                elif new_username == user.username:
                    flash('Username is unchanged.', 'info')
                elif User.query.filter_by(username=new_username).first():
                    flash('That username is already taken.', 'error')
                else:
                    user.username = new_username
                    db.session.commit()
                    flash('Username updated successfully.', 'success')

            elif update_field == 'email':
                new_email = request.form.get('new_email')
                if not new_email:
                    flash('Email cannot be empty.', 'error')
                elif new_email == user.email:
                    flash('Email is unchanged.', 'info')
                elif User.query.filter_by(email=new_email).first():
                    flash('That email is already taken.', 'error')
                else:
                    user.email = new_email
                    db.session.commit()
                    flash('Email updated successfully.', 'success')

            return redirect(url_for('main.settings'))


    # GET request renders the page
    return render_template('settings.html', user=user)

@main.route('/download_workouts')
def download_workouts():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    workouts = Exercise.query.filter_by(user_id=user.id).order_by(Exercise.date.desc()).all()

    si = StringIO()
    cw = csv.writer(si)
    
    # Write header
    cw.writerow(['Date', 'Type', 'Exercise', 'Sets', 'Reps', 'Weights', 'Distance', 'Duration', 'Difficulty', 'Pain_Level', 'Tags', 'Comments'])

    # Write workout data
    for w in workouts:
        cw.writerow([
            w.date.strftime('%Y-%m-%d'),
            w.type,
            w.exercise,
            w.sets or '',
            w.reps or '',
            w.weights or '',
            w.distance or '',
            w.duration or '',
            w.difficulty_rating or '',
            w.pain_level or '',
            w.tags or '',
            w.comments or ''
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=workouts.csv"}
    )

# ---------- Workout Templates ----------

@main.route('/templates')
def templates():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    templates = WorkoutTemplate.query.filter_by(user_id=user.id).all()
    return render_template('templates.html', templates=templates)

@main.route('/templates/new', methods=['GET', 'POST'])
def new_template():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        template = WorkoutTemplate(
            name=name,
            description=description,
            user_id=user.id
        )
        db.session.add(template)
        db.session.flush()  # Get the ID
        
        # Add exercises
        exercise_count = int(request.form.get('exercise_count', 0))
        for i in range(exercise_count):
            exercise_name = request.form.get(f'exercise_{i}_name')
            exercise_type = request.form.get(f'exercise_{i}_type')
            if exercise_name and exercise_type:
                template_exercise = TemplateExercise(
                    exercise_name=exercise_name,
                    type=exercise_type,
                    default_sets=int(request.form.get(f'exercise_{i}_sets')) if request.form.get(f'exercise_{i}_sets') else None,
                    default_reps=int(request.form.get(f'exercise_{i}_reps')) if request.form.get(f'exercise_{i}_reps') else None,
                    default_weight=request.form.get(f'exercise_{i}_weight') or None,
                    default_distance=float(request.form.get(f'exercise_{i}_distance')) if request.form.get(f'exercise_{i}_distance') else None,
                    default_duration=float(request.form.get(f'exercise_{i}_duration')) if request.form.get(f'exercise_{i}_duration') else None,
                    template_id=template.id
                )
                db.session.add(template_exercise)
        
        db.session.commit()
        flash('Workout template created successfully!', 'success')
        return redirect(url_for('main.templates'))
    
    return render_template('new_template.html')

@main.route('/templates/edit/<int:template_id>', methods=['GET', 'POST'])
def edit_template(template_id):
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    template = WorkoutTemplate.query.get_or_404(template_id)
    if template.user_id != user.id:
        abort(403)
    
    if request.method == 'POST':
        template.name = request.form['name']
        template.description = request.form.get('description', '')
        
        # Delete existing exercises and add new ones
        TemplateExercise.query.filter_by(template_id=template.id).delete()
        
        exercise_count = int(request.form.get('exercise_count', 0))
        for i in range(exercise_count):
            exercise_name = request.form.get(f'exercise_{i}_name')
            exercise_type = request.form.get(f'exercise_{i}_type')
            if exercise_name and exercise_type:
                template_exercise = TemplateExercise(
                    exercise_name=exercise_name,
                    type=exercise_type,
                    default_sets=int(request.form.get(f'exercise_{i}_sets')) if request.form.get(f'exercise_{i}_sets') else None,
                    default_reps=int(request.form.get(f'exercise_{i}_reps')) if request.form.get(f'exercise_{i}_reps') else None,
                    default_weight=request.form.get(f'exercise_{i}_weight') or None,
                    default_distance=float(request.form.get(f'exercise_{i}_distance')) if request.form.get(f'exercise_{i}_distance') else None,
                    default_duration=float(request.form.get(f'exercise_{i}_duration')) if request.form.get(f'exercise_{i}_duration') else None,
                    template_id=template.id
                )
                db.session.add(template_exercise)
        
        db.session.commit()
        flash('Workout template updated successfully!', 'success')
        return redirect(url_for('main.templates'))
    
    return render_template('new_template.html', template=template)

@main.route('/templates/delete/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    template = WorkoutTemplate.query.get_or_404(template_id)
    if template.user_id != user.id:
        abort(403)
    
    db.session.delete(template)
    db.session.commit()
    flash('Workout template deleted successfully!', 'success')
    return redirect(url_for('main.templates'))

@main.route('/use_template/<int:template_id>')
def use_template(template_id):
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    template = WorkoutTemplate.query.get_or_404(template_id)
    if template.user_id != user.id:
        abort(403)
    
    date_str = request.args.get("date", datetime.today().strftime("%Y-%m-%d"))
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Create exercises from template
    for template_exercise in template.exercises:
        new_exercise = Exercise(
            date=date,
            exercise=template_exercise.exercise_name,
            type=template_exercise.type,
            sets=template_exercise.default_sets or 0,
            reps=template_exercise.default_reps or 0,
            weights=template_exercise.default_weight,
            distance=template_exercise.default_distance,
            duration=template_exercise.default_duration,
            user_id=user.id
        )
        db.session.add(new_exercise)
    
    db.session.commit()
    flash(f'Applied "{template.name}" template to {date_str}!', 'success')
    return redirect(url_for('main.index', date=date_str))

# ---------- Stats Page ----------

@main.route('/dashboard')
def dashboard():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        return redirect(url_for('auth.login'))
    
    period = request.args.get('period', 'week')
    today = datetime.now().date()
    
    if period == 'month':
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    else:  # week
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    day_span = (end_date - start_date).days + 1

    exercises = Exercise.query.filter(
        Exercise.user_id == session['user_id'],
        Exercise.date >= start_date,
        Exercise.date <= end_date
    ).all()

    daily_durations = get_daily_durations(exercises, start_date, day_span)

    workout_duration_graph_labels = [(start_date + timedelta(days=i)).strftime('%d/%m') for i in range(day_span)]
    workout_duration_graph_data = [daily_durations.get(start_date + timedelta(days=i), 0) for i in range(day_span)]

    workout_type_percentages, workout_type_durations = get_time_per_type(exercises)

    total_workout_duration = format_duration(sum(daily_durations.values()))
    longest_workout_duration = format_duration(max(daily_durations.values()) if daily_durations else 0)

    total_cardio_distance = get_total_cardio_distance(exercises)

    total_strength_volume = get_total_strength_volume(exercises)

    fastest_pace_formatted = get_fastest_pace(exercises)

    return render_template('dashboard.html',
                           period=period,                    
                           workout_duration_graph_labels=workout_duration_graph_labels,
                           workout_duration_graph_data=workout_duration_graph_data,
                           workout_type_percentages=workout_type_percentages,
                           workout_type_durations=workout_type_durations,
                           total_workout_duration=total_workout_duration,
                           longest_workout_duration=longest_workout_duration,
                           total_cardio_distance=total_cardio_distance,
                           fastest_pace_formatted=fastest_pace_formatted,
                           total_strength_volume=total_strength_volume,
    )