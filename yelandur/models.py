from datetime import datetime

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from yelandur.auth import BrowserIDUserMixin
from yelandur.helpers import build_gravatar_id, JSONMixin


class User(mge.Document,BrowserIDUserMixin,JSONMixin):

    meta = {'ordering': ['name']}

    _jsonable_private = ['email', 'name', 'gravatar_id']
    _jsonable_public = ['email', 'name', 'gravatar_id']

    email = mge.EmailField(required=True, unique=True, min_length=3,
                           max_length=50)
    name = mge.StringField(max_length=50)
    gravatar_id = mge.StringField()

    def update_gravatar_id(self):
        self.gravatar_id = build_gravatar_id(self.email)
        self.save()

    @classmethod
    def get(cls, email):
        try:
            return User.objects.get(email=email)
        except DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, email):
        u = User.objects.get_or_create(email=email,
                                       defaults={'email': email},
                                       auto_save=True)[0]
        if not u.gravatar_id:
            u.update_gravatar_id()
        return u


class Result(mge.DynamicEmbeddedDocument,JSONMixin):

    meta = {'ordering': ['created_at']}

    _jsonable_private = ['created_at', 'device', r'/^[^_][a-zA-Z0-9]*$/']
    _jsonable_public = []

    created_at = mge.DateTimeField(default=datetime.now,
                                   required=True)
    device = mge.ReferenceField('Device', required=True, dbref=False)


class Exp(mge.Document,JSONMixin):

    meta = {'ordering': ['name']}

    _jsonable_private = ['name', 'description', 'owner', 'collaborators', 'n_results']
    _jsonable_public = ['name', 'description', 'owner', 'collaborators', 'n_results']

    name = mge.StringField(regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$',
                           required=True, unique=True,
                           min_length=3, max_length=50)
    description = mge.StringField(max_length=300)
    owner = mge.ReferenceField('User', required=True, dbref=False)
    collaborators = mge.ListField(mge.ReferenceField('User', dbref=False))
    results = mge.ListField(mge.EmbeddedDocumentField('Result'))


class Device(mge.Document,JSONMixin):

    meta = {'ordering': ['device_id']}

    _jsonable_private = ['device_id']
    _jsonable_public = []

    device_id = mge.StringField(regex='^[a-zA-Z0-9]+$', required=True,
                                unique=True, min_length=3, max_length=150)
    pubkey_ec = mge.StringField(required=True, max_length=5000)
