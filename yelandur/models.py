import re
from datetime import datetime
import json

import mongoengine as mge
from mongoengine.queryset import DoesNotExist
from mongoengine.base import BaseDocument

from yelandur.auth import BrowserIDUserMixin


class EmptyException(BaseException):
    pass


class JSONMixin(object):

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

    def _append_summary(self, type_string):
        out = type_string
        if not re.search('_summary$', type_string):
            out += '_summary'

        return out

    def _summarize(self, type_string, attr):
        if isinstance(attr, BaseDocument):
            return attr._to_jsonable(self._append_summary(type_string))
        elif isinstance(attr, list):
            return [self._summarize(type_string, item) for item in attr]
        elif isinstance(attr, datetime):
            return attr.strftime('%d/%m/%Y-%H:%M:%S')
        else:
            return attr

    def _insert_summary(self, type_string, res, inc):
        attr = self.__getattribute__(inc)
        try:
            res[inc] = self._summarize(type_string, attr)
        except EmptyException:
            pass

    def _insert_count(self, res, inc):
        res[inc] = len(self.__getattribute__(self._get_count_string(inc)))

    def _insert_regexp(self, type_string, res, inc):
        regexp = self._get_regexp_string(inc)

        for attr_name in self.to_mongo().iterkeys():
            if re.search(regexp, attr_name):
                self._insert_summary(type_string, res, attr_name)

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
                self._insert_summary(type_string, res, inc)

        return res

    def _build_to_json(self, type_string):
        def _to_json(self):
            try:
                return json.dumps(self._to_jsonable(type_string))
            except EmptyException:
                return ''
        # Return bound method
        return _to_json.__get__(self, JSONMixin)

    def __getattribute__(self, name):
        if (len(name) >= 4 and name[:3] == 'to_'
            and self.__contains__(name[2:])):
            return self._build_to_json(name[2:])
        else:
            return object.__getattribute__(self, name)


class User(mge.Document,BrowserIDUserMixin,JSONMixin):

    _json_private_summary = ['email', 'name']
    _json_private = ['email', 'name', 'exps']
    _json_public_summary = ['email', 'name']
    _json_public = ['email', 'name', '#exps']

    email = mge.EmailField(required=True, unique=True, min_length=3,
                           max_length=50)
    name = mge.StringField(max_length=50)
    exps = mge.ListField(mge.ReferenceField('Exp', dbref=True))

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

    _json_private_summary = ['created_at', 'device']
    _json_private = ['created_at', 'device', r'/^[^_][a-zA-Z0-9]*$/']
    _json_public_summary = []
    _json_public = []

    created_at = mge.DateTimeField(default=datetime.now,
                                   required=True)
    device = mge.ReferenceField('Device', required=True, dbref=True)


class Exp(mge.Document,JSONMixin):

    _json_private_summary = ['name', 'description', '#results']
    _json_private = ['name', 'description', 'owner', 'collaborators', 'results']
    _json_public_summary = ['name', 'description', '#results']
    _json_public = ['name', 'description', 'owner', 'collaborators', '#results']

    name = mge.StringField(regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$',
                           required=True, unique=True,
                           min_length=3, max_length=50)
    description = mge.StringField(max_length=300)
    owner = mge.ReferenceField('User', required=True, dbref=True)
    collaborators = mge.ListField(mge.ReferenceField('User', dbref=True))
    results = mge.ListField(mge.EmbeddedDocumentField('Result'))


class Device(mge.Document,JSONMixin):

    _json_private_summary = ['device_id']
    _json_private = ['device_id', 'pubkey_ec']
    _json_public_summary = []
    _json_public = []

    device_id = mge.StringField(regex='^[a-zA-Z0-9]+$', required=True,
                                unique=True, min_length=3, max_length=150)
    pubkey_ec = mge.StringField(required=True, max_length=5000)
