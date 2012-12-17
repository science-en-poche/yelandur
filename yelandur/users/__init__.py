from flask import Blueprint, abort, request
from flask.views import MethodView
from flask.ext.login import login_required, current_user

from mongoengine import NotUniqueError, ValidationError

from yelandur.models import User, Exp


users = Blueprint('users', __name__)


@users.route('/')
def root():
    return User.objects.to_json_public()


@users.route('/me')
@login_required
def me():
    return current_user.to_json_private()


class UserView(MethodView):

    def get(self, email):
        u = User.objects(email=email).first()

        if not u:
            abort(404)

        if current_user.is_authenticated() and current_user == u:
            return u.to_json_private()
        else:
            return u.to_json_public()

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
            return exps.to_json_private()
        else:
            return exps.to_json_public()

    @login_required
    def post(self, email):
        u = User.objects(email=email).first()

        if not u:
            # User not found
            abort(404)

        if current_user == u:
            form = request.form
            try:
                e = Exp(owner=u, name=form['name'], description=form['description'])
                e.save()
            except ValidationError:
                abort(403)
            except NotUniqueError:
                abort(403)

            return (e.to_json_private(), 201)

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
            return e.to_json_private()
        else:
            return e.to_json_public()

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
        return e.to_json_private('results')
    else:
        abort(403)
