import unittest
import re
from functools import partial
from datetime import datetime
from types import MethodType

import ecdsa
import jws
from ecdsa.util import sigencode_der, sigdecode_string
from jws.utils import base64url_decode
from mongoengine import Document, StringField

from . import init, models, helpers


class HashTestCase(unittest.TestCase):

    def test_hexregex(self):
        # Two example cases
        self.assertTrue(re.search(helpers.hexregex, '345abcf'),
                        'bad hexregex')
        self.assertFalse(re.search(helpers.hexregex, '345abdg'),
                         'bad hexregex')

    def test_md5hex(self):
        # One example case
        self.assertEqual(helpers.md5hex('test'),
                         '098f6bcd4621d373cade4e832627b4f6',
                         'bad md5 hex digest')

    def test_sha256hex(self):
        # One example case
        self.assertEqual(helpers.sha256hex('test'),
                         ('9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15'
                          'd6c15b0f00a08'),
                         'bad sha256 hex digest')

    def test_random_md5hex(self):
        r1 = helpers.random_md5hex()
        r2 = helpers.random_md5hex()

        # Make sure hexregex is good
        self.test_hexregex()

        # r1 is a 32 characters-long hex hash
        self.assertEqual(len(r1), 32, 'bad md5hex length')
        self.assertTrue(re.search(helpers.hexregex, r1),
                        'bad md5hex format')

        # r1 and r2 are different
        self.assertFalse(r1 == r2, 'constant md5hex')

    def test_random_sha256hex(self):
        r1 = helpers.random_sha256hex()
        r2 = helpers.random_sha256hex()

        # Make sure hexregex is good
        self.test_hexregex()

        # r1 is a 64 characters-long hex hash
        self.assertEqual(len(r1), 64, 'bad sha256hex length')
        self.assertTrue(re.search(helpers.hexregex, r1),
                        'bad sha256hex format')

        # r1 and r2 are different
        self.assertFalse(r1 == r2, 'constant sha256hex')

    def test_build_gravatar_id(self):
        # One example case
        self.assertEqual(helpers.build_gravatar_id('johndoe@example.com'),
                         'fd876f8cd6a58277fc664d47ea10ad19',
                         'bad gravatar id')


class SigConversionTestCase(unittest.TestCase):

    def test_sig_der_to_string(self):
        # One runtime generated example case
        sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        order = sk.curve.order
        jheader = '{"alg": "ES256"}'
        jpayload = '{"test": "test"}'
        sig_string_b64 = jws.sign(jheader, jpayload, sk, is_json=True)
        sig_string = base64url_decode(sig_string_b64)
        r, s = sigdecode_string(sig_string, order)
        sig_der = sigencode_der(r, s, order)
        self.assertEqual(helpers.sig_der_to_string(sig_der, order), sig_string,
                         'bad der_to_string signature')

        # One static example case
        sig2_string = ('k\xfc\xf2(\x88\x13I\x87\xc0\xf7%\x90\x16PD\xeb\xace'
                       '\x89\x8f\r\xbe^u\xc6\x19\x19\xb8\xe1=\xb5\xc1\x1bT'
                       '\xc6\xa9\xea\xcdC\xa5\xaf\xd7~\xddB\x14mmBw\x8b\xcc'
                       '\xecS\xaa\x03\xfal\xe02\xf6\xcb \xc3')
        sig2_der = ('0D\x02 k\xfc\xf2(\x88\x13I\x87\xc0\xf7%\x90\x16PD\xeb'
                    '\xace\x89\x8f\r\xbe^u\xc6\x19\x19\xb8\xe1=\xb5\xc1\x02 '
                    '\x1bT\xc6\xa9\xea\xcdC\xa5\xaf\xd7~\xddB\x14mmBw\x8b\xcc'
                    '\xecS\xaa\x03\xfal\xe02\xf6\xcb \xc3')
        order = 115792089210356248762697446949407573529996955224135760342422259061068512044369L
        self.assertEqual(helpers.sig_der_to_string(sig2_der, order),
                         sig2_string, 'bad der_to_string signature')


