from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.admin import bp
from app.models import Race, Runner, Event, RaceResult
from app.admin.forms import RaceForm, RunnerForm, EventForm
from app.utils.decorators import admin_required
from app.utils.email import send_race_notification
from datetime import datetime

def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    races_count = Race.query.count()
    runners_count = Runner.query.count()
    active_races = Race.query.filter_by(status='in_progress').count()
    recent_races = Race.query.order_by(Race.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         races_count=races_count,
                         runners_count=runners_count,
                         active_races=active_races,
                         recent_races=recent_races)

@bp.route('/races')
@login_required
@admin_required
def races():
    races = Race.query.order_by(Race.date.desc()).all()
    return render_template('admin/races.html', races=races)

@bp.route('/race/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_race():
    form = RaceForm()
    print("Method:", request.method)
    if request.method == 'POST':
        print("POST data:", request.form)
        print("Form errors:", form.errors)
    
    if form.validate_on_submit():
        print("Form validated!")
        race = Race(
            name=form.name.data,
            date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            registration_fields=form.registration_fields.data,
            admin_id=current_user.id
        )
        db.session.add(race)

        try:
            # Handle events
            print("Processing events...")
            events_data = {}
            
            # Process events data differently
            for key in request.form:
                if key.startswith('events['):
                    # Extract event number and field name
                    # events[0][name] -> ['events', '0', 'name']
                    parts = key.replace(']', '').replace('[', ' ').split()
                    event_num = int(parts[1])
                    field_name = parts[2]
                    
                    if event_num not in events_data:
                        events_data[event_num] = {}
                    events_data[event_num][field_name] = request.form[key]

            print("Events data:", events_data)

            # Create events
            for event_num in events_data:
                event_data = events_data[event_num]
                event = Event(
                    name=event_data['name'],
                    distance=float(event_data['distance']),
                    has_checkpoints=bool(event_data.get('has_checkpoints', False)),
                    number_of_laps=int(event_data.get('laps', 1))
                )
                race.events.append(event)
                print(f"Added event: {event_data}")

            db.session.commit()
            print("Database committed!")
            flash('Race created successfully.', 'success')
            return redirect(url_for('admin_panel.races'))
        except Exception as e:
            print(f"Error creating race: {str(e)}")
            db.session.rollback()
            flash('Error creating race.', 'error')
    else:
        print("Form validation failed:", form.errors)

    return render_template('admin/race_form.html', form=form, title='New Race')

@bp.route('/race/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_race(id):
    race = Race.query.get_or_404(id)
    form = RaceForm(obj=race)
    if form.validate_on_submit():
        race.name = form.name.data
        race.date = form.date.data
        race.location = form.location.data
        race.description = form.description.data
        race.registration_fields = form.registration_fields.data
        db.session.commit()
        flash('Race updated successfully.', 'success')
        return redirect(url_for('admin_panel.races'))
    return render_template('admin/race_form.html', form=form, race=race, title='Edit Race')

@bp.route('/race/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_race(id):
    race = Race.query.get_or_404(id)
    db.session.delete(race)
    db.session.commit()
    flash('Race deleted successfully.', 'success')
    return jsonify({'status': 'success'})

@bp.route('/runners')
@login_required
@admin_required
def runners():
    runners = Runner.query.all()
    return render_template('admin/runners.html', runners=runners, calculate_age=calculate_age)

@bp.route('/runner/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_runner():
    form = RunnerForm()
    if form.validate_on_submit():
        runner = Runner(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            gender=form.gender.data,
            birth_date=form.birth_date.data,
            club=form.club.data,
            phone=form.phone.data,
            emergency_contact=form.emergency_contact.data
        )
        db.session.add(runner)
        db.session.commit()
        flash('Runner added successfully.', 'success')
        return redirect(url_for('admin_panel.runners'))
    return render_template('admin/runner_form.html', form=form, title='New Runner')

@bp.route('/runner/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_runner(id):
    runner = Runner.query.get_or_404(id)
    form = RunnerForm(obj=runner)
    if form.validate_on_submit():
        runner.first_name = form.first_name.data
        runner.last_name = form.last_name.data
        runner.email = form.email.data
        runner.gender = form.gender.data
        runner.birth_date = form.birth_date.data
        runner.club = form.club.data
        runner.phone = form.phone.data
        runner.emergency_contact = form.emergency_contact.data
        db.session.commit()
        flash('Runner updated successfully.', 'success')
        return redirect(url_for('admin_panel.runners'))
    return render_template('admin/runner_form.html', form=form, runner=runner, title='Edit Runner')

@bp.route('/runner/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_runner(id):
    runner = Runner.query.get_or_404(id)
    db.session.delete(runner)
    db.session.commit()
    flash('Runner deleted successfully.', 'success')
    return jsonify({'status': 'success'})

@bp.route('/timing')
@login_required
@admin_required
def timing_list():
    active_races = Race.query.filter_by(status='in_progress').all()
    upcoming_races = Race.query.filter_by(status='open').all()
    
    # For each race, pre-load events and convert to list to avoid AppenderQuery issue
    for race in active_races + upcoming_races:
        race.events_list = list(race.events)
    
    return render_template('admin/timing_list.html', 
                         active_races=active_races,
                         upcoming_races=upcoming_races)

@bp.route('/timing/<int:race_id>')
@login_required
@admin_required
def timing(race_id):
    race = Race.query.get_or_404(race_id)
    results = RaceResult.query.filter_by(race_id=race_id).all()
    return render_template('admin/timing.html', race=race, results=results, get_status_class=get_status_class)

@bp.route('/timing/<int:race_id>/start', methods=['POST'])
@login_required
@admin_required
def start_race(race_id):
    race = Race.query.get_or_404(race_id)
    if race.status == 'open':
        race.status = 'in_progress'
        for event in race.events:
            event.start_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Race cannot be started'}), 400

@bp.route('/timing/<int:race_id>/finish', methods=['POST'])
@login_required
@admin_required
def finish_race(race_id):
    race = Race.query.get_or_404(race_id)
    if race.status == 'in_progress':
        race.status = 'completed'
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Race cannot be finished'}), 400

@bp.route('/timing/record', methods=['POST'])
@login_required
@admin_required
def record_time():
    data = request.json
    result = RaceResult.query.filter_by(
        race_id=data['race_id'],
        bib_number=data['bib_number']
    ).first()
    
    if result:
        if data['type'] == 'finish':
            result.finish_time = datetime.utcnow()
        elif data['type'] == 'checkpoint':
            if not result.checkpoint_times:
                result.checkpoint_times = {}
            result.checkpoint_times[data['checkpoint']] = datetime.utcnow().isoformat()
        
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Runner not found'}), 404

@bp.route('/results')
@login_required
@admin_required
def results():
    completed_races = Race.query.filter_by(status='completed').all()
    return render_template('admin/results.html', races=completed_races)

@bp.route('/race/<int:race_id>/results')
@login_required
@admin_required
def race_results(race_id):
    race = Race.query.get_or_404(race_id)
    results = RaceResult.query.filter_by(race_id=race_id).order_by(RaceResult.finish_time).all()
    return render_template('admin/race_results.html', race=race, results=results)

@bp.route('/race/<int:race_id>/email', methods=['GET', 'POST'])
@login_required
@admin_required
def email_runners(race_id):
    race = Race.query.get_or_404(race_id)
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        for runner in race.runners:
            send_race_notification(runner.email, subject, message, race)
        flash('Emails sent successfully.', 'success')
        return redirect(url_for('admin_panel.races'))
    return render_template('admin/email.html', race=race)

@bp.route('/race/<int:race_id>/results/export/<format>')
@login_required
@admin_required
def export_results(race_id, format):
    race = Race.query.get_or_404(race_id)
    results = RaceResult.query.filter_by(race_id=race_id).order_by(RaceResult.finish_time).all()
    
    if format == 'excel':
        # Excel export logic
        pass
    elif format == 'pdf':
        # PDF export logic
        pass
    
    return redirect(url_for('admin_panel.race_results', race_id=race_id))

def get_status_class(status):
    classes = {
        'registered': 'secondary',
        'started': 'primary',
        'finished': 'success',
        'DNF': 'danger',
        'DNS': 'warning'
    }
    return classes.get(status, 'secondary')