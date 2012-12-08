from flask import Blueprint
from flask.ext.login import login_required, current_user


user = Blueprint('user', __name__)


@user.route('/me')
@login_required
def me():
    return '{{"userId": "{}"}}'.format(current_user.email)


#@user.route('/<email>')
#def user(email):

