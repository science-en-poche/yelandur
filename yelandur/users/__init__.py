from flask import Blueprint, abort, request
from flask.views import MethodView
from flask.ext.login import login_required, current_user

from mongoengine import NotUniqueError, ValidationError
from mongoengine.queryset import DoesNotExist

from yelandur.models import User, Exp, LoginSetError
from yelandur.helpers import jsonify


users = Blueprint('users', __name__)


class RootView(MethodView):

    def get(self):
        return jsonify(User.objects.to_jsonable_public())

    @login_required
    def put(self):
        current_user.set_login(request.form['login'])
        current_user.save()
        return jsonify(current_user.to_jsonable_private())


users.add_url_rule('/', view_func=RootView.as_view('root'))


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
            return jsonify(u.to_jsonable_public())


users.add_url_rule('/<login>/', view_func=UserView.as_view('user'))


class ExpsView(MethodView):

    def get(self, login):
        u = User.objects.get(login=login)
        exps = Exp.objects(owner=u)

        if current_user.is_authenticated() and current_user == u:
            return jsonify(exps.to_jsonable_private())
        else:
            return jsonify(exps.to_jsonable_public())

    @login_required
    def post(self, login):
        u = User.objects.get(login=login)

        if current_user == u:
            form = request.form
            # Errors generated here are caught by errorhandlers, see below
            e = Exp(owner=u, name=form['name'], description=form['description'])
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
            return jsonify(e.to_jsonable_public())

    @login_required
    def put(self, login, name):
        u = User.objects.get(login=login)
        e = Exp.objects(owner=u).get(name=name)

        if current_user == e.owner or current_user in e.collaborators:
            e.description = request.form['description']
            e.save()
            return jsonify(e.to_jsonable_private())

        else:
            # User not authorized
            abort(403)


users.add_url_rule('/<login>/exps/<name>/', view_func=ExpView.as_view('exp'))


@users.route('/<login>/exps/<name>/results')
@login_required
def results(login, name):
    u = User.objects.get(login=login)
    e = Exp.objects(owner=u).get(name=name)

    if current_user == e.owner or current_user in e.collaborators:
        return jsonify(e.to_jsonable_private('results'))
    else:
        abort(403)


@users.errorhandler(ValidationError)
@users.errorhandler(NotUniqueError)
@users.errorhandler(LoginSetError)
def insertion_error(error):
    return jsonify(status='error', message=error.message), 403


@users.errorhandler(DoesNotExist)
def does_not_exist(error):
    abort(404)
