from flask import Flask, render_template
from flask.ext.mongoengine import MongoEngine

from yelandur.auth import auth
from yelandur.users import users


def create_apizer(app):
    def apize(url):
        return app.config['API_VERSION_URL'] + url
    return apize


def create_app():
    # Create app
    app = Flask(__name__)
    app.config.from_pyfile('settings.py')
    apize = create_apizer(app)

    # Link to database
    MongoEngine(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix=apize('/auth'))
    app.register_blueprint(users, url_prefix=apize('/users'))

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