class WipeDatabaseTestCase(unittest.TestCase):

    def setUp(self):
        # Create test app
        self.app = init.create_app(mode='test')
        self.conn = self.app.extensions['mongoengine'].connection

        u = models.User.get_or_create_by_email('johndoe@example.com')
        e = models.Exp.create(name='test', owner=u)
        d = models.Device.create('pem')
        models.Result.create(e, d, {})

        # A test collection
        class TestDoc(Document):

            name = StringField()

        self.TestDoc = TestDoc
        TestDoc(name='doc1').save()

    def tearDown(self):
        if (self.app.config['MONGODB_DB'][-5:] == '_test' and
                self.app.config['TESTING']):
            models.User.objects.delete()
            models.Exp.objects.delete()
            models.Device.objects.delete()
            models.Result.objects.delete()
            self.TestDoc.objects.delete()

    def test_wipe_test_database(self):
        # Check the database was created
        self.assertIn(self.app.config['MONGODB_DB'],
                      self.conn.database_names())
        self.assertEquals(models.User.objects.count(), 1)
        self.assertEquals(models.Exp.objects.count(), 1)
        self.assertEquals(models.Device.objects.count(), 1)
        self.assertEquals(models.Result.objects.count(), 1)
        self.assertEquals(self.TestDoc.objects.count(), 1)

        # Try wiping the database
        with self.app.test_request_context():
            helpers.wipe_test_database(self.TestDoc)

        self.assertEquals(models.User.objects.count(), 0)
        self.assertEquals(models.Exp.objects.count(), 0)
        self.assertEquals(models.Device.objects.count(), 0)
        self.assertEquals(models.Result.objects.count(), 0)
        self.assertEquals(self.TestDoc.objects.count(), 0)

    def test_wipe_nontest_database(self):
        # Check the database was created
        self.assertIn(self.app.config['MONGODB_DB'],
                      self.conn.database_names())
        self.assertEquals(models.User.objects.count(), 1)
        self.assertEquals(models.Exp.objects.count(), 1)
        self.assertEquals(models.Device.objects.count(), 1)
        self.assertEquals(models.Result.objects.count(), 1)
        self.assertEquals(self.TestDoc.objects.count(), 1)

        # Try wiping the database with deactivated TESTING flag
        self.app.config['TESTING'] = False
        with self.app.test_request_context():
            self.assertRaises(ValueError, helpers.wipe_test_database,
                              self.TestDoc)

        # Reset the TESTING flag
        self.app.config['TESTING'] = True

        # Try wiping the database with changed db name
        real_db_name = self.app.config['MONGODB_DB']
        self.app.config['MONGODB_DB'] = 'database_nontest'
        with self.app.test_request_context():
            self.assertRaises(ValueError, helpers.wipe_test_database,
                              self.TestDoc)

        # Reset the database name
        self.app.config['MONGODB_DB'] = real_db_name


class JsonifyTestCase(unittest.TestCase):

    def setUp(self):
        self.app = init.create_app(mode='test')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_jsonify(self):
        # Test as a classical request
        with self.app.test_request_context():
            # Test with an array
            j1 = helpers.jsonify(range(3))
            self.assertEqual(j1.data, '[\n  0, \n  1, \n  2\n]',
                             'bad jsonifying of array')
            self.assertEqual(j1.content_type, 'application/json',
                             'bad content-type')

            # Test with a dict
            j2 = helpers.jsonify({'a': 1, 'b': 2})
            self.assertEqual(j2.data, '{\n  "a": 1, \n  "b": 2\n}',
                             'bad jsonifying of dict')
            self.assertEqual(j2.content_type, 'application/json',
                             'bad content-type')

        # Test as an xhr
        with self.app.test_request_context(headers=[('X-Requested-With',
                                                     'XMLHttpRequest')]):
            # Test with an array
            j1 = helpers.jsonify(range(3))
            self.assertEqual(j1.data, '[0, 1, 2]', 'bad jsonifying of array')
            self.assertEqual(j1.content_type, 'application/json',
                             'bad content-type')

            # Test with a dict
            j2 = helpers.jsonify({'a': 1, 'b': 2})
            self.assertEqual(j2.data, '{"a": 1, "b": 2}',
                             'bad jsonifying of dict')
            self.assertEqual(j2.content_type, 'application/json',
                             'bad content-type')


