import re
from datetime import datetime
from hashlib import md5, sha256
import random
import time

from flask.helpers import jsonify as flask_jsonify
from flask.helpers import json
from flask import current_app, request
from mongoengine.queryset import QuerySet
import pymongo
from ecdsa.util import sigdecode_der, sigencode_string


hexregex = r'^[0-9a-f]*$'


def md5hex(s):
    return md5(s).hexdigest()


def sha256hex(s):
    return sha256(s).hexdigest()


def random_md5hex():
    random.seed(time.time())
    return md5hex(str(random.random()))


def random_sha256hex():
    random.seed(time.time())
    return sha256hex(str(random.random()))


def sig_der_to_string(sig, order):
    r, s = sigdecode_der(sig, order)
    return sigencode_string(r, s, order)


def build_gravatar_id(email):
    return md5hex(email)


def drop_test_database():
    if not current_app.config['TESTING']:
        raise ValueError('TESTING mode not activated for the app.'
                         " I won't risk wiping a production database.")

    if not current_app.config['MONGODB_DB'][-5:] == '_test':
        raise ValueError("MONGODB_DB does not end with '_test'."
                         " I won't risk wiping a production database.")

    c = pymongo.Connection()
    c.drop_database(current_app.config['MONGODB_DB'])
    c.close()


def jsonify(*args, **kwargs):
    """Allow arrays to be jsonified (since ECMAScript 5 fixes the array
    security hole)."""
    if len(args) > 0 and type(args[0]) == list:
        return current_app.response_class(
            json.dumps(args[0], indent=None if request.is_xhr else 2),
            mimetype='application/json')
    else:
        return flask_jsonify(*args, **kwargs)


class EmptyJsonableException(BaseException):
    pass


class JSONQuerySet(QuerySet):

    def _to_jsonable(self, pre_type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(pre_type_string))

        return res

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self):
            try:
                return self._to_jsonable(pre_type_string)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONQuerySet)

    def __getattribute__(self, name):
        # Catch 'to_*' calls, but don't test for existence of the method
        # as is done in JSONMixin
        if name != 'to_mongo' and len(name) >= 4 and name[:3] == 'to_':
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)


class JSONMixin(object):

    meta = {'queryset_class': JSONQuerySet}

    def _is_regex(self, s):
        return len(s) >= 3 and s[0] == '/' and s[-1] == '/'

    def _get_regex_string(self, s):
        if not self._is_regex(s):
            raise ValueError('string does not represent a regex')
        return s[1:-1]

    def _is_count(self, s):
        return len(s) >= 3 and s[:2] == 'n_'

    def _get_count_string(self, s):
        if not self._is_count(s):
            raise ValueError('string does not represent a count')
        return s[2:]

    def _get_includes(self, type_string):
        if not re.search('^(_[a-zA-Z][a-zA-Z0-9]*)+$', type_string):
            raise ValueError('bad type_string format')

        parts = type_string.split('_')
        includes = []
        for i in xrange(2, len(parts) + 1):
            current = '_'.join(parts[:i])
            try:
                includes.extend(self.__getattribute__(current))
            except AttributeError:
                continue
        return includes

    @classmethod
    def _parse_preinc(cls, preinc):
        return preinc if type(preinc) == tuple else (preinc, preinc)

    def _find_type_string(self, pre_type_string):
        parts = pre_type_string.split('_')
        for i in reversed(xrange(2, len(parts) + 1)):
            current = '_'.join(parts[:i])
            try:
                self.__getattribute__(current)
                return current
            except AttributeError:
                continue
        raise AttributeError(
            "no parent found for '{}'".format(pre_type_string))

    def _insert_jsonable(self, type_string, res, inc):
        attr = self.__getattribute__(inc[0])
        try:
            res[inc[1]] = self._jsonablize(type_string, attr)
        except EmptyJsonableException:
            pass

    def _insert_count(self, res, inc):
        res[inc[1]] = len(self.__getattribute__(
            self._get_count_string(inc[0])))

    def _insert_regex(self, type_string, res, inc):
        regex = self._get_regex_string(inc[0])

        for attr_name in self.__dict__.iterkeys():
            r = re.search(regex, attr_name)
            if r:
                self._insert_jsonable(type_string, res,
                                      (attr_name, r.expand(inc[1])))

    def _to_jsonable(self, pre_type_string):
        res = {}
        type_string = self._find_type_string(pre_type_string)
        includes = self._get_includes(type_string)

        if len(includes) == 0:
            raise EmptyJsonableException

        for preinc in includes:

            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                self._insert_regex(type_string, res, inc)
            elif self._is_count(inc[0]):
                self._insert_count(res, inc)
            else:
                self._insert_jsonable(type_string, res, inc)

        return res

    @classmethod
    def _jsonablize(cls, type_string, attr):
        if isinstance(attr, JSONMixin):
            return attr._to_jsonable(type_string)
        elif isinstance(attr, list):
            return [cls._jsonablize(type_string, item) for item in attr]
        elif isinstance(attr, datetime):
            return attr.strftime('%d/%m/%Y at %H:%M:%S')
        else:
            return attr

    def __getattribute__(self, name):
        # Catch 'to_*' calls
        if (name != 'to_mongo' and len(name) >= 4 and name[:3] == 'to_'
                and name[2:] in self.__dict__):
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self, attr_name=None):
            try:
                if attr_name is None:
                    return self._to_jsonable(pre_type_string)
                else:
                    attr = self.__getattribute__(attr_name)
                    return self._jsonablize(pre_type_string, attr)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONMixin)
