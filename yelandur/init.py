from flask import Flask
from flask.ext.mongoengine import MongoEngine

from .auth import auth
from .users import users
from .devices import devices


def create_apizer(app):
    def apize(url):
        return app.config['API_VERSION_URL'] + url
    return apize


def create_app(mode=None):
    # Create app
    app = Flask(__name__)
    _mode = '_' + mode if mode else ''
    app.config.from_pyfile('settings{}.py'.format(_mode))
    apize = create_apizer(app)

    # Link to database
    MongoEngine(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix=apize('/auth'))
    app.register_blueprint(users, url_prefix=apize('/users'))
    app.register_blueprint(devices, url_prefix=apize('/devices'))

    return app
