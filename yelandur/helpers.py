import re
from datetime import datetime
from hashlib import md5

from flask.helpers import jsonify as flask_jsonify
from flask.helpers import json
from flask import current_app, request
from mongoengine.queryset import QuerySet
from mongoengine.base import BaseDocument


def build_gravatar_id(email):
    m = md5()
    m.update(email)
    return m.hexdigest()


def jsonify(*args, **kwargs):
    """Allow arrays to be jsonified (since ECMAScript 5 fixes the array
    security hole)."""
    if len(args) > 0 and type(args[0]) == list:
        return current_app.response_class(json.dumps(args[0],
            indent=None if request.is_xhr else 2), mimetype='application/json')
    else:
        return flask_jsonify(*args, **kwargs)


class EmptyJsonableException(BaseException):
    pass


class JSONQuerySet(QuerySet):

    def _to_jsonable(self, type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(type_string))

        return res

    def _build_to_jsonable(self, type_string):
        def to_jsonable(self):
            try:
                return self._to_jsonable(type_string)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONQuerySet)

    def __getattribute__(self, name):
        # Catch 'to_*' calls, but don't test for existence of the method
        # as is done in JSONMixin
        if len(name) >= 4 and name[:3] == 'to_':
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)


class JSONMixin(object):

    meta = {'queryset_class': JSONQuerySet}

    def _is_regexp(self, s):
        return s[0] == '/' and s[-1] == '/'

    def _get_regexp_string(self, s):
        if not self._is_regexp(s):
            raise ValueError('string does not represent a regexp')
        return s[1:-1]

    def _is_count(self, s):
        return s[:2] == 'n_'

    def _get_count_string(self, s):
        if not self._is_count(s):
            raise ValueError('string does not represent a count')
        return s[2:]

    def _jsonablize(self, type_string, attr):
        if isinstance(attr, BaseDocument):
            return attr._to_jsonable(type_string)
        elif isinstance(attr, list):
            return [self._jsonablize(type_string, item) for item in attr]
        elif isinstance(attr, datetime):
            return attr.strftime('%d/%m/%Y-%H:%M:%S')
        else:
            return attr

    def _insert_jsonable(self, type_string, res, inc):
        attr = self.__getattribute__(inc)
        try:
            res[inc] = self._jsonablize(type_string, attr)
        except EmptyJsonableException:
            pass

    def _insert_count(self, res, inc):
        res[inc] = len(self.__getattribute__(self._get_count_string(inc)))

    def _insert_regexp(self, type_string, res, inc):
        regexp = self._get_regexp_string(inc)

        for attr_name in self.to_mongo().iterkeys():
            if re.search(regexp, attr_name):
                self._insert_jsonable(type_string, res, attr_name)

    def _to_jsonable(self, type_string):
        res = {}
        includes = self.__getattribute__(type_string)

        if len(includes) == 0:
            raise EmptyJsonableException

        for inc in includes:

            if self._is_regexp(inc):
                self._insert_regexp(type_string, res, inc)
            elif self._is_count(inc):
                self._insert_count(res, inc)
            else:
                self._insert_jsonable(type_string, res, inc)

        return res

    def _build_to_jsonable(self, type_string):
        def to_jsonable(self, attr_name=None):
            try:
                if attr_name is None:
                    return self._to_jsonable(type_string)
                else:
                    attr = self.__getattribute__(attr_name)
                    return self._jsonablize(type_string, attr)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONMixin)

    def __getattribute__(self, name):
        # Catch 'to_*' calls
        if (len(name) >= 4 and name[:3] == 'to_'
            and self.__contains__(name[2:])):
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)
