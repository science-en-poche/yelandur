from flask import Blueprint, abort
from flask.ext.login import login_required, current_user

from yelandur.models import User


user = Blueprint('user', __name__)


@user.route('/me')
@login_required
def me():
    return current_user.to_json_private()


@user.route('/<email>')
def user_data(email):
    u = User.objects(email=email).first()

    if not u:
        abort(404)

    if current_user.is_authenticated() and current_user == u:
        return u.to_json_private()
    else:
        return u.to_json_public()
