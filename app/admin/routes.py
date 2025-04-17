from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.admin import bp
from app.models import Race, Runner, Event, RaceResult
from app.admin.forms import RaceForm, RunnerForm, EventForm, RaceRunnerForm
from app.utils.decorators import admin_required
from app.utils.email import send_race_notification
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
import json
from flask_wtf import FlaskForm


def calculate_age(birth_date):
    today = datetime.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age


@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    races_count = Race.query.count()
    runners_count = Runner.query.count()
    active_races = Race.query.filter_by(status="in_progress").count()
    recent_races = Race.query.order_by(Race.created_at.desc()).limit(5).all()

    race_stats = []
    for race in recent_races:
        results = RaceResult.query.filter_by(race_id=race.id)
        stats = {
            'race': race,
            'total': results.count(),
            'registered': results.filter_by(status='registered').count(),
            'started': results.filter_by(status='started').count(),
            'finished': results.filter_by(status='finished').count(),
            'dnf': results.filter_by(status='DNF').count(),
            'dns': results.filter_by(status='DNS').count()
        }
        race_stats.append(stats)

    return render_template(
        "admin/dashboard.html",
        races_count=races_count,
        runners_count=runners_count,
        active_races=active_races,
        race_stats=race_stats
    )


@bp.route("/races")
@login_required
@admin_required
def races():
    races = Race.query.order_by(Race.date.desc()).all()
    return render_template("admin/races.html", races=races)


@bp.route("/race/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_race():
    form = RaceForm()
    print("Method:", request.method)
    if request.method == "POST":
        print("POST data:", request.form)
        print("Form errors:", form.errors)

    if form.validate_on_submit():
        print("Form validated!")
        
        # Create race with all form data including age_groups
        race = Race(
            name=form.name.data,
            date=form.date.data,
            location=form.location.data,
            description=form.description.data,
            registration_fields=form.registration_fields.data,
            admin_id=current_user.id,
        )
        
        # Process age_groups if birth_date is selected in registration fields
        if "birth_date" in form.registration_fields.data and form.age_groups.data:
            try:
                # Validate JSON format
                json.loads(form.age_groups.data)
                race.age_groups = form.age_groups.data
                print(f"Age groups added: {race.age_groups}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON format in age groups: {e}")
                flash("Invalid JSON format in age groups", "danger")
                return render_template("admin/race_form.html", form=form, title="New Race")
        
        db.session.add(race)

        try:
            # Handle events
            print("Processing events...")
            events_data = {}

            # Process events data differently
            for key in request.form:
                if key.startswith("events["):
                    # Extract event number and field name
                    # events[0][name] -> ['events', '0', 'name']
                    parts = key.replace("]", "").replace("[", " ").split()
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
                    name=event_data["name"],
                    distance=float(event_data["distance"]),
                    has_checkpoints=bool(event_data.get("has_checkpoints", False)),
                    number_of_laps=int(event_data.get("laps", 1)),
                )
                race.events.append(event)
                print(f"Added event: {event_data}")

            db.session.commit()
            print("Database committed!")
            flash("Race created successfully.", "success")
            return redirect(url_for("admin_panel.races"))
        except Exception as e:
            print(f"Error creating race: {str(e)}")
            db.session.rollback()
            flash("Error creating race.", "error")
    else:
        print("Form validation failed:", form.errors)

    return render_template("admin/race_form.html", form=form, title="New Race")

