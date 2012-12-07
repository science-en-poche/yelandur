from flask import Flask, render_template
from flask.ext.login import login_required, current_user
from flask.ext.mongoengine import MongoEngine

from yelandur.auth import auth


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

    # Register auth blueprint
    app.register_blueprint(auth, url_prefix=apize('/auth'))

    @app.route(apize('/users/me'))
    @login_required
    def me():
        return '{{"userId": "{}"}}'.format(current_user.email)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
