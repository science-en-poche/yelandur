# -*- coding: utf-8 -*-

import unittest
import re

from mongoengine import ValidationError, NotUniqueError
from mongoengine.base import ObjectId

from . import create_app, helpers, models


class UserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_constraints_missing_field(self):
        # A user with no user_id, or no persona_email, or no gravatar_id,
        # is wrong
        u = models.User()
        u.user_id = 'abc'
        u.persona_email = 'johndoe@example.com'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.user_id = 'abc'
        u.gravatar_id = 'fff'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.persona_email = 'johndoe@example.com'
        u.gravatar_id = 'fff'
        self.assertRaises(ValidationError, u.save)

        # But with all of those, it's ok
        u = models.User()
        u.user_id = 'abc'
        u.persona_email = 'johndoe@example.com'
        u.gravatar_id = 'fff'
        # No exception here
        u.save()
        self.assertIsInstance(u.id, ObjectId)

    def test_constraints_format(self):
        # `user_id` must follow certain rules
        u = models.User()
        u.persona_email = 'johndoe@example.com'
        u.gravatar_id = 'fff'
        # Can't start with a number
        u.user_id = '3abc'
        self.assertRaises(ValidationError, u.save)
        # Can't end with a -
        u.user_id = 'abc-'
        self.assertRaises(ValidationError, u.save)
        # Can't end with a _
        u.user_id = 'abc_'
        self.assertRaises(ValidationError, u.save)
        # Can't start with a -
        u.user_id = '-abc'
        self.assertRaises(ValidationError, u.save)
        # Can't start with a _
        u.user_id = '_abc'
        self.assertRaises(ValidationError, u.save)
        # Must be at least two characters long
        u.user_id = 'a'
        self.assertRaises(ValidationError, u.save)
        # Can't have awkward characters
        u.user_id = 'abcé'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'abéc'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'abc@'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'ab@c'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'abc)'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'ab)c'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'abc/'
        self.assertRaises(ValidationError, u.save)
        u.user_id = 'ab/c'
        self.assertRaises(ValidationError, u.save)
        # But can have _ and - in the middle
        u.user_id = 'abc_-what4ver56'
        u.save()
        self.assertIsInstance(u.id, ObjectId)

        # `persona_email` must be an email
        u = models.User()
        u.user_id = 'abc'
        u.peronsa_email = 'johndoeexample.com'
        u.gravatar_id = 'fff'
        self.assertRaises(ValidationError, u.save)

        # `gravatar_id` must hexadecimal
        u = models.User()
        u.user_id = 'abc'
        u.persona_email = 'johndoe@example.com'
        u.gravatar_id = 'fffg'
        self.assertRaises(ValidationError, u.save)

    def test_constraints_unique_user_id(self):
        # `user_id` must be unique
        u1 = models.User()
        u1.user_id = 'aaa'
        u1.persona_email = 'johndoe1@example.com'
        u1.gravatar_id = 'fff'
        u1.save()

        u2 = models.User()
        u2.user_id = 'aaa'
        u2.persona_email = 'johndoe2@example.com'
        u2.gravatar_id = 'fff'
        self.assertRaises(NotUniqueError, u2.save)

    def test_constraints_unique_persona_email(self):
        # `user_id` must be unique
        u1 = models.User()
        u1.user_id = 'seb'
        u1.persona_email = 'seb@example.com'
        u1.gravatar_id = 'fff'
        u1.save()

        u2 = models.User()
        u2.user_id = 'toad'
        u2.persona_email = 'seb@example.com'
        u2.gravatar_id = 'fff'
        self.assertRaises(NotUniqueError, u2.save)

    def test_set_user_id(self):
        # set_user_id works, and `user_id` can only be set once
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        self.assertFalse(u.user_id_is_set)
        u.set_user_id('seb-login')
        self.assertTrue(u.user_id_is_set)
        self.assertEquals(u.user_id, 'seb-login')
        self.assertRaises(models.UserIdSetError, u.set_user_id,
                          'new-login')
        self.assertEquals(u.user_id, 'seb-login')

    def test_get(self):
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.save()
        # Getting an existing user works
        self.assertEquals(models.User.get('seb'), u)
        # Getting a non-exiting user returns None
        self.assertIsNone(models.User.get('non-existing'))

    def test_get_by_email(self):
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.save()
        # Getting an existing user works
        self.assertEquals(models.User.get_by_email('seb@example.com'), u)
        # Getting a non-exiting user returns None
        self.assertIsNone(models.User.get_by_email('no@example.com'))

    def test_get_or_create_by_email(self):
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.save()
        # Getting an existing user works
        self.assertEquals(
            models.User.get_or_create_by_email('seb@example.com'), u)
        # Getting an non-existing user creates it
        ug = models.User.get_or_create_by_email('no@example.com')
        self.assertIsInstance(ug, models.User)
        self.assertIsInstance(ug.id, ObjectId)
        self.assertFalse(ug.user_id_is_set)
        self.assertEquals(ug.user_id[:3], 'no-')
        self.assertTrue(re.search(helpers.hexregex, ug.user_id[3:]))
