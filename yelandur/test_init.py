import unittest

from flask.ext.mongoengine import MongoEngine

from yelandur import init


class InitTestCase(unittest.TestCase):

    def test_create_apizer(self):
        # A mock app to work with
        class App(object):
            pass

        mock_app = App()
        mock_app.config = {'API_VERSION_URL': '/api/vX_mock_test'}

        mock_apize = init.create_apizer(mock_app)
        self.assertEqual(mock_apize('/test_url'), '/api/vX_mock_test/test_url')

        # Now with a real app object
        app = init.create_app(mode='test')
        apize = init.create_apizer(app)
        self.assertRegexpMatches(apize('/test_url'),
                                 r'^/api/v[0-9]+/test_url$')

    def test_create_app(self):
        # Test configuration loading
        test_app = init.create_app(mode='test')
        self.assertTrue(test_app.config['TESTING'])
        self.assertRaises(IOError, init.create_app, 'absent')

        # MongoEngine is initialized
        self.assertEqual(type(test_app.extensions['mongoengine']),
                         MongoEngine)

        # Blueprints are present
        self.assertIn('auth', test_app.blueprints)
        self.assertIn('users', test_app.blueprints)
        self.assertIn('devices', test_app.blueprints)
