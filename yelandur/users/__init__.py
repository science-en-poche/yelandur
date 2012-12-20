from flask import Blueprint, abort, request
from flask.views import MethodView
from flask.ext.login import login_required, current_user
from mongoengine import NotUniqueError, ValidationError
from mongoengine.queryset import DoesNotExist

from yelandur.models import User, Exp, LoginSetError
from yelandur.helpers import jsonify


users = Blueprint('users', __name__)


@users.route('/')
def root():
    # No POST method here since users are created through BrowserID only
    return jsonify(User.objects.to_jsonable())


@users.route('/me')
@login_required
def me():
    return jsonify(current_user.to_jsonable_private())


class UserView(MethodView):

    def get(self, login):
        u = User.objects.get(login=login)

        if current_user.is_authenticated() and current_user == u:
            return jsonify(u.to_jsonable_private())
        else:
            return jsonify(u.to_jsonable())

    @login_required
    def put(self, login):
        u = User.objects.get(login=login)

        if current_user == u:
            # Errors generated here are caught by errorhandlers, see below
            u.set_login(request.json['login'])
            u.save()
            return jsonify(u.to_jsonable_private())
        else:
            # User not authorized
            abort(403)


users.add_url_rule('/<login>', view_func=UserView.as_view('user'))


class ExpsView(MethodView):

    def get(self, login):
        u = User.objects.get(login=login)
        exps = Exp.objects(owner=u)

        if current_user.is_authenticated() and current_user == u:
            return jsonify(exps.to_jsonable_private())
        else:
            return jsonify(exps.to_jsonable())

    @login_required
    def post(self, login):
        u = User.objects.get(login=login)

        if current_user == u:
            name = request.json.get('name') or request.json.get('name_claim')
            description = request.json.get('description')
            # Errors generated here are caught by errorhandlers, see below
            e = Exp.create(name, u, description)
            e.save()
            return jsonify(e.to_jsonable_private()), 201
        else:
            # User not authorized
            abort(403)


users.add_url_rule('/<login>/exps/', view_func=ExpsView.as_view('exps'))


class ExpView(MethodView):

    def get(self, login, name):
        u = User.objects.get(login=login)
        e = Exp.objects(owner=u).get(name=name)

        if (current_user.is_authenticated() and
            (current_user == e.owner or current_user in e.collaborators)):
            return jsonify(e.to_jsonable_private())
        else:
            return jsonify(e.to_jsonable())

    @login_required
    def put(self, login, name):
        u = User.objects.get(login=login)
        e = Exp.objects(owner=u).get(name=name)

        if current_user == e.owner or current_user in e.collaborators:
            if name != request.json['name']:
                abort(400)
            e.description = request.json['description']
            e.save()
            return jsonify(e.to_jsonable_private())
        else:
            # User not authorized
            abort(403)


users.add_url_rule('/<login>/exps/<name>', view_func=ExpView.as_view('exp'))


@users.route('/<login>/exps/<name>/results/')
@login_required
def results(login, name):
    # No POST method here since results are added by devices only
    u = User.objects.get(login=login)
    e = Exp.objects(owner=u).get(name=name)

    if current_user == e.owner or current_user in e.collaborators:
        return jsonify(e.to_jsonable_private('results'))
    else:
        abort(403)


@users.errorhandler(ValidationError)
def validation_error(error):
    return jsonify(status='error', type='ValidationError', message=error.message), 403


@users.errorhandler(NotUniqueError)
def not_unique_error(error):
    return jsonify(status='error', type='NotUniqueError', message=error.message), 403


@users.errorhandler(LoginSetError)
def login_set_error(error):
    return jsonify(status='error', type='LoginSetError', message=error.message), 403


@users.errorhandler(DoesNotExist)
def does_not_exist(error):
    abort(404)
