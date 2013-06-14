import unittest

from flask.ext.mongoengine import MongoEngine

from yelandur import create_app, create_apizer, helpers
from yelandur.session import ItsdangerousSessionInterface


class InitTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_create_apizer(self):
        # A mock app to work with
        class App(object):
            pass

        mock_app = App()
        mock_app.config = {'API_VERSION_URL': '/vX_mock_test'}

        mock_apize = create_apizer(mock_app)
        self.assertEqual(mock_apize('/test_url'), '/vX_mock_test/test_url')

        # Now with a real app object
        apize = create_apizer(self.app)
        self.assertRegexpMatches(apize('/test_url'),
                                 r'^/v[0-9]+/test_url$')

    def test_create_app(self):
        # Test configuration loading
        self.assertTrue(self.app.config['TESTING'])
        self.assertRaises(IOError, create_app, 'absent')

        # MongoEngine is initialized
        self.assertIsInstance(self.app.extensions['mongoengine'], MongoEngine)

        # Session interface is initialized
        self.assertIsInstance(self.app.session_interface,
                              ItsdangerousSessionInterface)

        # Blueprints are present
        self.assertIn('auth', self.app.blueprints)
        self.assertIn('users', self.app.blueprints)
        self.assertIn('exps', self.app.blueprints)
        self.assertIn('devices', self.app.blueprints)
        self.assertIn('profiles', self.app.blueprints)
        self.assertIn('results', self.app.blueprints)


class RootApiTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(mode='test')
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_root(self):
        # Nothing is found out of the blueprints (/auth, /users, /devices,
        # etc)
        self.assertEqual(self.client.get('/').status_code, 404)
        apize = create_apizer(self.app)
        self.assertEqual(self.client.get(apize('')).status_code, 404)
        self.assertEqual(self.client.get(apize('/')).status_code, 404)
