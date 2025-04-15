from flask import render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.public import bp
from app.models import Race, Runner, Event, RaceResult
from app.public.forms import RaceRegistrationForm
from datetime import datetime

@bp.route('/')
def index():
    upcoming_races = Race.query.filter(
        Race.date >= datetime.utcnow()
    ).order_by(Race.date).limit(6).all()
    
    completed_races = Race.query.filter_by(status='completed').order_by(Race.date.desc()).limit(3).all()
    
    return render_template('public/index.html', 
                         featured_races=upcoming_races,
                         latest_results=completed_races)

@bp.route('/races')
def race_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'upcoming')
    
    if status == 'upcoming':
        query = Race.query.filter(Race.date >= datetime.utcnow())
    elif status == 'past':
        query = Race.query.filter(Race.date < datetime.utcnow())
    else:
        query = Race.query
    
    races = query.order_by(Race.date.desc()).paginate(
        page=page, per_page=12, error_out=False)
    
    return render_template('public/race_list.html', races=races, status=status)

@bp.route('/race/<int:id>')
def race_detail(id):
    race = Race.query.get_or_404(id)
    return render_template('public/race_detail.html', race=race)

@bp.route('/race/<int:id>/register', methods=['GET', 'POST'])
def race_register(id):
    race = Race.query.get_or_404(id)
    
    if race.date < datetime.utcnow():
        flash('Registration for this race is closed.', 'error')
        return redirect(url_for('public.race_detail', id=id))
    
    form = RaceRegistrationForm()
    # Fix the event choices here
    form.event.choices = [(str(e.id), e.name) for e in race.events]
    
    if form.validate_on_submit():
        runner = Runner(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            gender=form.gender.data,
            birth_date=form.birth_date.data if 'birth_date' in race.registration_fields else None,
            club=form.club.data if 'club' in race.registration_fields else None,
            address=form.address.data if 'address' in race.registration_fields else None,
            phone=form.phone.data if 'phone' in race.registration_fields else None,
            emergency_contact=form.emergency_contact.data if 'emergency_contact' in race.registration_fields else None
        )
        
        # Check if runner already exists
        existing_runner = Runner.query.filter_by(
            email=runner.email,
            first_name=runner.first_name,
            last_name=runner.last_name
        ).first()
        
        if existing_runner:
            runner = existing_runner
        else:
            db.session.add(runner)
        
        # Create race result
        result = RaceResult(
            race=race,
            runner=runner,
            event_id=form.event.data,
            status='registered'
        )
        
        db.session.add(result)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('public.race_detail', id=id))
    
    return render_template('public/race_register.html', race=race, form=form)

@bp.route('/race/<int:id>/results')
def race_results(id):
    race = Race.query.get_or_404(id)
    results = RaceResult.query.filter_by(race_id=id).order_by(RaceResult.finish_time).all()
    return render_template('public/race_results.html', race=race, results=results)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    races = Race.query.filter(Race.name.ilike(f'%{query}%')).all()
    return render_template('public/search_results.html', races=races, query=query)