import unittest

from mongoengine import ValidationError, NotUniqueError
from mongoengine.base import ObjectId

from . import init, helpers, models


class UserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = init.create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_constraints_missing_field(self):
        # A user with no user_id, or no email, or no login, is wrong
        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.user_id = 'abc'
        u.login = 'johndoe'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.email = 'johndoe@example.com'
        u.login = 'johndoe'
        self.assertRaises(ValidationError, u.save)

        # But with all of those, it's ok
        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        u.login = 'johndoe'
        # No exception here
        u.save(safe=True)
        self.assertIsInstance(u.id, ObjectId)

    def test_constraints_format(self):
        # `user_id` must be a hexregex
        u = models.User()
        u.user_id = 'abcg'
        u.email = 'johndoe@example.com'
        u.login = 'johndoe'
        self.assertRaises(ValidationError, u.save)

        # `email` must be an email
        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoeexample.com'
        u.login = 'johndoe'
        self.assertRaises(ValidationError, u.save)

        # `login` must be follow its format
        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        u.login = 'johndoe_'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        u.login = '_johndoe'
        self.assertRaises(ValidationError, u.save)

        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        u.login = '1_johndoe'
        self.assertRaises(ValidationError, u.save)

        # `gravatar_id' must be a hexregex
        u = models.User()
        u.user_id = 'abc'
        u.email = 'johndoe@example.com'
        u.login = 'johndoe'
        u.gravatar_id = 'abcg'
        self.assertRaises(ValidationError, u.save)

    def test_constraints_unique_user_id(self):
        # `user_id` must be unique
        u1 = models.User()
        u1.user_id = 'aaa'
        u1.email = 'johndoe1@example.com'
        u1.login = 'johndoe1'
        u1.save()

        u2 = models.User()
        u2.user_id = 'aaa'
        u2.email = 'johndoe2@example.com'
        u2.login = 'johndoe2'
        self.assertRaises(NotUniqueError, u2.save)
