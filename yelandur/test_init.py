import unittest

from flask.ext.mongoengine import MongoEngine

from yelandur import init, helpers


class InitTestCase(unittest.TestCase):

    def setUp(self):
        self.app = init.create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.drop_test_database()

    def test_create_apizer(self):
        # A mock app to work with
        class App(object):
            pass

        mock_app = App()
        mock_app.config = {'API_VERSION_URL': '/api/vX_mock_test'}

        mock_apize = init.create_apizer(mock_app)
        self.assertEqual(mock_apize('/test_url'), '/api/vX_mock_test/test_url')

        # Now with a real app object
        apize = init.create_apizer(self.app)
        self.assertRegexpMatches(apize('/test_url'),
                                 r'^/api/v[0-9]+/test_url$')

    def test_create_app(self):
        # Test configuration loading
        self.assertTrue(self.app.config['TESTING'])
        self.assertRaises(IOError, init.create_app, 'absent')

        # MongoEngine is initialized
        self.assertIsInstance(self.app.extensions['mongoengine'], MongoEngine)

        # Blueprints are present
        self.assertIn('auth', self.app.blueprints)
        self.assertIn('users', self.app.blueprints)
        self.assertIn('devices', self.app.blueprints)


#class RootApiTestCase(unittest.TestCase):

    #def setUp(self):

