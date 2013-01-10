from flask import Flask
from flask.ext.mongoengine import MongoEngine

from yelandur.auth import auth
from yelandur.users import users
from yelandur.devices import devices


def create_apizer(app):
    def apize(url):
        return app.config['API_VERSION_URL'] + url
    return apize


def create_app(mode=None):
    # Create app
    app = Flask(__name__)
    app.config.from_pyfile('settings_{}.py'.format(mode))
    apize = create_apizer(app)

    # Link to database
    MongoEngine(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix=apize('/auth'))
    app.register_blueprint(users, url_prefix=apize('/users'))
    app.register_blueprint(devices, url_prefix=apize('/devices'))

    return app
