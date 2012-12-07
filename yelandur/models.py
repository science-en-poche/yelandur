from datetime import datetime

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from yelandur.auth import BrowserIDUserMixin


class User(mge.Document,BrowserIDUserMixin):

    email = mge.EmailField(required=True, unique=True, min_length=3,
                           max_length=50)
    name = mge.StringField(max_length=50)
    exps = mge.ListField(mge.ReferenceField('Exp'))

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


class Result(mge.DynamicEmbeddedDocument):

    created_at = mge.DateTimeField(default=datetime.now,
                                   required=True)
    device = mge.ReferenceField('Device', required=True)


class Exp(mge.Document):

    name = mge.StringField(regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$',
                           required=True, unique=True,
                           min_length=3, max_length=50)
    description = mge.StringField(max_length=300)
    owner = mge.ReferenceField('User', required=True)
    collaborators = mge.ListField(mge.ReferenceField('User'))
    results = mge.ListField(mge.EmbeddedDocumentField('Result'))


class Device(mge.Document):

    deviceid = mge.StringField(regex='^[a-zA-Z0-9]+$', required=True,
                               unique=True, min_length=3, max_length=150)
    pubkey_ec = mge.StringField(required=True, max_length=5000)
