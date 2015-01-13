# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler, StreamHandler
import sys

from flask import Flask
from flask.ext.mongoengine import MongoEngine
from raven.contrib.flask import Sentry

from .auth import auth
from .users import users
from .exps import exps
from .devices import devices
from .profiles import profiles
from .results import results

import settings_base


sentry = Sentry()


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

    # Set up logging
    if 'LOG_FILE' in app.config:
        handler = RotatingFileHandler(app.config['LOG_FILE'],
                                      maxBytes=10 * 1024 * 1024,
                                      backupCount=5)
    else:
        handler = StreamHandler(sys.stdout)
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))

    # Initialize Sentry
    sentry.init_app(app)

    # Link to database
    MongoEngine(app)

    # Register blueprints
    app.register_blueprint(auth, url_prefix=apize('/auth'))
    app.register_blueprint(users, url_prefix=apize('/users'))
    app.register_blueprint(exps, url_prefix=apize('/exps'))
    app.register_blueprint(devices, url_prefix=apize('/devices'))
    app.register_blueprint(profiles, url_prefix=apize('/profiles'))
    app.register_blueprint(results, url_prefix=apize('/results'))

    return app
