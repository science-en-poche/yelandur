from flask import Flask, render_template
from flask.ext.mongoengine import MongoEngine

from yelandur.auth import auth
from yelandur.user import user
from yelandur.exp import exp


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
    app.register_blueprint(user, url_prefix=apize('/user'))
    app.register_blueprint(exp, url_prefix=apize('/exp'))

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
