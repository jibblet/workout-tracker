from datetime import datetime, timedelta
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

def format_date_pretty(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return date.strftime("%d %B %Y")  # e.g. 16 May 2025


def format_duration(minutes):
    hours, mins = divmod(round(minutes), 60)
    if hours == 0:
        return f"{mins} min"
    if mins == 0:
        return f"{hours} hr"
    return f"{hours} hr {mins} min"

def get_exercise_count_by_day(workouts, start_date, days=7):
    day_labels = [(start_date + timedelta(days=i)).strftime('%d/%m') for i in range(days)]
    date_counts = Counter([w.date for w in workouts])
    workouts_count_list = [date_counts.get(start_date + timedelta(days=i), 0) for i in range(days)]
    return day_labels, workouts_count_list


def get_daily_durations(exercises, start_date, day_span):
    daily_totals = defaultdict(int)

    for exercise in exercises:
        exercise_date = exercise.date  # Ensure we strip time
        if start_date <= exercise_date <= start_date + timedelta(days=day_span):
            daily_totals[exercise_date] += exercise.duration or 0  # Fallback to 0 if null

    return daily_totals


def get_total_cardio_distance(exercises):
    total_distance = 0
    for ex in exercises:
        if ex.type == 'cardio' and ex.distance:
            total_distance += float(ex.distance)
    return total_distance

def get_total_strength_volume(exercises):
    total_volume = 0
    for ex in exercises:
        if ex.type == 'strength' and ex.reps and ex.weights:
            try:
                weights = [int(w) for w in ex.weights.split('/') if w.strip().isdigit()]
                for weight in weights:
                    total_volume += weight * ex.reps
            except ValueError:
                continue
    return total_volume

def get_time_per_type(exercises):
    totals = defaultdict(int)

    # Sum durations by type
    for ex in exercises:
        totals[ex.type] += ex.duration or 0

    # Total time (in minutes)
    total_time = sum(totals.values()) or 1  # avoid division by zero

    # Calculate percentages and formatted durations
    workout_type_percentages = {
        type_: round((duration / total_time) * 100, 1)
        for type_, duration in totals.items()
    }

    workout_type_durations = {
        type_: format_duration(duration)
        for type_, duration in totals.items()
    }

    return workout_type_percentages, workout_type_durations

def format_pace(pace):
    if pace is None:
        return "N/A"
    minutes = int(pace)
    seconds = round((pace - minutes) * 60)
    return f"{minutes}m {seconds}s /km"

def get_fastest_pace(exercises):
    fastest = None
    for ex in exercises:
        if ex.type == 'cardio' and ex.distance and ex.duration:
            try:
                km = float(ex.distance)
                if km > 0:
                    pace = ex.duration / km  # minutes per km
                    if fastest is None or pace < fastest:
                        fastest = pace
            except (ValueError, IndexError):
                continue
    return format_pace(fastest)  # e.g. 5.4 means 5 mins 24 secs

def get_total_volume_by_exercise(exercises):
    """Calculate total volume grouped by exercise name"""
    volume_by_exercise = defaultdict(float)
    
    for ex in exercises:
        if ex.type == 'strength':
            volume_by_exercise[ex.exercise] += ex.total_volume
    
    return dict(volume_by_exercise)

def get_weekly_volume_progression(exercises, weeks=4):
    """Analyze volume progression over the last N weeks"""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    weekly_data = {}
    
    for week in range(weeks):
        week_start = today - timedelta(days=today.weekday() + (week * 7))
        week_end = week_start + timedelta(days=6)
        week_label = f"Week {weeks - week}"
        
        week_exercises = [ex for ex in exercises if week_start <= ex.date <= week_end]
        weekly_data[week_label] = {
            'total_volume': sum(ex.total_volume for ex in week_exercises if ex.type == 'strength'),
            'by_exercise': get_total_volume_by_exercise(week_exercises),
            'workout_count': len(set(ex.date for ex in week_exercises))
        }
    
    return weekly_data

def analyze_volume_trends(weekly_data):
    """Detect trends and provide recommendations"""
    weeks = list(weekly_data.keys())
    volumes = [weekly_data[week]['total_volume'] for week in weeks]
    
    trends = {}
    recommendations = []
    
    if len(volumes) >= 2:
        # Calculate week-over-week change
        recent_change = volumes[-1] - volumes[-2] if len(volumes) >= 2 else 0
        recent_change_pct = (recent_change / volumes[-2] * 100) if volumes[-2] > 0 else 0
        
        trends['recent_change'] = recent_change
        trends['recent_change_pct'] = round(recent_change_pct, 1)
        
        # Overall trend calculation
        if len(volumes) >= 3:
            trend_sum = sum(volumes[i] - volumes[i-1] for i in range(1, len(volumes)))
            trends['overall_trend'] = 'increasing' if trend_sum > 0 else 'decreasing' if trend_sum < 0 else 'stable'
        
        # Generate recommendations
        if recent_change_pct < -10:
            recommendations.append("Consider increasing volume - you've decreased by more than 10% this week")
        elif recent_change_pct > 20:
            recommendations.append("Volume increased significantly - monitor for overtraining")
        elif -5 <= recent_change_pct <= 5:
            recommendations.append("Volume is stable - consider progressive overload")
        
        # Check for exercise-specific recommendations
        current_week = weeks[-1]
        previous_week = weeks[-2] if len(weeks) >= 2 else None
        
        if previous_week:
            current_exercises = weekly_data[current_week]['by_exercise']
            previous_exercises = weekly_data[previous_week]['by_exercise']
            
            for exercise, current_vol in current_exercises.items():
                prev_vol = previous_exercises.get(exercise, 0)
                if prev_vol > 0:
                    exercise_change = ((current_vol - prev_vol) / prev_vol) * 100
                    if exercise_change < -15:
                        recommendations.append(f"{exercise}: Volume dropped {abs(exercise_change):.1f}% - consider increasing")
    
    trends['recommendations'] = recommendations
    return trends

def export_analysis_data(user_id, exercises):
    """Prepare comprehensive data for LLM analysis"""
    analysis_data = {
        'user_summary': {
            'total_workouts': len(exercises),
            'date_range': {
                'start': min(ex.date for ex in exercises).strftime('%Y-%m-%d') if exercises else None,
                'end': max(ex.date for ex in exercises).strftime('%Y-%m-%d') if exercises else None
            }
        },
        'volume_analysis': {
            'total_volume': sum(ex.total_volume for ex in exercises if ex.type == 'strength'),
            'by_exercise': get_total_volume_by_exercise(exercises),
            'weekly_progression': get_weekly_volume_progression(exercises),
        },
        'performance_metrics': {
            'total_cardio_distance': get_total_cardio_distance(exercises),
            'fastest_pace': get_fastest_pace(exercises),
            'difficulty_ratings': [ex.difficulty_rating for ex in exercises if ex.difficulty_rating],
            'pain_levels': [ex.pain_level for ex in exercises if ex.pain_level is not None],
        },
        'workout_patterns': {
            'by_type': get_time_per_type(exercises)[0],
            'common_exercises': Counter([ex.exercise for ex in exercises]).most_common(10),
            'workout_frequency': len(set(ex.date for ex in exercises)),
        }
    }
    
    # Add trend analysis
    weekly_data = analysis_data['volume_analysis']['weekly_progression']
    analysis_data['trends'] = analyze_volume_trends(weekly_data)
    
    return analysis_data