@bp.route("/race/<int:id>/edit", methods=["GET", "POST"])
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

        # Only process age_groups if birth_date is selected
        if "birth_date" in form.registration_fields.data and form.age_groups.data:
            try:
                # Validate JSON format
                json.loads(form.age_groups.data)
                race.age_groups = form.age_groups.data
                print(f"Age groups updated: {race.age_groups}")
            except json.JSONDecodeError:
                flash("Invalid JSON format in age groups", "danger")
                return render_template("admin/race_form.html", form=form, race=race, title="Edit Race")
        else:
            # Clear age_groups if birth_date is not selected
            race.age_groups = None
            print("Age groups cleared (birth_date not selected)")

        # Handle events would go here

        db.session.commit()
        flash("Race updated", "success")
        # Fix the redirect to use the correct endpoint
        return redirect(url_for("admin_panel.races"))

    # Pre-fill form with existing JSON
    if race.age_groups:
        form.age_groups.data = race.age_groups
        
    return render_template(
        "admin/race_form.html", form=form, race=race, title="Edit Race"
    )


@bp.route("/race/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_race(id):
    race = Race.query.get_or_404(id)
    db.session.delete(race)
    db.session.commit()
    flash("Race deleted successfully.", "success")
    return jsonify({"status": "success"})


@bp.route("/runners")
@login_required
@admin_required
def runners():
    runners = Runner.query.all()
    return render_template(
        "admin/runners.html", runners=runners, calculate_age=calculate_age
    )


@bp.route("/runner/new", methods=["GET", "POST"])
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
            emergency_contact=form.emergency_contact.data,
        )
        db.session.add(runner)
        db.session.commit()
        flash("Runner added successfully.", "success")
        return redirect(url_for("admin_panel.runners"))
    return render_template("admin/runner_form.html", form=form, title="New Runner")


@bp.route("/runner/<int:id>/edit", methods=["GET", "POST"])
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
        flash("Runner updated successfully.", "success")
        return redirect(url_for("admin_panel.runners"))
    return render_template(
        "admin/runner_form.html", form=form, runner=runner, title="Edit Runner"
    )


