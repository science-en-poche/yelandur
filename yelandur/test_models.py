# -*- coding: utf-8 -*-

import unittest
from datetime import datetime

from mongoengine import ValidationError, NotUniqueError
from bson.objectid import ObjectId

from . import create_app, helpers, models


# Often, before modifying a model, you will encounter a model.reload()
# call. This is a workaround for bug
# https://github.com/MongoEngine/mongoengine/issues/237 whose fix
# doesn't seem to be included in our mongoengine 0.8.2. The fix comes
# from
# http://stackoverflow.com/questions/16725340.


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

    def test_constraints_user_id(self):
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

    def test_constraints_persona_email(self):
        # `persona_email` must be an email
        u = models.User()
        u.user_id = 'abc'
        u.peronsa_email = 'johndoeexample.com'
        u.gravatar_id = 'fff'
        self.assertRaises(ValidationError, u.save)

    def test_constraints_gravatar_id(self):
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

    def test_contraints_exp_ids(self):
        # `exp_ids` must be hexadecimal
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.exp_ids = ['ffg']
        self.assertRaises(ValidationError, u.save)

        u.exp_ids = ['fff']
        u.save()
        self.assertIsInstance(u.id, ObjectId)

    def test_contraints_profile_ids(self):
        # `profile_ids` must be hexadecimal
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.profile_ids = ['ffg']
        self.assertRaises(ValidationError, u.save)

        u.profile_ids = ['fff']
        u.save()
        self.assertIsInstance(u.id, ObjectId)

    def test_contraints_device_ids(self):
        # `device_ids` must be hexadecimal
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.device_ids = ['ffg']
        self.assertRaises(ValidationError, u.save)

        u.device_ids = ['fff']
        u.save()
        self.assertIsInstance(u.id, ObjectId)

    def test_contraints_result_ids(self):
        # `result_ids` must be hexadecimal
        u = models.User()
        u.user_id = 'seb'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.result_ids = ['ffg']
        self.assertRaises(ValidationError, u.save)

        u.result_ids = ['fff']
        u.save()
        self.assertIsInstance(u.id, ObjectId)

    def test_set_user_id(self):
        # set_user_id works, and `user_id` can only be set once
        u = models.User()
        u.user_id = 'seb-tmp'
        u.persona_email = 'seb@example.com'
        u.gravatar_id = 'fff'
        u.save()
        self.assertFalse(u.user_id_is_set)
        # User_id can't be a reserved name
        self.assertRaises(models.UserIdReservedError, u.set_user_id, 'new')
        self.assertRaises(models.UserIdReservedError, u.set_user_id,
                          'settings')
        # Set user_id
        u.set_user_id('seb-login')
        self.assertTrue(u.user_id_is_set)
        self.assertEquals(u.user_id, 'seb-login')
        # `user_id` can't be set again
        self.assertRaises(models.UserIdSetError, u.set_user_id,
                          'new-login')
        self.assertEquals(u.user_id, 'seb-login')
        # The model was saved automatically
        u.reload()
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
        self.assertRegexpMatches(ug.user_id[3:], helpers.hexregex)


class ExpTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

        # Two users with a set `user_id`
        self.u1 = models.User(user_id='seb-tmp',
                              persona_email='seb@example.com',
                              gravatar_id='fff')
        self.u1.set_user_id('seb')
        self.u2 = models.User(user_id='toad-tmp',
                              persona_email='toad@example.com',
                              gravatar_id='eee')
        self.u2.set_user_id('toad')

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
        e.owner_id = self.u1.user_id
        self.assertRaises(ValidationError, e.save)

        e = models.Exp()
        e.name = 'after-motion-effet'
        e.owner_id = self.u1.user_id
        self.assertRaises(ValidationError, e.save)

        # But with all of those, it's ok
        e = models.Exp()
        e.exp_id = 'abc'
        e.name = 'after-motion-effet'
        e.owner_id = self.u1.user_id
        # No exception here
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_name(self):
        # `name` must follow certain rules
        e = models.Exp()
        e.exp_id = 'abcdef'
        e.owner_id = self.u1.user_id
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

    def test_constraints_exp_id(self):
        # `exp_id` must hexadecimal
        e = models.Exp()
        e.exp_id = 'abcg'
        e.name = 'after-motion-effet'
        e.owner_id = self.u1.user_id
        self.assertRaises(ValidationError, e.save)

    def test_constraints_description(self):
        # `description`` can't be too long
        e = models.Exp()
        e.exp_id = 'abc'
        e.name = 'after-motion-effet'
        e.owner_id = self.u1.user_id
        e.description = 'a' * 301
        self.assertRaises(ValidationError, e.save)
        e.description = '&' * 300
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_unique_exp_id(self):
        # `exp_id` must be unique
        e1 = models.Exp()
        e1.exp_id = 'abc'
        e1.name = 'after-motion-effet'
        e1.owner_id = self.u1.user_id
        e1.save()

        e2 = models.Exp()
        e2.exp_id = 'abc'
        e2.name = 'after-motion-effet-two'
        e2.owner_id = self.u1.user_id
        self.assertRaises(NotUniqueError, e2.save)

    def test_constraints_unique_name_with_owner_id(self):
        # `owner` in conjunction with `name` are unique
        e1 = models.Exp()
        e1.exp_id = 'abc1'
        e1.name = 'after-motion-effet'
        e1.owner_id = self.u1.user_id
        e1.save()

        e2 = models.Exp()
        e2.exp_id = 'abc2'
        e2.name = 'after-motion-effet'
        e2.owner_id = self.u1.user_id
        self.assertRaises(NotUniqueError, e2.save)
        # Changing the owner makes the save possible
        e2.owner_id = self.u2.user_id
        e2.save()
        self.assertIsInstance(e2.id, ObjectId)

    def test_constraints_owner_id(self):
        # `owner_id` must be a name
        e = models.Exp()
        e.exp_id = 'abc1'
        e.name = 'after-motion-effect'
        e.owner_id = '_seb'
        self.assertRaises(ValidationError, e.save)

        e.owner_id = 'seb'
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_collaborator_ids(self):
        # `collaborator_ids` must be names
        e = models.Exp()
        e.exp_id = 'abc1'
        e.name = 'after-motion-effect'
        e.owner_id = 'seb'
        e.collaborator_ids = ['_a']
        self.assertRaises(ValidationError, e.save)

        e.collaborator_ids = ['vincent']
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_device_ids(self):
        # `device_ids` must be hexadecimal
        e = models.Exp()
        e.exp_id = 'abc1'
        e.name = 'after-motion-effect'
        e.owner_id = 'seb'
        e.device_ids = ['ffg']
        self.assertRaises(ValidationError, e.save)

        e.device_ids = ['fff']
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_profile_ids(self):
        # `profile_ids` must be hexadecimal
        e = models.Exp()
        e.exp_id = 'abc1'
        e.name = 'after-motion-effect'
        e.owner_id = 'seb'
        e.profile_ids = ['ffg']
        self.assertRaises(ValidationError, e.save)

        e.profile_ids = ['fff']
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_constraints_result_ids(self):
        # `result_ids` must be hexadecimal
        e = models.Exp()
        e.exp_id = 'abc1'
        e.name = 'after-motion-effect'
        e.owner_id = 'seb'
        e.profile_ids = ['ffg']
        self.assertRaises(ValidationError, e.save)

        e.profile_ids = ['fff']
        e.save()
        self.assertIsInstance(e.id, ObjectId)

    def test_build_exp_id(self):
        # Two example tests
        exp_name = 'after-motion-effect'
        self.assertEquals(models.Exp.build_exp_id(exp_name, self.u1),
                          '9e182dac9b384935658c18854abbc76166224bea7216242cd'
                          '26833318b18500d')
        self.assertNotEqual(models.Exp.build_exp_id(exp_name, self.u2),
                            '9e182dac9b384935658c18854abbc76166224bea7216242cd'
                            '26833318b18500d')

    def test_check_owner_collaborators_integrity(self):
        # Creating an exp involving a user who's id is not set does
        # not work.
        self.assertRaises(models.UserIdSetError,
                          models.Exp.check_owner_collaborators_integrity,
                          self.nu, [self.u1])
        self.assertRaises(models.UserIdSetError,
                          models.Exp.check_owner_collaborators_integrity,
                          self.u1, [self.nu])

    def test_create(self):
        e = models.Exp.create('after-motion-effect', self.u1,
                              'The experiment', [self.u2])
        self.u1.reload()
        self.u2.reload()
        # The exp is created and saved with the right values
        self.assertIsInstance(e.id, ObjectId)
        self.assertEquals(e.exp_id, '9e182dac9b384935658c18854abbc76166224be'
                          'a7216242cd26833318b18500d')
        self.assertEquals(e.owner_id, self.u1.user_id)
        self.assertEquals(e.description, 'The experiment')
        self.assertEquals(len(e.collaborator_ids), 1)
        self.assertEquals(e.n_collaborators, 1)
        self.assertEquals(e.collaborator_ids[0], self.u2.user_id)

        # And the users concerned have been updated
        self.assertIn(e.exp_id, self.u1.exp_ids)
        self.assertIn(e.exp_id, self.u2.exp_ids)

        # But creating an exp involving a user who's id is not set does
        # not work.
        self.assertRaises(models.UserIdSetError, models.Exp.create,
                          'after-motion-effect-2', self.nu)
        self.assertRaises(models.UserIdSetError, models.Exp.create,
                          'after-motion-effect-2', self.u1,
                          collaborators=[self.nu])

        # Finally, setting the owner in the collaborators does not work
        self.assertRaises(models.OwnerInCollaboratorsError, models.Exp.create,
                          'after-motion-effect-2', self.u1,
                          collaborators=[self.u1, self.u2])

    def test_create_no_collaborators(self):
        e = models.Exp.create('after-motion-effect', self.u1,
                              'The experiment')
        self.u1.reload()
        self.u2.reload()
        # The exp is created and saved with the right values
        self.assertIsInstance(e.id, ObjectId)
        self.assertEquals(e.exp_id, '9e182dac9b384935658c18854abbc76166224be'
                          'a7216242cd26833318b18500d')
        self.assertEquals(e.owner_id, self.u1.user_id)
        self.assertEquals(e.description, 'The experiment')
        self.assertEquals(len(e.collaborator_ids), 0)
        self.assertEquals(e.n_collaborators, 0)

        # And the users concerned have been updated
        self.assertIn(e.exp_id, self.u1.exp_ids)
        self.assertNotIn(e.exp_id, self.u2.exp_ids)


class DeviceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_contraints_missing_field(self):
        # A device without a `device_id`, or without a `vk_pem`, is
        # wrong
        d = models.Device()
        d.device_id = 'fff'
        self.assertRaises(ValidationError, d.save)

        d = models.Device()
        d.vk_pem = 'my key'
        self.assertRaises(ValidationError, d.save)

        # But a device with both is ok
        d = models.Device()
        d.device_id = 'fff'
        d.vk_pem = 'my key'
        d.save()
        self.assertIsInstance(d.id, ObjectId)

    def test_constraints_device_id(self):
        # `device_id` must be hexadecimal
        d = models.Device()
        d.device_id = 'fffg'
        d.vk_pem = 'my key'
        self.assertRaises(ValidationError, d.save)
        d.device_id = 'fff'
        d.save()
        self.assertIsInstance(d.id, ObjectId)

    def test_constraints_vk_pem(self):
        # `vk_pem` can't excede 5000 characters
        d = models.Device()
        d.device_id = 'eee'
        d.vk_pem = 'a' * 5001
        self.assertRaises(ValidationError, d.save)
        d.vk_pem = 'a' * 5000
        d.save()
        self.assertIsInstance(d.id, ObjectId)

    def test_build_device_id(self):
        # An example test
        vk_pem = 'my key'
        self.assertEquals(models.Device.build_device_id(vk_pem),
                          'a0e12d601e10154fe5743fd6d2ba37492365077b485f06'
                          'c131ef495420005253')

    def test_create(self):
        d = models.Device.create('my key')
        # Model is saved with the right values
        self.assertIsInstance(d.id, ObjectId)
        self.assertEquals(d.vk_pem, 'my key')
        self.assertEquals(d.device_id,
                          'a0e12d601e10154fe5743fd6d2ba37492365077b485f06'
                          'c131ef495420005253')


class ProfileTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

        # Two users
        self.u1 = models.User(user_id='seb-tmp',
                              persona_email='seb@example.com',
                              gravatar_id='fff')
        self.u1.set_user_id('seb')

        self.u2 = models.User(user_id='toad-tmp',
                              persona_email='toad@example.com',
                              gravatar_id='eee')
        self.u2.set_user_id('toad')

        # An exp for the users
        self.e = models.Exp.create('after-motion-effect', self.u1,
                                   'Study of the after-motion effect',
                                   collaborators=[self.u2])

        # Two devices
        self.d1 = models.Device.create('my key')
        self.d1.save()
        self.d2 = models.Device.create('my second device')
        self.d2.save()

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_constraints_missing_field(self):
        # A profile without profile_id, vk_pem, or exp, is wrong
        p = models.Profile()
        p.profile_id = 'abc'
        p.vk_pem = 'profile key'
        self.assertRaises(ValidationError, p.save)

        p = models.Profile()
        p.profile_id = 'abc'
        p.exp_id = self.e.exp_id
        self.assertRaises(ValidationError, p.save)

        p = models.Profile()
        p.vk_pem = 'profile key'
        p.exp_id = self.e.exp_id
        self.assertRaises(ValidationError, p.save)

        # But with all three, it's ok
        p.profile_id = 'abc'
        p.save()
        self.assertIsInstance(p.id, ObjectId)

    def test_constraints_profile_id(self):
        # `profile_id` must be hexadecimal
        p = models.Profile()
        p.profile_id = 'fffg'
        p.vk_pem = 'profile key'
        p.exp_id = self.e.exp_id
        self.assertRaises(ValidationError, p.save)
        p.profile_id = 'fff'
        p.save()
        self.assertIsInstance(p.id, ObjectId)

    def test_constraints_vk_pem(self):
        # `vk_pem` can't excede 5000 characters
        p = models.Profile()
        p.profile_id = 'eee'
        p.vk_pem = 'a' * 5001
        p.exp_id = self.e.exp_id
        self.assertRaises(ValidationError, p.save)
        p.vk_pem = 'a' * 5000
        p.save()
        self.assertIsInstance(p.id, ObjectId)

    def test_constraints_device_id(self):
        # `device_id` must be hexadecimal
        p = models.Profile()
        p.profile_id = 'fff'
        p.vk_pem = 'profile key'
        p.exp_id = 'fff'
        p.device_id = 'ffg'
        self.assertRaises(ValidationError, p.save)

        p.device_id = 'fff'
        p.save()
        self.assertIsInstance(p.id, ObjectId)

    def test_constraints_result_ids(self):
        # `result_ids` must be hexadecimal
        p = models.Profile()
        p.profile_id = 'fff'
        p.vk_pem = 'profile key'
        p.exp_id = 'fff'
        p.result_ids = ['ffg']
        self.assertRaises(ValidationError, p.save)

        p.result_ids = ['fff']
        p.save()
        self.assertIsInstance(p.id, ObjectId)

    def test_set_device(self):
        # set_device works, and it can only be set once
        p = models.Profile()
        p.profile_id = 'fff'
        p.vk_pem = 'profile key'
        p.exp_id = self.e.exp_id
        p.save()
        self.assertIsNone(p.device_id)
        # The model was saved automatically with the proper value
        p.set_device(self.d1)
        p.reload()
        self.u1.reload()
        self.u2.reload()
        self.e.reload()
        self.assertEquals(p.device_id, self.d1.device_id)
        # device can't be set again
        self.assertRaises(models.DeviceSetError, p.set_device, self.d2)
        self.assertEquals(p.device_id, self.d1.device_id)

        # The other models involved were updated
        self.assertIn(self.d1.device_id, self.e.device_ids)
        self.assertIn(self.d1.device_id, self.u1.device_ids)
        self.assertIn(self.d1.device_id, self.u2.device_ids)

    def test_set_device_already_present_in_users(self):
        # Add the device to self.u1, self.u2, and self.e to make it
        # doesn't get re-added
        self.u1.reload()
        self.u2.reload()
        self.e.reload()
        self.u1.device_ids.append(self.d1.device_id)
        self.u2.device_ids.append(self.d1.device_id)
        self.e.device_ids.append(self.d1.device_id)
        self.u1.save()
        self.u2.save()
        self.e.save()

        # Do the rest of the work
        self.test_set_device()

        # Make sure the device wasn't re-added
        self.assertEquals(self.u1.device_ids.count(self.d1.device_id), 1)
        self.assertEquals(self.u2.device_ids.count(self.d1.device_id), 1)
        self.assertEquals(self.e.device_ids.count(self.d1.device_id), 1)

    def test_set_data(self):
        # set_data works
        p = models.Profile.create('profile key', self.e, {'test_data': 'hoo'})
        self.assertEquals(p.data, models.Data(test_data='hoo'))

        p.set_data({})
        p.reload()
        self.assertEquals(p.data, models.Data())

        p.set_data({'new_data': 'bla'})
        p.reload()
        self.assertEquals(p.data, models.Data(new_data='bla'))

        # Anything else than a dict is refused
        self.assertRaises(models.DataValueError, p.set_data, 'non-dict')
        self.assertRaises(models.DataValueError, p.set_data, [1, 2, 3])
        self.assertRaises(models.DataValueError, p.set_data, 123)

    def test_build_profile_id(self):
        # An example test
        vk_pem = 'profile key'
        self.assertEquals(models.Profile.build_profile_id(vk_pem),
                          'f78b789735d69bb79a9cc71062325cb448700cef87ac74'
                          'c12713d8c2e3c1a674')

    def test_create_with_device(self):
        p = models.Profile.create('profile key', self.e, {'test': 1}, self.d1)
        self.u1.reload()
        self.u2.reload()
        self.e.reload()

        # The proper data was set
        self.assertEquals(p.vk_pem, 'profile key')
        self.assertEquals(p.profile_id, 'f78b789735d69bb79a9cc71062325cb'
                          '448700cef87ac74c12713d8c2e3c1a674')
        self.assertEquals(p.exp_id, self.e.exp_id)
        self.assertEquals(p.device_id, self.d1.device_id)
        self.assertEquals(p.data, models.Data(test=1))

        # The models involved were updated
        self.assertIn(self.d1.device_id, self.e.device_ids)
        self.assertIn(self.d1.device_id, self.u1.device_ids)
        self.assertIn(self.d1.device_id, self.u2.device_ids)
        self.assertIn(p.profile_id, self.e.profile_ids)
        self.assertIn(p.profile_id, self.u1.profile_ids)
        self.assertIn(p.profile_id, self.u2.profile_ids)

    def test_create_with_device_already_present_in_users(self):
        # Add the device to self.u1, self.u2, and self.e to make sure it
        # doesn't get added again futher down
        self.u1.reload()
        self.u2.reload()
        self.e.reload()
        self.u1.device_ids.append(self.d1.device_id)
        self.u2.device_ids.append(self.d1.device_id)
        self.e.device_ids.append(self.d1.device_id)
        self.u1.save()
        self.u2.save()
        self.e.save()

        # Do the rest of the work
        self.test_create_with_device()

        # Make sure the device wasn't added a second time
        self.assertEquals(self.u1.device_ids.count(self.d1.device_id), 1)
        self.assertEquals(self.u2.device_ids.count(self.d1.device_id), 1)
        self.assertEquals(self.e.device_ids.count(self.d1.device_id), 1)

    def test_create_without_device(self):
        # Most of the same process without device or data this time
        p = models.Profile.create('profile key', self.e)
        self.u1.reload()
        self.u2.reload()
        self.e.reload()

        # The proper data was set
        self.assertEquals(p.exp_id, self.e.exp_id)
        self.assertIsNone(p.device_id)
        self.assertEquals(p.data, models.Data())

        # The models involved were updated
        self.assertNotIn(self.d1.device_id, self.e.device_ids)
        self.assertNotIn(self.d1.device_id, self.u1.device_ids)
        self.assertNotIn(self.d1.device_id, self.u2.device_ids)
        self.assertIn(p.profile_id, self.e.profile_ids)
        self.assertIn(p.profile_id, self.u1.profile_ids)
        self.assertIn(p.profile_id, self.u2.profile_ids)

    def test_create_non_dict(self):
        # Anything else than a dict is refused
        self.assertRaises(models.DataValueError, models.Profile.create,
                          'profile key', self.e, 'non-dict')
        self.assertRaises(models.DataValueError, models.Profile.create,
                          'profile key', self.e, [1, 2, 3])
        self.assertRaises(models.DataValueError, models.Profile.create,
                          'profile key', self.e, 123)


class ResultTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

        # Two users
        self.u1 = models.User(user_id='seb-tmp',
                              persona_email='seb@example.com',
                              gravatar_id='fff')
        self.u1.set_user_id('seb')

        self.u2 = models.User(user_id='toad-tmp',
                              persona_email='toad@example.com',
                              gravatar_id='eee')
        self.u2.set_user_id('toad')

        # An exp for the users
        self.e = models.Exp.create('after-motion-effect', self.u1,
                                   'Study of the after-motion effect',
                                   collaborators=[self.u2])

        # A device
        self.d = models.Device.create('my key')
        self.d.save()

        # Two profiles: one attached to the device, the other not
        self.p1 = models.Profile.create('first profile key', self.e,
                                        device=self.d)
        self.p2 = models.Profile.create('second profile key', self.e)

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_constraints_missing_field(self):
        # A result without result_id, profile, exp, created_at, or data,
        # is wrong
        r = models.Result()
        r.profile_id = self.p1.profile_id
        r.exp_id = self.e.exp_id
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)

        r = models.Result()
        r.result_id = 'fff'
        r.exp_id = self.e.exp_id
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)

        r = models.Result()
        r.result_id = 'fff'
        r.profile_id = self.p1.profile_id
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)

        # This fails because MongoEngine seems to initialize a
        # ComplexDateTimeField to `now` upon creation, which is undocumented
        # behaviour (and is different from DateTimeField for which the test
        # passes)
        #r = models.Result()
        #r.result_id = 'fff'
        #r.profile_id = self.p1.profile_id
        #r.exp_id = self.e.exp_id
        #r.data = models.Data(my_result=5)
        #self.assertRaises(ValidationError, r.save)

        r = models.Result()
        r.result_id = 'fff'
        r.profile_id = self.p1.profile_id
        r.exp_id = self.e.exp_id
        r.created_at = datetime.utcnow()
        self.assertRaises(ValidationError, r.save)

        # But with all five, it's ok
        r.data = models.Data(my_result=5)
        r.save()
        self.assertIsInstance(r.id, ObjectId)

    def test_constraints_result_id(self):
        # `result_id` must be hexadecimal
        r = models.Result()
        r.result_id = 'fffg'
        r.profile_id = self.p1.profile_id
        r.exp_id = self.e.exp_id
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)
        r.result_id = 'fff'
        r.save()
        self.assertIsInstance(r.id, ObjectId)

    def test_constraints_exp_id(self):
        # `exp_id` must be hexadecimal
        r = models.Result()
        r.result_id = 'fff'
        r.profile_id = 'fff'
        r.exp_id = 'ffg'
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)

        r.exp_id = 'fff'
        r.save()
        self.assertIsInstance(r.id, ObjectId)

    def test_constraints_profile_id(self):
        # `profile_id` must be hexadecimal
        r = models.Result()
        r.result_id = 'fff'
        r.profile_id = 'ffg'
        r.exp_id = 'fff'
        r.created_at = datetime.utcnow()
        r.data = models.Data(my_result=5)
        self.assertRaises(ValidationError, r.save)

        r.profile_id = 'fff'
        r.save()
        self.assertIsInstance(r.id, ObjectId)

    def test_build_result_id(self):
        # An example test
        created_at = datetime.strptime('2013-06-16T12:38:45.176671Z',
                                       '%Y-%m-%dT%H:%M:%S.%fZ')
        data_dict = {'my_result': 5, 'my_other_result': 10}
        result_id = models.Result.build_result_id(self.p1, created_at,
                                                  data_dict)
        self.assertEquals(result_id, 'db021d30a01085b258f694eed3db82cc'
                          '0c9269a6acb06cd905a3d58d8d24d999')

    def test_create(self):
        r = models.Result.create(self.p1, {'my_result': 5})
        self.u1.reload()
        self.u2.reload()
        self.e.reload()
        self.d.reload()
        self.p1.reload()

        # The proper data was set
        # Can't test result_id since it depends on the time of creation;
        # a test here would be a reverse implementation
        self.assertEquals(r.profile_id, self.p1.profile_id)
        self.assertEquals(r.exp_id, self.e.exp_id)
        self.assertEquals(r.data, models.Data(my_result=5))

        # The models involved were updated
        self.assertIn(r.result_id, self.e.result_ids)
        self.assertIn(r.result_id, self.p1.result_ids)
        self.assertIn(r.result_id, self.u1.result_ids)
        self.assertIn(r.result_id, self.u2.result_ids)

    def test_create_without_device(self):
        # Now the same without a device attached
        r = models.Result.create(self.p2, {'my_result': 5})
        self.u1.reload()
        self.u2.reload()
        self.e.reload()
        self.p2.reload()

        # The proper data was set
        # Can't test result_id since it depends on the time of creation;
        # a test here would be a reverse implementation
        self.assertEquals(r.profile_id, self.p2.profile_id)
        self.assertEquals(r.exp_id, self.e.exp_id)
        self.assertEquals(r.data, models.Data(my_result=5))

        # The models involved were updated
        self.assertIn(r.result_id, self.e.result_ids)
        self.assertIn(r.result_id, self.p2.result_ids)
        self.assertIn(r.result_id, self.u1.result_ids)
        self.assertIn(r.result_id, self.u2.result_ids)

    def test_create_non_dict(self):
        # Anything else than a dict is refused
        self.assertRaises(models.DataValueError, models.Result.create,
                          self.p1, 'non-dict')
        self.assertRaises(models.DataValueError, models.Result.create,
                          self.p1, [1, 2, 3])
        self.assertRaises(models.DataValueError, models.Result.create,
                          self.p1, 123)
