from flask import Flask, render_template
from flask.ext.login import LoginManager, login_required, current_user
from flask.ext.browserid import BrowserID


app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.config['BROWSERID_LOGIN_URL'] = '/api/auth/browserid/login'
app.config['BROWSERID_LOGOUT_URL'] = '/api/auth/browserid/logout'


class User(object):

    _userids = set(['seblerique@wanadoo.fr', 'john', 'smith', 'vanessa'])
    _cached_users = {}

    def __init__(self, userid):
        self.userid = userid

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.userid)

    @classmethod
    def get(cls, userid):
        print 'userid', userid
        if not userid in cls._userids:
            return None

        if not cls._cached_users.has_key(userid):
            cls._cached_users[userid] = User(userid)

        return cls._cached_users[userid]


def load_user_by_id(userid):
    return User.get(userid)


def load_user(browserid_data):
    return load_user_by_id(browserid_data.get('email'))


login_manager = LoginManager()
login_manager.user_loader(load_user_by_id)
login_manager.setup_app(app)

browser_id = BrowserID()
browser_id.user_loader(load_user)
browser_id.init_app(app)


@app.route('/api/me')
@login_required
def me():
    return '{{"userId": "{}"}}'.format(current_user.userid)


@app.route('/')
def index():
    return render_template('index.html')
