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
        # Can't be more than 50 characters long
        u.user_id = 'abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmno'
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
        u.user_id = 'seb-tmp'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.save()
        self.assertFalse(u.user_id_is_set)
        u.set_user_id('seb-login')
        self.assertTrue(u.user_id_is_set)
        self.assertEquals(u.user_id, 'seb-login')
        # `user_id` can't be set again
        self.assertRaises(models.UserIdSetError, u.set_user_id,
                          'new-login')
        self.assertEquals(u.user_id, 'seb-login')
        # The model wasn't saved automatically
        fu = models.User.get_by_email('seb@example.com')
        self.assertEquals(fu.user_id, 'seb-tmp')
        # But saving sets it
        u.save()
        fu = models.User.get_by_email('seb@example.com')
        self.assertEquals(fu.user_id, 'seb-login')

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


class ExpTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

        # Two users with a set `user_id`
        self.u1 = models.User(user_id='seb-tmp',
                              persona_email='seb@example.com',
                              gravatar_id='fff')
        self.u1.set_user_id('seb')
        self.u1.save()
        self.u2 = models.User(user_id='toad-tmp',
                              persona_email='toad@example.com',
                              gravatar_id='eee')
        self.u2.set_user_id('toad')
        self.u2.save()

        # A user with a non-set `user_id`
        self.nu = models.User(user_id='nonset-tmp',
                              persona_email='nonset@example.com',
                              gravatar_id='ddd')
        self.nu.save()

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_constraints_missing_field(self):
        # An exp with no exp_id, or no name, or no owner is wrong
        e = models.Exp()
        e.exp_id = 'abc'
        e.name = 'after-motion-effet'
        self.assertRaises(ValidationError, e.save)

        e = models.Exp()
        e.exp_id = 'abc'
        e.owner = self.u1
        self.assertRaises(ValidationError, e.save)

        e = models.Exp()
        e.name = 'after-motion-effet'
        e.owner = self.u1
        self.assertRaises(ValidationError, e.save)

        # But with all of those, it's ok
        e = models.Exp()
        e.exp_id = 'abc'
        e.name = 'after-motion-effet'
        e.owner = self.u1
        # No exception here
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_format(self):
        # `name` must follow certain rules
        e = models.Exp()
        e.exp_id = 'abcdef'
        e.owner = self.u1
        # Can't start with a number
        e.name = '3abc'
        self.assertRaises(ValidationError, e.save)
        # Can't end with a -
        e.name = 'abc-'
        self.assertRaises(ValidationError, e.save)
        # Can't end with a _
        e.name = 'abc_'
        self.assertRaises(ValidationError, e.save)
        # Can't start with a -
        e.name = '-abc'
        self.assertRaises(ValidationError, e.save)
        # Can't start with a _
        e.name = '_abc'
        self.assertRaises(ValidationError, e.save)
        # Must be at least three characters long
        e.name = 'ab'
        self.assertRaises(ValidationError, e.save)
        # Can't be more than 50 characters long
        e.name = 'abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmno'
        self.assertRaises(ValidationError, e.save)
        # Can't have awkward characters
        e.name = 'abcé'
        self.assertRaises(ValidationError, e.save)
        e.name = 'abéc'
        self.assertRaises(ValidationError, e.save)
        e.name = 'abc@'
        self.assertRaises(ValidationError, e.save)
        e.name = 'ab@c'
        self.assertRaises(ValidationError, e.save)
        e.name = 'abc)'
        self.assertRaises(ValidationError, e.save)
        e.name = 'ab)c'
        self.assertRaises(ValidationError, e.save)
        e.name = 'abc/'
        self.assertRaises(ValidationError, e.save)
        e.name = 'ab/c'
        self.assertRaises(ValidationError, e.save)
        # But can have _ and - in the middle
        e.name = 'abc_-what4ver56'
        e.save()
        self.assertIsInstance(e.id, ObjectId)

        # `exp_id` must hexadecimal
        e = models.Exp()
        e.exp_id = 'abcg'
        e.name = 'after-motion-effet'
        e.owner = self.u1
        self.assertRaises(ValidationError, e.save)

    def test_constraints_unique_exp_id(self):
        # `exp_id` must be unique
        e1 = models.Exp()
        e1.exp_id = 'abc'
        e1.name = 'after-motion-effet'
        e1.owner = self.u1
        e1.save()

        e2 = models.Exp()
        e2.exp_id = 'abc'
        e2.name = 'after-motion-effet-two'
        e2.owner = self.u1
        self.assertRaises(NotUniqueError, e2.save)

    def test_constraints_unique_name_with_owner(self):
        # `owner` in conjunction with `name` are unique
        e1 = models.Exp()
        e1.exp_id = 'abc1'
        e1.name = 'after-motion-effet'
        e1.owner = self.u1
        e1.save()

        e2 = models.Exp()
        e2.exp_id = 'abc2'
        e2.name = 'after-motion-effet'
        e2.owner = self.u1
        self.assertRaises(NotUniqueError, e2.save)
        # Changing the owner makes the save possible
        e2.owner = self.u2
        e2.save()
        self.assertIsInstance(e2.id, ObjectId)

    def test_build_exp_id(self):
        # Two example tests
        exp_name = 'after-motion-effect'
        self.assertEquals(models.Exp.build_exp_id(exp_name, self.u1),
                          '9e182dac9b384935658c18854abbc76166224bea7216242cd'
                          '26833318b18500d')
        self.assertNotEqual(models.Exp.build_exp_id(exp_name, self.u2),
                            '9e182dac9b384935658c18854abbc76166224bea7216242cd'
                            '26833318b18500d')

    def test_create(self):
        e = models.Exp.create('after-motion-effect', self.u1,
                              'The experiment', [self.u2])
        # The exp is created and saved with the right values
        self.assertIsInstance(e.id, ObjectId)
        self.assertEquals(e.exp_id, '9e182dac9b384935658c18854abbc76166224be'
                          'a7216242cd26833318b18500d')
        self.assertEquals(e.owner, self.u1)
        self.assertEquals(e.description, 'The experiment')
        self.assertEquals(len(e.collaborators), 1)
        self.assertEquals(e.collaborators[0], self.u2)

        # And the users concerned have been updated
        self.assertIn(e, self.u1.exps)
        self.assertIn(e, self.u2.exps)

        # But creating an exp involving a user who's id is not set does
        # not work.
        self.assertRaises(models.UserIdSetError, models.Exp.create,
                          'after-motion-effect-2', self.nu)
        self.assertRaises(models.UserIdSetError, models.Exp.create,
                          'after-motion-effect-2', self.u1,
                          collaborators=[self.nu])

        # Finally, setting the owner in the collaborators does not work
        self.assertRaises(ValueError, models.Exp.create,
                          'after-motion-effect-2', self.u1,
                          collaborators=[self.u1, self.u2])
