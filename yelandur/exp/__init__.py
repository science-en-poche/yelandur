from flask import Blueprint, abort
from flask.ext.login import current_user

from yelandur.models import Exp


exp = Blueprint('exp', __name__)


@exp.route('/<name>')
def exp_data(name):
    e = Exp.objects(name=name).first()

    if not e:
        abort(404)

    if (current_user.is_authenticated() and
        (current_user == e.owner or current_user in e.collaborators)):
        return e.to_json_private()
    else:
        return e.to_json_public()
