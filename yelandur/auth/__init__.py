from flask import Blueprint, request, abort
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID
from mongoengine.queryset import NotUniqueError

from yelandur.helpers import jsonify


class BrowserIDUserMixin(object):

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.login)


def load_user_by_login(login):
    from yelandur.models import User
    return User.get_by_login(login)


def load_user_by_browserid(browserid_data):
    from yelandur.models import User
    return User.get_or_create_by_email(browserid_data.get('email'))


# Create the actual blueprint
auth = Blueprint('auth', __name__)

# Create the login manager
login_manager = LoginManager()
login_manager.user_loader(load_user_by_login)

# Create the BrowserID manager
browser_id = BrowserID()
browser_id.user_loader(load_user_by_browserid)


@auth.route('/device/register', methods=['POST'])
def register():
    """Process a public key uploaded for a device."""
    from yelandur.models import Device
    pubkey_ec = request.json.get('pubkey_ec')

    if not pubkey_ec:
        abort(400)

    device = Device.create(pubkey_ec)
    return jsonify(device.to_jsonable_private()), 201


@auth.errorhandler(NotUniqueError)
def not_unique_error(error):
    return (jsonify(status='error', type='NotUniqueError',
                    message=error.message), 406)


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
