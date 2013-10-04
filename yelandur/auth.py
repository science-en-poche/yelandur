# -*- coding: utf-8 -*-

from flask import Blueprint, request, abort
from flask.ext.login import LoginManager, login_user, logout_user
from flask.ext.browserid import BrowserID

from .cors import cors, add_cors_headers


def load_user_by_user_id(user_id):
    from yelandur.models import User
    return User.get(user_id)


def load_user_by_browserid(browserid_data):
    from yelandur.models import User
    return User.get_or_create_by_email(browserid_data.get('email'))


# Create the actual blueprint
auth = Blueprint('auth', __name__)

# Create the login manager
login_manager = LoginManager()
login_manager.user_loader(load_user_by_user_id)

# Create the BrowserID manager
browser_id = BrowserID()
browser_id.user_loader(load_user_by_browserid)

# Add the after-request CORS-adding function
browser_id.views.after_request(add_cors_headers)


@cors()
def debug_login():
    from yelandur.models import User
    try:
        user_id = request.args['id']
        u = User.get(user_id)
        if not u:
            abort(404)
        login_user(u)
        return "Logged '{}' in".format(user_id)
    except KeyError:
        abort(400)


@cors()
def debug_logout():
    logout_user()
    return 'Logged user out'


@auth.record_once
def configure_app(setup_state):
    app = setup_state.app
    url_prefix = setup_state.url_prefix

    # Configure login manager
    login_manager.init_app(app)

    # Configure BrowserID manager
    app.config['BROWSERID_LOGIN_URL'] = url_prefix + '/browserid/login'
    app.config['BROWSERID_LOGOUT_URL'] = url_prefix + '/browserid/logout'
    browser_id.init_app(app)

    # Add debug urls if necessary
    if app.config['DEBUG']:
        auth.add_url_rule('/debug/login', view_func=debug_login)
        auth.add_url_rule('/debug/logout', view_func=debug_logout)


class BrowserIDUserMixin(object):

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.user_id)
