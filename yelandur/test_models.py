import unittest

from mongoengine import ValidationError, NotUniqueError

from yelandur import init, helpers, models


class UserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = init.create_app(mode='test')

        # A reference user
        models.User(user_id='aaa', email='refuser@example.com',
                    login='refuser').save()

    def tearDown(self):
        with self.app.test_request_context():
            helpers.drop_test_database()

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
        self.assertTrue(u.save())

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
