from flask import Blueprint, abort
from flask.ext.login import login_required, current_user

from yelandur.models import User, Exp


users = Blueprint('users', __name__)


@users.route('/')
def root():
    return User.objects.to_json_public()


@users.route('/me')
@login_required
def me():
    return current_user.to_json_private()


@users.route('/<email>/')
def user(email):
    u = User.objects(email=email).first()

    if not u:
        abort(404)

    if current_user.is_authenticated() and current_user == u:
        return u.to_json_private()
    else:
        return u.to_json_public()

@users.route('/<email>/exps/')
def exps(email):
    u = User.objects(email=email).first()
    exps = Exp.objects(owner=u)

    if not u:
        abort(404)

    if current_user.is_authenticated() and current_user == u:
        return exps.to_json_private()
    else:
        return exps.to_json_public()


@users.route('/<email>/exps/<name>/')
def exp(email, name):
    u = User.objects(email=email).first()
    e = Exp.objects(name=name).first()

    if not u or not e:
        abort(404)

    if (current_user.is_authenticated() and
        (current_user == e.owner or current_user in e.collaborators)):
        return e.to_json_private()
    else:
        return e.to_json_public()


@users.route('/<email>/exps/<name>/results')
@login_required
def results(email, name):
    u = User.objects(email=email).first()
    e = Exp.objects(name=name).first()

    if not u or not e:
        abort(404)

    if current_user == e.owner or current_user in e.collaborators:
        return e.to_json_private('results')
    else:
        abort(403)
