# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.mongoengine import MongoEngine

from .auth import auth
from .users import users
from .exps import exps
from .devices import devices
from .profiles import profiles
from .results import results
from .session import ItsdangerousSessionInterface

import settings_base


def create_apizer(app):
    def apize(url):
        return app.config['API_VERSION_URL'] + url
    return apize


def create_app(mode='dev'):
    # Create app
    app = Flask(__name__)
    settings_file = 'settings_{}.py'.format(mode)
    app.config.from_object(settings_base)
    app.config.from_pyfile(settings_file)
    apize = create_apizer(app)

    # Link to database
    MongoEngine(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix=apize('/auth'))
    app.register_blueprint(users, url_prefix=apize('/users'))
    app.register_blueprint(exps, url_prefix=apize('/exps'))
    app.register_blueprint(devices, url_prefix=apize('/devices'))
    app.register_blueprint(profiles, url_prefix=apize('/profiles'))
    app.register_blueprint(results, url_prefix=apize('/results'))

    # Change session interface
    app.session_interface = ItsdangerousSessionInterface()

    return app
