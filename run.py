from app import create_app, db
from app.models import User, Race, Runner, Event, RaceResult

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Race': Race,
        'Runner': Runner,
        'Event': Event,
        'RaceResult': RaceResult
    }

if __name__ == '__main__':
    app.run(debug=True)