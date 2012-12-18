from flask import Blueprint, abort, request
from flask.views import MethodView
from flask.ext.login import login_required, current_user

from mongoengine import NotUniqueError, ValidationError

from yelandur.models import User, Exp
from yelandur.helpers import jsonify


users = Blueprint('users', __name__)


@users.route('/')
def root():
    return jsonify(User.objects.to_jsonable_public())


@users.route('/me')
@login_required
def me():
    return jsonify(current_user.to_jsonable_private())


class UserView(MethodView):

    def get(self, email):
        u = User.objects(email=email).first()

        if not u:
            abort(404)

        if current_user.is_authenticated() and current_user == u:
            return jsonify(u.to_jsonable_private())
        else:
            return jsonify(u.to_jsonable_public())

    @login_required
    def put(self, email):
        raise NotImplementedError


users.add_url_rule('/<email>/', view_func=UserView.as_view('user'))


class ExpsView(MethodView):

    def get(self, email):
        u = User.objects(email=email).first()
        exps = Exp.objects(owner=u)

        if not u:
            abort(404)

        if current_user.is_authenticated() and current_user == u:
            return jsonify(exps.to_jsonable_private())
        else:
            return jsonify(exps.to_jsonable_public())

    @login_required
    def post(self, email):
        u = User.objects(email=email).first()

        if not u:
            # User not found
            abort(404)

        if current_user == u:
            form = request.form
            e = Exp(owner=u, name=form['name'], description=form['description'])
            # Errors generated here are catched by errorhandlers, see below
            e.save()
            return jsonify(e.to_jsonable_private()), 201

        else:
            # User not authorized
            abort(403)


users.add_url_rule('/<email>/exps/', view_func=ExpsView.as_view('exps'))


class ExpView(MethodView):

    def get(self, email, name):
        u = User.objects(email=email).first()
        e = Exp.objects(name=name).first()

        if not u or not e:
            abort(404)

        if (current_user.is_authenticated() and
            (current_user == e.owner or current_user in e.collaborators)):
            return jsonify(e.to_jsonable_private())
        else:
            return jsonify(e.to_jsonable_public())

    @login_required
    def put(self, email, name):
        raise NotImplementedError


users.add_url_rule('/<email>/exps/<name>/', view_func=ExpView.as_view('exp'))


@users.route('/<email>/exps/<name>/results')
@login_required
def results(email, name):
    u = User.objects(email=email).first()
    e = Exp.objects(name=name).first()

    if not u or not e:
        abort(404)

    if current_user == e.owner or current_user in e.collaborators:
        return jsonify(e.to_jsonable_private('results'))
    else:
        abort(403)


@users.errorhandler(ValidationError)
@users.errorhandler(NotUniqueError)
def insertion_error(error):
    return jsonify(status='error', message=error.message), 403
