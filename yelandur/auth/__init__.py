import os
#import time

from flask import Blueprint#, request, abort
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID
#from flask.ext.uploads import (UploadSet, configure_uploads,
                               #patch_request_class)

#import yelandur.auth.crypto as crypto
#from yelandur.models import Device


class BrowserIDUserMixin(object):

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.name)


def load_user_by_login(login):
    from yelandur.models import User
    return User.get_by_login(login)


def load_user_by_browserid(browserid_data):
    from yelandur.models import User
    return User.get_or_create_by_email(browserid_data.get('email'))


def file_allowed(upload_set, f):
    return upload_set.file_allowed(f, os.path.basename(f.filename))


#def generate_device_id():
    #found = False

    #for i in range(50):
        #device_id = crypto.sha256_hash_hex(str(request.headers) +
                                           #str(time.time()))
        #if Device.objects(device_id=device_id).count() == 0:
            #found = True
            #break

    #if not found:
        #raise Exception('could not generate a device_id')

    #return device_id


# Create the actual blueprint
auth = Blueprint('auth', __name__)

# Create the login manager
login_manager = LoginManager()
login_manager.user_loader(load_user_by_login)

# Create the BrowserID manager
browser_id = BrowserID()
browser_id.user_loader(load_user_by_browserid)

# Create the upload set
#dest = lambda app: os.path.join(app.root_path, 'uploads')
#us_pubkey = UploadSet('pubkey', 'pub', default_dest=dest)


#@auth.route('/device/register', methods=['POST'])
#def register():
    #"""Process a public key uploaded for a device."""
    #pubkeyfile = request.files['pubkeyfile']

    #if not pubkeyfile:
        #abort(400)

    #if not file_allowed(us_pubkey, pubkeyfile):
        #abort(400)

    #device_id = generate_device_id()
    #device = Device(device_id=device_id,
                    #pubkey_ec=pubkeyfile.read())
    #device.save()

    #return device_id


def configure_app(setup_state):
    app = setup_state.app
    url_prefix = setup_state.url_prefix

    # Configure login manager
    login_manager.init_app(app)

    # Configure BrowserID manager
    app.config['BROWSERID_LOGIN_URL'] = url_prefix + '/browserid/login'
    app.config['BROWSERID_LOGOUT_URL'] = url_prefix + '/browserid/logout'
    browser_id.init_app(app)

    # Configure upload set
    #configure_uploads(app, (us_pubkey,))
    #patch_request_class(app, app.config['MAX_CONTENT_LENGTH'])


auth.record_once(configure_app)
