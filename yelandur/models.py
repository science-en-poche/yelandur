import re
from datetime import datetime
import json

import mongoengine as mge
from mongoengine.queryset import DoesNotExist, QuerySet
from mongoengine.base import BaseDocument

from yelandur.auth import BrowserIDUserMixin


class EmptyException(BaseException):
    pass


class JSONQuerySet(QuerySet):

    def _to_jsonable(self, type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(type_string))

        return res

    def _build_to_json(self, type_string):
        def _to_json(self):
            try:
                return json.dumps(self._to_jsonable(type_string))
            except EmptyException:
                return ''
        # Return bound method
        return _to_json.__get__(self, JSONQuerySet)

    def __getattribute__(self, name):
        # Catch 'to_*' calls, but don't test for existence of the method
        # as is done in JSONMixin
        if len(name) >= 4 and name[:3] == 'to_':
            return self._build_to_json(name[2:])
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
        return s[0] == '#'

    def _get_count_string(self, s):
        if not self._is_count(s):
            raise ValueError('string does not represent a count')
        return s[1:]

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
        except EmptyException:
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
            raise EmptyException

        for inc in includes:

            if self._is_regexp(inc):
                self._insert_regexp(type_string, res, inc)
            elif self._is_count(inc):
                self._insert_count(res, inc)
            else:
                self._insert_jsonable(type_string, res, inc)

        return res

    def _build_to_json(self, type_string):
        def _to_json(self, attr_name=None):
            try:
                if attr_name is None:
                    return json.dumps(self._to_jsonable(type_string))
                else:
                    attr = self.__getattribute__(attr_name)
                    return json.dumps(self._jsonablize(type_string, attr))
            except EmptyException:
                return ''
        # Return bound method
        return _to_json.__get__(self, JSONMixin)

    def __getattribute__(self, name):
        # Catch 'to_*' calls
        if (len(name) >= 4 and name[:3] == 'to_'
            and self.__contains__(name[2:])):
            return self._build_to_json(name[2:])
        else:
            return object.__getattribute__(self, name)


class User(mge.Document,BrowserIDUserMixin,JSONMixin):

    meta = {'ordering': ['name']}

    _json_private = ['email', 'name']
    _json_public = ['email', 'name']

    email = mge.EmailField(required=True, unique=True, min_length=3,
                           max_length=50)
    name = mge.StringField(max_length=50)

    @classmethod
    def get(cls, email):
        try:
            return User.objects.get(email=email)
        except DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, email):
        return User.objects.get_or_create(email=email,
                                          defaults={'email': email},
                                          auto_save=True)[0]


class Result(mge.DynamicEmbeddedDocument,JSONMixin):

    meta = {'ordering': ['created_at']}

    _json_private = ['created_at', 'device', r'/^[^_][a-zA-Z0-9]*$/']
    _json_public = []

    created_at = mge.DateTimeField(default=datetime.now,
                                   required=True)
    device = mge.ReferenceField('Device', required=True, dbref=False)


class Exp(mge.Document,JSONMixin):

    meta = {'ordering': ['name']}

    _json_private = ['name', 'description', 'owner', 'collaborators', '#results']
    _json_public = ['name', 'description', 'owner', 'collaborators', '#results']

    name = mge.StringField(regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$',
                           required=True, unique=True,
                           min_length=3, max_length=50)
    description = mge.StringField(max_length=300)
    owner = mge.ReferenceField('User', required=True, dbref=False)
    collaborators = mge.ListField(mge.ReferenceField('User', dbref=False))
    results = mge.ListField(mge.EmbeddedDocumentField('Result'))


class Device(mge.Document,JSONMixin):

    meta = {'ordering': ['device_id']}

    _json_private = ['device_id']
    _json_public = []

    device_id = mge.StringField(regex='^[a-zA-Z0-9]+$', required=True,
                                unique=True, min_length=3, max_length=150)
    pubkey_ec = mge.StringField(required=True, max_length=5000)