class JSONQuerySetTestCase(unittest.TestCase):

    def setUp(self):
        # Init the app to access the database
        self.app = init.create_app(mode='test')

        # A test collection using the JSONMixin. That should also bring the
        # JSONQuerySet along (through the `meta` attribute).
        class TestDoc(Document, helpers.JSONMixin):

            _test = ['name']
            _empty = []

            name = StringField()

        self.TestDoc = TestDoc
        TestDoc(name='doc1').save()
        TestDoc(name='doc2').save()
        TestDoc(name='doc3').save()
        self.qs = TestDoc.objects

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database(self.TestDoc)

    def test__to_jsonable(self):
        # Basic usage, with inheritance
        self.assertEqual(set([d['name'] for d in
                              self.qs._to_jsonable('_test')]),
                         {'doc1', 'doc2', 'doc3'})
        self.assertEqual(set([d['name'] for d in
                              self.qs._to_jsonable('_test_ext')]),
                         {'doc1', 'doc2', 'doc3'})

        # Exception raised if empty jsonable
        self.assertRaises(helpers.EmptyJsonableException, self.qs._to_jsonable,
                          '_empty')

    def test__build_to_jsonable(self):
        # Basic usage, with inheritance
        self.assertEqual(set([d['name'] for d in
                              self.qs._build_to_jsonable('_test')()]),
                         {'doc1', 'doc2', 'doc3'})
        self.assertEqual(set([d['name'] for d in
                              self.qs._build_to_jsonable('_test_ext')()]),
                         {'doc1', 'doc2', 'doc3'})

        # No exception is raised if empty jsonable
        self.assertEqual(self.qs._build_to_jsonable('_empty')(), None)

    def test___getattribute__(self):
        # Regular attributes are found
        self.qs.__class__.a = '1'
        self.assertEqual(self.qs.__getattribute__('a'), '1')

        # Asking for `to_` returns the attribute
        self.qs.__class__.to_ = 'to'
        self.qs._document.to_ = 'document_to'
        self.assertEqual(self.qs.__getattribute__('to_'), 'to')

        # to_* attributes raise an exception if the _* type_string isn't
        # defined in the Document class and the to_* attribute doesn't exist.
        self.assertRaises(AttributeError, self.qs.__getattribute__,
                          '_absent')

        # If the attribute exists (but not the type_string in the Document
        # class), the attribute is found.
        self.qs.__class__.to_foo = 'bar'
        self.assertEqual(self.qs.__getattribute__('to_foo'), 'bar')

        # But if the attribute exists as well as the type_string in the
        # Document class, the type_string shadows the attribute.
        self.qs.__class__.to_foo = 'bar'
        self.qs._document._foo = ['a']
        self.assertIsInstance(self.qs.__getattribute__('to_foo'), MethodType)

        # `to_mongo` is skipped even if _mongo type_string exists
        self.qs._document._mongo = ['gobble']
        self.assertRaises(AttributeError, self.qs.__getattribute__,
                          'to_mongo')


