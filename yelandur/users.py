# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user, logout_user, login_user
from mongoengine import NotUniqueError, ValidationError
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import User, UserIdSetError, UserIdReservedError


# Create the actual blueprint
users = Blueprint('users', __name__)


class MissingRequirementError(Exception):
    pass


class RequestMalformedError(Exception):
    pass


@users.route('')
@cors()
def root():
    # No POST method here since users are created through BrowserID only

    # Private access
    if request.args.get('access', None) == 'private':
        if not current_user.is_authenticated():
            abort(401)

        # The only user current_user has access to is himself
        rusers = User.objects(user_id=current_user.user_id)

        if 'ids[]' in request.args:
            ids = request.args.getlist('ids[]')
            if current_user.user_id not in ids:
                # Override with an empty result set
                rusers = User.objects(user_id=None)

        limit = request.args.get('limit')
        limit = int(limit) if limit is not None else None
        orders = User.objects.translate_order_to_jsonable_private(
            request.args)
        filtered_query = User.objects.translate_to_jsonable_private(
            request.args)
        rusers = rusers(**filtered_query).order_by(*orders)
        rusers = rusers.limit(limit) if limit is not None else rusers

        return jsonify({'users': rusers.to_jsonable_private()})

    # Public access
    if 'ids[]' in request.args:
        ids = request.args.getlist('ids[]')
        rusers = User.objects(user_id__in=ids)
    else:
        rusers = User.objects()

    limit = request.args.get('limit')
    limit = int(limit) if limit is not None else None
    orders = User.objects.translate_order_to_jsonable(request.args)
    filtered_query = User.objects.translate_to_jsonable(request.args)
    rusers = rusers(**filtered_query).order_by(*orders)
    rusers = rusers.limit(limit) if limit is not None else rusers

    return jsonify({'users': rusers.to_jsonable()})


@users.route('/me')
@cors()
def me():
    if not current_user.is_authenticated():
        abort(401)
    return jsonify({'user': current_user.to_jsonable_private()})


class UserView(MethodView):

    @cors()
    def get(self, user_id):
        u = User.objects.get(user_id=user_id)

        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if u.user_id == current_user.user_id:
                return jsonify({'user': u.to_jsonable_private()})
            else:
                abort(403)
        else:
            return jsonify({'user': u.to_jsonable()})

    @cors()
    def put(self, user_id):
        u = User.objects.get(user_id=user_id)

        if not current_user.is_authenticated():
            abort(401)

        user_dict = request.json.get('user', None)
        if user_dict is None:
            raise RequestMalformedError

        claimed_user_id = user_dict.get('id', None)
        if claimed_user_id is None:
            raise MissingRequirementError

        if u.user_id == current_user.user_id:
            u.set_user_id(claimed_user_id)

            # Logout and login
            logout_user()
            login_user(u)

            return jsonify({'user': u.to_jsonable_private()})
        else:
            # Authenticated as another user
            abort(403)

    @cors()
    def options(self, user_id):
        pass


users.add_url_rule('/<user_id>', view_func=UserView.as_view('user'))


@users.errorhandler(ValidationError)
@cors()
def validation_error(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'BadSyntax',
                   'message': ('A field does not fulfill '
                               'the required syntax')}}), 400


@users.errorhandler(NotUniqueError)
@cors()
def not_unique_error(error):
    return jsonify(
        {'error': {'status_code': 409,
                   'type': 'FieldConflict',
                   'message': 'The value is already taken'}}), 409


@users.errorhandler(UserIdReservedError)
@cors()
def reserved_error(error):
    return jsonify(
        {'error': {'status_code': 409,
                   'type': 'UserIdReserved',
                   'message': 'The claimed user_id is reserved'}}), 409


@users.errorhandler(UserIdSetError)
@cors()
def user_id_set_error(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'UserIdSet',
                   'message': 'user_id has already been set'}}), 403


@users.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404


@users.errorhandler(MissingRequirementError)
@cors()
def missing_requirement(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'MissingRequirement',
                   'message': 'One of the required fields is missing'}}), 400


@users.errorhandler(400)
@users.errorhandler(RequestMalformedError)
@cors()
def malformed(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@users.errorhandler(401)
@cors()
def unauthenticated(error):
    return jsonify(
        {'error': {'status_code': 401,
                   'type': 'Unauthenticated',
                   'message': 'Request requires authentication'}}), 401


@users.errorhandler(403)
@cors()
def unauthorized(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'Unauthorized',
                   'message': ('You do not have access '
                               'to this resource')}}), 403
