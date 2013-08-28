# -*- coding: utf-8 -*-

from flask import Blueprint
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID

from .cors import add_cors_headers


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


class BrowserIDUserMixin(object):

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.user_id)
