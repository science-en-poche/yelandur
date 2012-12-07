from flask import Blueprint
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID



class BrowserIDUserMixin(object):

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.email)


def load_user_by_email(email):
    from yelandur.models import User
    return User.get(email)


def load_user_by_browserid(browserid_data):
    from yelandur.models import User
    return User.get_or_create(browserid_data.get('email'))


def configure_app(setup_state):
    app = setup_state.app
    url_prefix = setup_state.url_prefix

    login_manager = LoginManager()
    login_manager.user_loader(load_user_by_email)
    login_manager.init_app(app)

    app.config['BROWSERID_LOGIN_URL'] = url_prefix + '/browserid/login'
    app.config['BROWSERID_LOGOUT_URL'] = url_prefix + '/browserid/logout'
    browser_id = BrowserID()
    browser_id.user_loader(load_user_by_browserid)
    browser_id.init_app(app)


auth = Blueprint('auth', __name__)
auth.record_once(configure_app)