@bp.route("/runner/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_runner(id):
    runner = Runner.query.get_or_404(id)
    db.session.delete(runner)
    db.session.commit()
    flash("Runner deleted successfully.", "success")
    return jsonify({"status": "success"})


@bp.route("/timing")
@login_required
@admin_required
def timing_list():
    active_races = Race.query.filter_by(status="in_progress").all()
    upcoming_races = Race.query.filter_by(status="open").all()

    for race in active_races + upcoming_races:
        race.events_list = list(race.events)
        race.runners_count = RaceResult.query.filter_by(race_id=race.id).count()

    return render_template(
        "admin/timing_list.html",
        active_races=active_races,
        upcoming_races=upcoming_races,
    )



@bp.route("/timing/<int:race_id>")
@login_required
@admin_required
def timing(race_id):
    race = Race.query.get_or_404(race_id)
    results = RaceResult.query.filter_by(race_id=race_id).all()
    return render_template(
        "admin/timing.html",
        race=race,
        results=results,
        get_status_class=get_status_class,
    )


@bp.route("/timing/<int:race_id>/start", methods=["POST"])
@login_required
@admin_required
def start_race(race_id):
    race = Race.query.get_or_404(race_id)

    if race.status == "open":
        race.status = "in_progress"
        current_time = datetime.utcnow()

        for event in race.events:
            event.start_time = current_time

            # Set start_time for all runners in this event
            for result in event.results:
                result.start_time = current_time

        db.session.commit()
        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Race cannot be started"}), 400


@bp.route("/timing/<int:race_id>/finish", methods=["POST"])
@login_required
@admin_required
def finish_race(race_id):
    race = Race.query.get_or_404(race_id)
    if race.status == "in_progress":
        race.status = "completed"
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Race cannot be finished"}), 400


@bp.route("/timing/record", methods=["POST"])
@login_required
@admin_required
def record_time():
    data = request.get_json()
    
    # Validate input
    if not data or 'race_id' not in data or 'bib_number' not in data:
        return jsonify({"status": "error", "message": "Missing required data"}), 400

    try:
        race = Race.query.get_or_404(data['race_id'])
        result = RaceResult.query.filter_by(
            race_id=race.id,
            bib_number=data['bib_number']
        ).first_or_404()

        # Initialize lap times if needed
        if result.lap_times is None:
            result.lap_times = []

        # Record current lap
        current_time = datetime.utcnow()
        result.lap_times.append(current_time.isoformat())

        # Get the event to check laps (since laps are defined at event level)
        event = Event.query.get(result.event_id)
        
        # Check completion (with explicit lap check)
        if len(result.lap_times) >= event.number_of_laps:
            result.finish_time = current_time
            result.status = "finished"
            message = "Runner has finished the race"
        else:
            result.status = "started"
            message = f"Lap {len(result.lap_times)} recorded"

        db.session.commit()
        return jsonify({
            "status": "success",
            "message": message,
            "current_lap": len(result.lap_times),
            "total_laps": event.number_of_laps
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Timing error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/results")
@login_required
@admin_required
def results():
    completed_races = Race.query.filter_by(status="completed").all()
    return render_template("admin/results.html", races=completed_races)

@bp.route("/timing/<int:race_id>/results")
@login_required
@admin_required
def get_race_results(race_id):
    race = Race.query.get_or_404(race_id)
    results = RaceResult.query.filter_by(race_id=race_id).all()

    # Serialize results
    results_data = []
    for r in results:
        results_data.append({
            "id": r.id,
            "runner_name": r.runner.name,
            "bib_number": r.bib_number,
            "status": r.status,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "finish_time": r.finish_time.isoformat() if r.finish_time else None,
            "lap_times": r.lap_times or []
        })

    return jsonify(results_data)

@bp.route("/race/<int:race_id>/results")
@login_required
@admin_required
def race_results(race_id):
    import json
    from datetime import datetime, timedelta
    
    race = Race.query.get_or_404(race_id)
    
    # Get all events for this race without eager loading
    events = Event.query.filter_by(race_id=race_id).all()
    
    # Define helper functions for the template
    def calculate_average_time(results):
        # Filter out results with no finish time
        valid_results = [r for r in results if r.finish_time and r.start_time]
        
        if not valid_results:
            return "N/A"
        
        # Calculate average time
        total_seconds = sum((r.finish_time - r.start_time).total_seconds() for r in valid_results)
        avg_seconds = total_seconds / len(valid_results)
        
        # Format as HH:MM:SS
        hours, remainder = divmod(avg_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def get_age_group(birth_date):
        if not birth_date or not race.age_groups:
            return "N/A"
        
        # Calculate age on race day
        race_date = race.date.date()
        age = race_date.year - birth_date.year
        
        # Adjust age if birthday hasn't occurred yet this year
        if (birth_date.month, birth_date.day) > (race_date.month, race_date.day):
            age -= 1
            
        # Parse age groups from JSON string
        try:
            age_groups = json.loads(race.age_groups)
        except (json.JSONDecodeError, TypeError):
            return "N/A"
            
        # Find matching age group
        for group in age_groups:
            if group.get("min") <= age <= group.get("max"):
                return group.get("label")
                
        return "Other"  # Fallback if no matching group
    
    def get_category_position(result):
        if not result or not result.finish_time or not result.runner or not result.runner.birth_date:
            return "-"
            
        # Get age group
        age_group = get_age_group(result.runner.birth_date)
        if age_group == "N/A" or age_group == "Other":
            return "-"
            
        # Get gender
        gender = result.runner.gender
        
        # Get all finished results for the same event
        all_results = [r for r in result.event.results 
                      if r.status == 'finished' and r.finish_time]
        
        # Filter results by age group and gender
        category_results = [r for r in all_results 
                           if get_age_group(r.runner.birth_date) == age_group 
                           and r.runner.gender == gender]
        
        # Sort by finish time
        category_results.sort(key=lambda r: r.finish_time)
        
        # Find position of current result
        for i, r in enumerate(category_results):
            if r.id == result.id:
                return i + 1  # +1 because positions start at 1, not 0
                
        return "-"  # Should not happen if result is in the list
    
    def get_status_class(status):
        classes = {
            "registered": "secondary",
            "started": "primary",
            "finished": "success",
            "DNF": "danger",
            "DNS": "warning",
        }
        return classes.get(status, "secondary")
    
    # Organize results by event
    event_results = {}
    for event in events:
        # Fetch results for each event
        results = sorted(event.results, key=lambda r: r.finish_time or datetime.max)
        event_results[event] = {
            'results': results,
            'count': len(results)
        }
    
    return render_template(
        "admin/race_results.html",
        race=race,
        events=events,
        event_results=event_results,
        calculate_average_time=calculate_average_time,
        get_age_group=get_age_group,
        get_category_position=get_category_position,
        get_status_class=get_status_class
    )


@bp.route("/race/<int:race_id>/email", methods=["GET", "POST"])
@login_required
@admin_required
def email_runners(race_id):
    race = Race.query.get_or_404(race_id)
    if request.method == "POST":
        subject = request.form.get("subject")
        message = request.form.get("message")
        for runner in race.runners:
            send_race_notification(runner.email, subject, message, race)
        flash("Emails sent successfully.", "success")
        return redirect(url_for("admin_panel.races"))
    return render_template("admin/email.html", race=race)


@bp.route("/race/<int:race_id>/results/export/<format>")
@login_required
@admin_required
def export_results(race_id, format):
    race = Race.query.get_or_404(race_id)
    results = (
        RaceResult.query.filter_by(race_id=race_id)
        .order_by(RaceResult.finish_time)
        .all()
    )

    if format == "excel":
        # Excel export logic
        pass
    elif format == "pdf":
        # PDF export logic
        pass

    return redirect(url_for("admin_panel.race_results", race_id=race_id))

@bp.route("/race/<int:race_id>/runners")
@login_required
@admin_required
def race_runners(race_id):
    race = Race.query.get_or_404(race_id)
    
    # Get all race results for this race
    results = RaceResult.query.filter_by(race_id=race_id).all()
    
    return render_template(
        "admin/race_runners.html", 
        race=race,
        results=results,
        calculate_age=calculate_age,
        get_status_class=get_status_class
    )

@bp.route("/race/<int:race_id>/runner/<int:runner_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_race_runner(race_id, runner_id):
    race = Race.query.get_or_404(race_id)
    runner = Runner.query.get_or_404(runner_id)
    
    # Get the race result entry for this runner in this race
    result = RaceResult.query.filter_by(
        race_id=race_id,
        runner_id=runner_id
    ).first_or_404()
    
    # Use your existing form
    form = RaceRunnerForm()
    
    # Check if race has t-shirt registration field
    has_shirt_size = race.registration_fields and "shirt_size" in race.registration_fields
    
    if form.validate_on_submit():
        # Update runner details
        runner.first_name = form.first_name.data
        runner.last_name = form.last_name.data
        runner.birth_date = form.birth_date.data
        runner.club = form.club.data
        
        # Update result details (bib number)
        result.bib_number = form.bib_number.data
        
        db.session.commit()
        flash("Runner information updated successfully", "success")
        return redirect(url_for("admin_panel.race_runners", race_id=race_id))
    
    # Pre-populate form with existing data
    form.first_name.data = runner.first_name
    form.last_name.data = runner.last_name
    form.bib_number.data = result.bib_number
    form.birth_date.data = runner.birth_date
    form.club.data = runner.club
    
    return render_template(
        "admin/race_runner_form.html", 
        form=form, 
        race=race,
        runner=runner,
        result=result,
        has_shirt_size=has_shirt_size,
        title="Edit Runner"
    )

def get_status_class(status):
    classes = {
        "registered": "secondary",
        "started": "primary",
        "finished": "success",
        "DNF": "danger",
        "DNS": "warning",
    }
    return classes.get(status, "secondary")