class JSONMixinTestCase(unittest.TestCase):

    def setUp(self):
        self.bad_regexes = ['/test', 'test/', 'te/st', '/', '//']
        self.bad_counts = ['ntest', 'test', 'n_', 'n']

        ############################
        # The instances to work with
        ############################
        self.jm = helpers.JSONMixin()
        self.jm1 = helpers.JSONMixin()
        self.jm2 = helpers.JSONMixin()
        self.jm11 = helpers.JSONMixin()
        self.jm12 = helpers.JSONMixin()

        ##################
        # Their attributes
        ##################

        # Basics, for basic inheritance
        self.jm.a = '1'
        self.jm.l = [1, 2]
        self.jm.date = datetime(2012, 9, 12, 20, 12, 54)

        self.jm1.a1 = '11'
        self.jm1.l1 = [3, 4]

        self.jm2.a2 = '21'
        self.jm2.l2 = [5, 6]

        self.jm11.a11 = '111'
        self.jm11.l11 = [7, 8]

        self.jm12.a12 = '121'
        self.jm12.l12 = [9, 10]

        # Lists and inheritance
        self.jm.l_jm = [self.jm1, self.jm2]

        self.jm1.l1_jm = [self.jm11, self.jm12]

        # Regexes and inheritance
        self.jm.jm1 = self.jm1
        self.jm.jm2 = self.jm2

        self.jm1.jm11 = self.jm11
        self.jm1.jm12 = self.jm12

        ##################
        # The type_strings
        ##################

        ## Basic usage and basic inheritance
        self.jm._basic = ['a']
        self.jm._basic_ext = ['l']

        self.jm1._basic = ['a1']
        self.jm1._basic_ext = ['l1']

        ## Inheritance with nested objects: truncation of type_string
        self.jm._trunc = ['jm1']
        self.jm._trunc_ext = ['l']

        self.jm1._trunc = []
        self.jm1._trunc_ext = ['jm11']

        self.jm11._trunc = []
        self.jm11._trunc_ext = ['a11']
        self.jm11._trunc_ext_ext = ['l11']

        ## Inheritance with nested lists
        self.jm._list = ['l']
        self.jm._list_ext = ['l_jm']

        self.jm1._list = ['l1']
        self.jm1._list_ext = ['l1_jm']

        self.jm2._list = ['l2']

        self.jm11._list = ['l11']

        self.jm12._list = ['l12']

        ## Absent type_strings, at each level
        # `self.jm._absent` is absent
        self.jm._absent_ext = ['jm1']
        self.jm._absent_ext_ext_ext = []

        # `self.jm1._absent` is absent
        # `self.jm1._absent_ext` is absent
        self.jm1._absent_ext_ext = ['jm11']

        # `self.jm11._absent` is absent
        # `self.jm11._absent_ext` is absent
        # `self.jm11._absent_ext_ext` is absent
        self.jm11._absent_ext_ext_ext = ['a1']

        ## Absent type_strings in lists
        # `self.jm._absentl` is absent
        self.jm._absentl_ext = ['l_jm']
        self.jm._absentl_ext_ext = []

        # `self.jm1._absentl` is absent
        # `self.jm1._absentl_ext` is absent
        self.jm1._absentl_ext_ext = ['l1_jm']

        self.jm2._absentl = []

        # `self.jm11._absentl` is absent
        # `self.jm11._absentl_ext` is absent
        # `self.jm11._absentl_ext_ext` is absent
        self.jm11._absentl_ext_ext_ext = ['a1']

        self.jm12._absentl = []

        ## Empty type_string
        self.jm._empty = []

        self.jm1._empty = []

        ## Renaming keys
        self.jm._rename = [('jm1', 'trans_jm1')]

        self.jm1._rename = [('jm11', 'trans_jm11')]
        self.jm1._rename_ext = [('a1', 'trans_a1')]

        self.jm11._rename = [('a11', 'trans_a11')]
        self.jm11._rename_ext = [('l11', 'trans_l11')]

        ## Counts, with nested objects
        self.jm._count = ['n_l_jm']
        self.jm._count_ext = ['l_jm']

        self.jm1._count = ['n_l1_jm']
        self.jm1._count_ext = ['l1_jm']

        self.jm2._count = ['n_l2']

        self.jm11._count = ['n_l11']

        self.jm12._count = ['n_l12']

        ## Regexes, with nested objects
        self.jm._regex = [(r'/^jm([0-9])$/', r'trans_jm\1')]

        self.jm1._regex = [(r'/^jm1([0-9])$/', r'trans_jm1\1')]

        self.jm2._regex = [(r'/^([a-z])2$/', r'trans_\g<1>2')]

        self.jm11._regex = [(r'/^([a-z])11$/', r'trans_\g<1>11')]

        self.jm12._regex = [(r'/^([a-z])12$/', r'trans_\g<1>12')]

    def test__is_regex(self):
        # Example of correct regex
        self.assertTrue(self.jm._is_regex('/test/'))

        # Examples of incorrect regexes
        for br in self.bad_regexes:
            self.assertFalse(self.jm._is_regex(br))

    def test__get_regex_string(self):
        # Example of correct regex
        self.assertEqual(self.jm._get_regex_string('/test/'), 'test')

        # Examples of incorrect regexes
        for br in self.bad_regexes:
            self.assertRaises(ValueError, self.jm._get_regex_string, br)

    def test__is_count(self):
        # Example of correct count
        self.assertTrue(self.jm._is_count('n_test'))

        # Examples of incorrect counts
        for bc in self.bad_counts:
            self.assertFalse(self.jm._is_count(bc))

    def test__get_count_string(self):
        # Example of correct count
        self.assertEqual(self.jm._get_count_string('n_test'), 'test')

        # Examples of incorrect counts
        for bc in self.bad_counts:
            self.assertRaises(ValueError, self.jm._get_count_string, bc)

    def test__get_includes(self):
        ## Examples of includes
        # With inheritance
        self.assertEqual(self.jm._get_includes('_basic'), ['a'])
        self.assertEqual(self.jm._get_includes('_basic_ext'), ['a', 'l'])
        self.assertEqual(self.jm._get_includes('_basic_ext_ext'), ['a', 'l'])

        # Don't raise an exception if nothing found
        self.assertEqual(self.jm._get_includes('_absent'), [])

        # Examples of bad type strings
        self.assertRaises(ValueError, self.jm._get_includes, 'basic')
        self.assertRaises(ValueError, self.jm._get_includes, '_1basic')
        self.assertRaises(ValueError, self.jm._get_includes, '_basic_')

    def test__parse_preinc(self):
        # Examples of preincs to parse
        self.assertEqual(self.jm._parse_preinc('test'), ('test', 'test'))
        self.assertEqual(self.jm._parse_preinc(('test', 'test')),
                         ('test', 'test'))

    def test__find_type_string(self):
        ## Example type strings
        # Inheritance
        self.assertEqual(self.jm._find_type_string('_basic'), '_basic')
        self.assertEqual(self.jm._find_type_string('_basic_ext'),
                         '_basic_ext')
        self.assertEqual(self.jm._find_type_string('_basic_ext_ext'),
                         '_basic_ext')

        # If nothing found, raise an exception
        self.assertRaises(AttributeError, self.jm._find_type_string, '_absent')

        # More inheritance
        self.assertEqual(self.jm._find_type_string('_absent_ext'),
                         '_absent_ext')
        self.assertEqual(self.jm._find_type_string('_absent_ext_ext'),
                         '_absent_ext')
        self.assertEqual(self.jm._find_type_string('_absent_ext_ext_ext'),
                         '_absent_ext_ext_ext')

    def test__insert_jsonable(self):
        ## Example insertions
        # Basic
        res = {}
        self.jm._insert_jsonable('_basic', res, ('a', 'a'))
        self.assertEqual(res, {'a': '1'})

        # Inheritance and nested objects: truncation of type_string
        res = {}
        self.jm._insert_jsonable('_trunc', res, ('jm1', 'jm1'))
        self.assertEqual(res, {})

        res = {}
        self.jm._insert_jsonable('_trunc_ext', res, ('jm1', 'jm1'))
        self.assertEqual(res, {'jm1': {'jm11': {'a11': '111'}}})

        # Inheritance with nested lists
        res = {}
        self.jm._insert_jsonable('_list', res, ('l', 'l'))
        self.assertEqual(res, {'l': [1, 2]})

        res = {}
        self.jm._insert_jsonable('_list_ext', res, ('l_jm', 'l_jm'))
        self.assertEqual(res, {'l_jm': [{'l1': [3, 4],
                                         'l1_jm': [{'l11': [7, 8]},
                                                   {'l12': [9, 10]}]},
                                        {'l2': [5, 6]}]})

        # If, in a nested attribute, no parent can be found for the given
        # type_string, an AttributeError should be raised.
        res = {}
        self.assertRaises(AttributeError, self.jm._insert_jsonable,
                          '_absent', res, ('jm1', 'jm1'))

        res = {}
        self.assertRaises(AttributeError, self.jm._insert_jsonable,
                          '_absentl', res, ('l_jm', 'l_jm'))

        # Renaming keys
        res = {}
        self.jm._insert_jsonable('_rename', res, ('jm1', 'trans_jm1'))
        self.assertEqual(res,
                         {'trans_jm1': {'trans_jm11': {'trans_a11': '111'}}})

    def test__insert_count(self):
        # Example insertion with renaming
        res = {}
        self.jm._insert_count(res, ('n_l_jm', 'trans_n_l_jm'))
        self.assertEqual(res, {'trans_n_l_jm': 2})

    def test__insert_regex(self):
        # Example insertions
        res = {}
        self.jm._insert_regex('_regex', res, (r'/^jm([0-9])$/', r'trans_jm\1'))
        self.assertEqual(res,
                         {'trans_jm1': {'trans_jm11': {'trans_a11': '111',
                                                       'trans_l11': [7, 8]},
                                        'trans_jm12': {'trans_a12': '121',
                                                       'trans_l12': [9, 10]}},
                          'trans_jm2': {'trans_a2': '21',
                                        'trans_l2': [5, 6]}})

    def to_jsonable_all_but_empty(self, to_jsonable):
        # Examining all defined type_strings, which describe many if not all
        # possible cases. Exclude '_empty', which involves
        # `EmptyJsonableException`.

        # Basic with inheritance
        self.assertEqual(to_jsonable('_basic'), {'a': '1'})
        self.assertEqual(to_jsonable('_basic_ext'), {'a': '1', 'l': [1, 2]})

        # Truncated inheritance for nested objects
        self.assertEqual(to_jsonable('_trunc'), {})
        self.assertEqual(to_jsonable('_trunc_ext'),
                         {'l': [1, 2], 'jm1': {'jm11': {'a11': '111'}}})
        self.assertEqual(to_jsonable('_trunc_ext_ext'),
                         {'l': [1, 2], 'jm1': {'jm11': {'a11': '111'}}})

        # Inheritance with nested lists
        self.assertEqual(to_jsonable('_list'), {'l': [1, 2]})
        self.assertEqual(to_jsonable('_list_ext'),
                         {'l': [1, 2],
                          'l_jm': [{'l1': [3, 4],
                                    'l1_jm': [{'l11': [7, 8]},
                                              {'l12': [9, 10]}]},
                                   {'l2': [5, 6]}]})

        # Absent type_strings
        self.assertRaises(AttributeError, to_jsonable, '_absent')
        self.assertRaises(AttributeError, to_jsonable, '_absent_ext')
        self.assertRaises(AttributeError, to_jsonable, '_absent_ext_ext')
        self.assertRaises(AttributeError, to_jsonable, '_absent_ext_ext_ext')

        # Absent type_strings in lists
        self.assertRaises(AttributeError, to_jsonable, '_absentl')
        self.assertRaises(AttributeError, to_jsonable, '_absentl_ext')
        self.assertRaises(AttributeError, to_jsonable, '_absentl_ext_ext')
        self.assertRaises(AttributeError, to_jsonable, '_absentl_ext_ext_ext')

        # Renaming keys
        self.assertEqual(to_jsonable('_rename'),
                         {'trans_jm1': {'trans_jm11': {'trans_a11': '111'}}})
        self.assertEqual(to_jsonable('_rename_ext'),
                         {'trans_jm1': {'trans_jm11': {'trans_a11': '111'}}})

        # Counts, with nested objects
        self.assertEqual(to_jsonable('_count'), {'n_l_jm': 2})
        self.assertEqual(to_jsonable('_count_ext'),
                         {'n_l_jm': 2,
                          'l_jm': [{'n_l1_jm': 2,
                                    'l1_jm': [{'n_l11': 2}, {'n_l12': 2}]},
                                   {'n_l2': 2}]})

        # Regexes, with nested objects
        self.assertEqual(to_jsonable('_regex'),
                         {'trans_jm1': {'trans_jm11': {'trans_a11': '111',
                                                       'trans_l11': [7, 8]},
                                        'trans_jm12': {'trans_a12': '121',
                                                       'trans_l12': [9, 10]}},
                          'trans_jm2': {'trans_a2': '21',
                                        'trans_l2': [5, 6]}})

    def test__to_jsonable(self):
        # Examine all cases not involving EmptyJsonableException
        self.to_jsonable_all_but_empty(self.jm._to_jsonable)

        # The special case of EmptyJsonableException
        self.assertRaises(helpers.EmptyJsonableException,
                          self.jm._to_jsonable, '_empty')

    def test__jsonablize(self):
        # With a JSONMixin attribute
        attr_jsonablize = partial(helpers.JSONMixin._jsonablize, attr=self.jm)
        self.to_jsonable_all_but_empty(attr_jsonablize)
        self.assertRaises(helpers.EmptyJsonableException, attr_jsonablize,
                          '_empty')

        ## The following tests do not do full checks, they just make sure
        ## _jsonablized forwards the attributes to the right subfunction.
        # With list attributes
        self.assertEqual(helpers.JSONMixin._jsonablize('_regex',
                                                       [self.jm1, self.jm2]),
                         [{'trans_jm11': {'trans_a11': '111',
                                          'trans_l11': [7, 8]},
                           'trans_jm12': {'trans_a12': '121',
                                          'trans_l12': [9, 10]}},
                          {'trans_a2': '21',
                           'trans_l2': [5, 6]}])
        self.assertRaises(AttributeError, helpers.JSONMixin._jsonablize,
                          '_absentl', [self.jm1, self.jm2])
        self.assertRaises(AttributeError, helpers.JSONMixin._jsonablize,
                          '_absentl_ext', [self.jm1, self.jm2])
        self.assertRaises(AttributeError, helpers.JSONMixin._jsonablize,
                          '_absentl_ext_ext', [self.jm1, self.jm2])
        self.assertRaises(AttributeError, helpers.JSONMixin._jsonablize,
                          '_absentl_ext_ext_ext', [self.jm1, self.jm2])

        # With a datetime attribute
        self.assertEqual(helpers.JSONMixin._jsonablize(None, self.jm.date),
                         '12/09/2012 at 20:12:54')

        # With something else
        self.assertEqual(helpers.JSONMixin._jsonablize(None, self.jm.a),
                         '1')

    def test___getattribute__(self):
        # Regular attributes are found
        self.assertEqual(self.jm.__getattribute__('a'), '1')

        # Asking for `to_` returns the attribute
        self.jm.__class__.to_ = 'to'
        self.assertEqual(self.jm.__getattribute__('to_'), 'to')

        # to_* attributes raise an exception if the _* type_string isn't
        # defined and the to_* attribute doesn't exist.
        self.assertRaises(AttributeError, self.jm.__getattribute__,
                          'to_foo')

        # If the attribute exists (but not the type_string), the attribute is
        # found.
        self.jm.__class__.to_foo = 'bar'
        self.assertEqual(self.jm.__getattribute__('to_foo'), 'bar')

        # But if the attribute exists as well as the type_string, the
        # type_string shadows the attribute.
        self.jm.__class__.to_foo = 'bar'
        self.jm.__class__._foo = ['a']
        self.assertIsInstance(self.jm.__getattribute__('to_foo'), MethodType)

        # `to_mongo` is skipped even if _mongo type_string exists
        self.jm.__class__._mongo = ['gobble']
        self.assertRaises(AttributeError, self.jm.__getattribute__,
                          'to_mongo')

    def test__build_to_jsonable(self):
        ### Without attribute name, behaves like _to_jsonable except for the
        ### `EmptyJsonableException`
        def to_jsonable_no_attr(pre_type_string):
            return self.jm._build_to_jsonable(pre_type_string)()

        self.to_jsonable_all_but_empty(to_jsonable_no_attr)
        self.assertEqual(self.jm._build_to_jsonable('_empty')(), None)

        ### With attribute name, behaves a little like _jsonablize (but takes
        ### an attribute name, not an attribute).
        def to_jsonable_attr(pre_type_string, attr_name):
            return self.jm._build_to_jsonable(pre_type_string)(attr_name)

        ## With JSONMixin attribute
        to_jsonable_partial = partial(to_jsonable_attr, attr_name='jm1')

        # Basic with inheritance
        self.assertEqual(to_jsonable_partial('_basic'), {'a1': '11'})
        self.assertEqual(to_jsonable_partial('_basic_ext'),
                         {'a1': '11', 'l1': [3, 4]})

        # Truncated inheritance for nested objects
        self.assertEqual(to_jsonable_partial('_trunc'), None)
        self.assertEqual(to_jsonable_partial('_trunc_ext'),
                         {'jm11': {'a11': '111'}})
        self.assertEqual(to_jsonable_partial('_trunc_ext_ext'),
                         {'jm11': {'a11': '111'}})

        # Inheritance with nested lists
        self.assertEqual(to_jsonable_partial('_list'), {'l1': [3, 4]})
        self.assertEqual(to_jsonable_partial('_list_ext'),
                         {'l1': [3, 4],
                          'l1_jm': [{'l11': [7, 8]},
                                    {'l12': [9, 10]}]})

        # Absent type_strings
        self.assertRaises(AttributeError, to_jsonable_partial, '_absent')
        self.assertRaises(AttributeError, to_jsonable_partial, '_absent_ext')
        self.assertRaises(AttributeError, to_jsonable_partial,
                          '_absent_ext_ext')
        self.assertRaises(AttributeError, to_jsonable_partial,
                          '_absent_ext_ext_ext')

        # Absent type_strings in lists
        self.assertRaises(AttributeError, to_jsonable_partial, '_absentl')
        self.assertRaises(AttributeError, to_jsonable_partial, '_absentl_ext')
        self.assertRaises(AttributeError, to_jsonable_partial,
                          '_absentl_ext_ext')
        self.assertRaises(AttributeError, to_jsonable_partial,
                          '_absentl_ext_ext_ext')

        # Empty type_string
        self.assertEqual(to_jsonable_partial('_empty'), None)

        # Renaming keys
        self.assertEqual(to_jsonable_partial('_rename'),
                         {'trans_jm11': {'trans_a11': '111'}})
        self.assertEqual(to_jsonable_partial('_rename_ext'),
                         {'trans_jm11': {'trans_a11': '111',
                                         'trans_l11': [7, 8]},
                          'trans_a1': '11'})

        # Counts, with nested objects
        self.assertEqual(to_jsonable_partial('_count'), {'n_l1_jm': 2})
        self.assertEqual(to_jsonable_partial('_count_ext'),
                         {'n_l1_jm': 2,
                          'l1_jm': [{'n_l11': 2}, {'n_l12': 2}]})

        # Regexes, with nested objects
        self.assertEqual(to_jsonable_partial('_regex'),
                         {'trans_jm11': {'trans_a11': '111',
                                         'trans_l11': [7, 8]},
                          'trans_jm12': {'trans_a12': '121',
                                         'trans_l12': [9, 10]}})

        ## With list attributes
        to_jsonable_partial_l = partial(to_jsonable_attr, attr_name='l_jm')
        self.assertEqual(to_jsonable_partial_l('_regex'),
                         [{'trans_jm11': {'trans_a11': '111',
                                          'trans_l11': [7, 8]},
                           'trans_jm12': {'trans_a12': '121',
                                          'trans_l12': [9, 10]}},
                          {'trans_a2': '21',
                           'trans_l2': [5, 6]}])
        self.assertRaises(AttributeError,
                          to_jsonable_partial_l, '_absentl')
        self.assertRaises(AttributeError,
                          to_jsonable_partial_l, '_absentl_ext')
        self.assertRaises(AttributeError,
                          to_jsonable_partial_l, '_absentl_ext_ext')
        self.assertRaises(AttributeError,
                          to_jsonable_partial_l, '_absentl_ext_ext_ext')

        ## With a datetime attribute
        self.assertEqual(self.jm._build_to_jsonable(None)('date'),
                         '12/09/2012 at 20:12:54')

        ## With something else
        self.assertEqual(self.jm._build_to_jsonable(None)('a'), '1')
        self.assertEqual(self.jm._build_to_jsonable(None)('a'), '1')
