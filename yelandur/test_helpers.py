# -*- coding: utf-8 -*-

import unittest
import re
from functools import partial
from datetime import datetime
from types import MethodType

import ecdsa
import jws
from ecdsa.util import sigencode_der, sigdecode_string
from jws.utils import base64url_decode
from mongoengine import Document, ListField, StringField, IntField
from werkzeug.datastructures import MultiDict

from . import create_app, models, helpers


class HashTestCase(unittest.TestCase):

    def test_hexregex(self):
        # Two example cases
        self.assertTrue(re.search(helpers.hexregex, '345abcf'),
                        'bad hexregex')
        self.assertFalse(re.search(helpers.hexregex, '345abdg'),
                         'bad hexregex')

    def test_nameregex(self):
        # Two example cases
        self.assertTrue(re.search(helpers.nameregex, 'some-good_name.dotted'),
                        'bad nameregex')
        self.assertTrue(re.search(helpers.nameregex, 'somegoodname'),
                        'bad nameregex')
        self.assertTrue(re.search(helpers.nameregex, 'somegoodname-123'),
                        'bad nameregex')
        self.assertTrue(re.search(helpers.nameregex, 'ru.p_h-us'),
                        'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, '-not-good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, '_not-good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not--good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not-_good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not__good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not-good-name-'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not-good-name_'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, '9not-good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, '.not-good-name'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not-good-name.'),
                         'bad nameregex')
        self.assertFalse(re.search(helpers.nameregex, 'not-good,name'),
                         'bad nameregex')

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


class TimeTestCase(unittest.TestCase):

    def test_iso8601(self):
        # Formatted datetimes are in the right format
        d = datetime(2013, 7, 6, 13, 6, 50, 653259)
        self.assertEqual(d.strftime(helpers.iso8601),
                         '2013-07-06T13:06:50.653259Z')


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
        self.app = create_app(mode='test')
        self.conn = self.app.extensions['mongoengine'].connection

        u = models.User.get_or_create_by_email('johndoe@example.com')
        u.set_user_id('john')
        e = models.Exp.create(name='test', owner=u)
        d = models.Device.create('device key')
        p = models.Profile.create('profile key', e, {'age': 20}, d)
        models.Result.create(p, {'trials': 12})

        # A test collection
        class TestDoc(Document):

            name = StringField()

        self.TestDoc = TestDoc
        TestDoc(name='doc1').save()

    def tearDown(self):
        if (self.app.config['MONGODB_SETTINGS']['db'][-5:] == '_test' and
                self.app.config['TESTING']):
            models.User.drop_collection()
            models.User.ensure_indexes()
            models.Exp.drop_collection()
            models.Exp.ensure_indexes()
            models.Device.drop_collection()
            models.Device.ensure_indexes()
            models.Profile.drop_collection()
            models.Profile.ensure_indexes()
            models.Result.drop_collection()
            models.Result.ensure_indexes()
            self.TestDoc.drop_collection()
            self.TestDoc.ensure_indexes()

    def test_wipe_test_database(self):
        # Check the database was created
        self.assertIn(self.app.config['MONGODB_SETTINGS']['db'],
                      self.conn.database_names())
        self.assertEquals(models.User.objects.count(), 1)
        self.assertEquals(models.Exp.objects.count(), 1)
        self.assertEquals(models.Device.objects.count(), 1)
        self.assertEquals(models.Profile.objects.count(), 1)
        self.assertEquals(models.Result.objects.count(), 1)
        self.assertEquals(self.TestDoc.objects.count(), 1)

        # Try wiping the database
        with self.app.test_request_context():
            helpers.wipe_test_database(self.TestDoc)

        self.assertEquals(models.User.objects.count(), 0)
        self.assertEquals(models.Exp.objects.count(), 0)
        self.assertEquals(models.Device.objects.count(), 0)
        self.assertEquals(models.Profile.objects.count(), 0)
        self.assertEquals(models.Result.objects.count(), 0)
        self.assertEquals(self.TestDoc.objects.count(), 0)

    def test_wipe_nontest_database(self):
        # Check the database was created
        self.assertIn(self.app.config['MONGODB_SETTINGS']['db'],
                      self.conn.database_names())
        self.assertEquals(models.User.objects.count(), 1)
        self.assertEquals(models.Exp.objects.count(), 1)
        self.assertEquals(models.Device.objects.count(), 1)
        self.assertEquals(models.Profile.objects.count(), 1)
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
        real_db_name = self.app.config['MONGODB_SETTINGS']['db']
        self.app.config['MONGODB_SETTINGS']['db'] = 'database_nontest'
        with self.app.test_request_context():
            self.assertRaises(ValueError, helpers.wipe_test_database,
                              self.TestDoc)

        # Reset the database name
        self.app.config['MONGODB_SETTINGS']['db'] = real_db_name


class ComputedSaveMixinTestCase(unittest.TestCase):

    def setUp(self):
        # Create test app
        self.app = create_app(mode='test')

        # A few test collections
        ## A properly configured one
        class TestDoc1(helpers.ComputedSaveMixin, Document):

            computed_lengths = [('many_names', 'n_names')]

            many_names = ListField(StringField())
            n_names = IntField()

        ## With a missing count field
        class TestDoc2(helpers.ComputedSaveMixin, Document):

            computed_lengths = [('many_things_missing', 'n_things')]

            many_things = ListField(StringField())
            # Missing `n_things`

        ## With a missing field to be counted
        class TestDoc3(helpers.ComputedSaveMixin, Document):

            computed_lengths = [('many_people', 'n_people')]

            # Missing list of people
            n_people = IntField()

        ## With bad ordering of superclasses
        class TestDoc4(Document, helpers.ComputedSaveMixin):

            computed_lengths = [('names', 'n_names_will_never_update')]

            names = ListField(StringField())
            n_names_will_never_update = IntField()

        self.TestDoc1 = TestDoc1
        self.doc1 = TestDoc1(name='doc1')
        self.TestDoc2 = TestDoc2
        self.doc2 = TestDoc2(name='doc2')
        self.TestDoc3 = TestDoc3
        self.doc3 = TestDoc3(name='doc3')
        self.TestDoc4 = TestDoc4
        self.doc4 = TestDoc4(name='doc4')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database(self.TestDoc1, self.TestDoc2,
                                       self.TestDoc3, self.TestDoc4)

    def test_update_computed_lengths(self):
        self.doc1.many_names = ['vincent', 'julia', 'valeria', 'seb']
        self.doc1.n_names = 42
        self.doc1.save()
        self.assertEqual(self.doc1.n_names, 4)

        self.doc1.many_names = ['frog', 'foo']
        self.doc1.n_names = 42
        self.doc1.save()
        self.assertEqual(self.doc1.n_names, 2)

    def test_update_computed_lengths_missing_count(self):
        self.assertRaises(AttributeError, self.doc2.save)

    def test_update_computed_lengths_missing_original_field(self):
        self.assertRaises(AttributeError, self.doc3.save)

    def test_update_computed_lengths_bad_superclass_ordering(self):
        self.doc4.many_names = ['al', 'thames', 'whatever']
        self.doc4.save()
        self.assertEqual(self.doc4.n_names_will_never_update, None)

        self.doc4.many_names = ['cat', 'dog']
        self.doc4.n_names_will_never_update = 36
        self.doc4.save()
        self.assertEqual(self.doc4.n_names_will_never_update, 36)


class TypeStringTester(unittest.TestCase):

    def setUp(self):
        self.bad_regexes = ['/test', 'test/', 'te/st', '/', '//']
        self.bad_deeps = ['test__attr__attr2']

        ############################
        # The instances to work with
        ############################
        self.jm = helpers.JSONDocumentMixin()
        self.jm1 = helpers.JSONDocumentMixin()
        self.jm2 = helpers.JSONDocumentMixin()
        self.jm11 = helpers.JSONDocumentMixin()
        self.jm12 = helpers.JSONDocumentMixin()

        ##################
        # Their attributes
        ##################

        # Basics, for basic inheritance
        self.jm.a = '1'
        self.jm.a_int = 1
        self.jm.l = [1, 2]
        self.jm.date = datetime(2012, 9, 12, 20, 12, 54, 123456)

        self.jm1.a1 = '11'
        self.jm1.b = 'jm1_b'
        self.jm1.l1 = [3, 4]

        self.jm2.a2 = '21'
        self.jm2.b = 'jm2_b'
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
        self.jm._count = [('l_jm__count', 'n_l_jm')]
        self.jm._count_ext = ['l_jm']

        self.jm1._count = [('l1_jm__count', 'n_l1_jm')]
        self.jm1._count_ext = ['l1_jm']

        self.jm2._count = [('l2__count', 'n_l2')]

        self.jm11._count = [('l11__count', 'n_l11')]

        self.jm12._count = [('l12__count', 'n_l12')]

        ## Regexes, with nested objects
        self.jm._regex = [(r'/^jm([0-9])$/', r'trans_jm\1')]

        self.jm1._regex = [(r'/^jm1([0-9])$/', r'trans_jm1\1')]

        self.jm2._regex = [(r'/^([a-z])2$/', r'trans_\g<1>2')]

        self.jm11._regex = [(r'/^([a-z])11$/', r'trans_\g<1>11')]

        self.jm12._regex = [(r'/^([a-z])12$/', r'trans_\g<1>12')]

        ## Deep attributes
        self.jm._deep = [('jm1__a1', 'jm1_a1'),
                         ('jm2__l2', 'jm2_l2'),
                         'jm1',
                         ('jm1__l1_jm', 'jm1_l1_jm')]
        self.jm1._deep = [('jm11__a11', 'jm11_a11'),
                          ('jm12__l12', 'jm12_l12')]
        self.jm11._deep = ['a11']
        self.jm12._deep = ['l12']

        ## Deep attributes with lists
        self.jm._listdeep = [('l_jm__b', 'l_jm_bs')]

        ## Wrong deep attributes
        self.jm._wrongdeep = [('jm1__c', 'jm1_c')]
        self.jm._toodeep = [('jm1__jm11__a11', 'jm1_jm11_a11')]
        self.jm._wrongdeepcount = [('a_int__count', 'n_a_int')]

        ## Default-valued attributes
        self.jm._defval = [('c', 'will_not_appear', None),
                           ('d', 'default_d', 'd_def'),
                           'l_jm']
        self.jm1._defval = [('c1', 'will_not_appear', None),
                            ('d1', 'default_d1', 'd1_def')]
        self.jm2._defval = [('c2', 'will_not_appear', None),
                            ('d2', 'default_d2', 'd2_def')]

        ## Default-valued deep attributes
        self.jm._deepdefval = [('jm1__c1', 'will_not_appear', None),
                               ('l_jm__a1', 'only_jm1_a1', None),
                               'jm1']
        self.jm1._deepdefval = [('jm11__c11', 'default_c11', 'c11_def'),
                                ('l1_jm__a11', 'only_jm11_a11', 'jm12_def')]


class TypeStringParserMixinTestCase(TypeStringTester):

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

    def test__parse_preinc(self):
        # Examples of preincs to parse
        self.assertEqual(self.jm._parse_preinc('test'), ('test', 'test'))
        self.assertEqual(self.jm._parse_preinc(('test', 'trans_test')),
                         ('test', 'trans_test'))

    def test__parse_deep_attr_name(self):
        # Examples of deep attribute names
        self.assertEqual(self.jm._parse_deep_attr_name('attr_nondeep'),
                         ['attr_nondeep'])
        self.assertEqual(self.jm._parse_deep_attr_name('attr__deep'),
                         ['attr', 'deep'])
        self.assertRaises(ValueError, self.jm._parse_deep_attr_name,
                          'attr__too__deep')

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


class JSONIteratableTestCase(unittest.TestCase):

    def setUp(self):
        # Init the app to access the database
        self.app = create_app(mode='test')

        # A test collection using the JSONDocumentMixin. That should
        # also bring the JSONQuerySet along (through the `meta`
        # attribute).
        class TestDoc(Document, helpers.JSONDocumentMixin):

            _test = ['name']
            _empty = []
            _something = ['stuff',
                          ('sub__attr', 'sub_attr', 'default_value'),
                          (r'/someregex/', 'ignored')]
            _something_ext = [('more__stuff', 'more_stuff')]

            name = StringField()

        self.TestDoc = TestDoc
        d1 = TestDoc(name='doc1').save()
        d2 = TestDoc(name='doc2').save()
        d3 = TestDoc(name='doc3').save()

        self.qs = TestDoc.objects
        # d3 is there twice to make sure it is removed in the final set
        self.s = helpers.JSONSet(TestDoc, [d1, d2, d3, d3])

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database(self.TestDoc)

    def _test__to_jsonable(self, it):
        self.assertEqual(len(it), 3)

        # Basic usage, with inheritance
        self.assertEqual(set([d['name'] for d in
                              it._to_jsonable('_test')]),
                         {'doc1', 'doc2', 'doc3'})
        self.assertEqual(set([d['name'] for d in
                              it._to_jsonable('_test_ext')]),
                         {'doc1', 'doc2', 'doc3'})

        # Exception raised if empty jsonable
        self.assertRaises(helpers.EmptyJsonableException,
                          it._to_jsonable, '_empty')

    def test__to_jsonable_query_set(self):
        self._test__to_jsonable(self.qs)

    def test__to_jsonable_set(self):
        self._test__to_jsonable(self.s)

    def _test__translate_to(self, it):
        query = {'ignored': 'bla',
                 'stuff': 'blabla',
                 'sub_attr': 'more_bla',
                 'excluded': 123,
                 'more_stuff__with__query': 456,
                 'more_stuff__other__query': 789}

        # An empty TypeString raises an exception
        self.assertRaises(helpers.EmptyJsonableException,
                          it._translate_to, '_empty', query)

        # Otherwise: it includes only arguments in the type-string,
        # ignores regexps, renames everything properly
        self.assertEqual(it._translate_to('_something', query),
                         {'stuff': 'blabla',
                          'sub__attr': 'more_bla'})
        self.assertEqual(it._translate_to('_something_ext', query),
                         {'stuff': 'blabla',
                          'sub__attr': 'more_bla',
                          'more__stuff__with__query': 456,
                          'more__stuff__other__query': 789})

    def test__translate_to_query_set(self):
        self._test__translate_to(self.qs)

    def test__translate_to_set(self):
        self._test__translate_to(self.s)

    def _test__translate_order_to(self, it):
        query = MultiDict([('ignored', 'bla'),
                           ('stuff', 'blabla'),
                           ('sub_attr', 'more_bla'),
                           ('excluded', 123),
                           ('more_stuff__with__query', 456),
                           ('more_stuff__other__query', 789),
                           ('order', 'stuff'),
                           ('order', 'excluded'), ('order', 'ignored'),
                           ('order', 'sub_attr__with__query'),
                           ('order', 'more_stuff'),
                           ('order', 'more_stuff__with__morequery')])
        noorder_query = MultiDict([('ignored', 'bla'),
                                   ('stuff', 'blabla'),
                                   ('sub_attr', 'more_bla')])

        # An empty TypeString raises an exception
        self.assertRaises(helpers.EmptyJsonableException,
                          it._translate_order_to, '_empty', query)

        # Otherwise: it includes only arguments in the type-string,
        # ignores regexps, renames everything properly
        self.assertEqual(it._translate_order_to('_something', query),
                         ['stuff', 'sub__attr__with__query'])
        self.assertEqual(it._translate_order_to('_something_ext', query),
                         ['stuff', 'sub__attr__with__query',
                          'more__stuff', 'more__stuff__with__morequery'])
        self.assertEqual(it._translate_order_to('_something_ext', noorder_query),
                         [])

    def test__translate_order_to_query_set(self):
        self._test__translate_order_to(self.qs)

    def test__translate_order_to_set(self):
        self._test__translate_order_to(self.s)

    def _test__build_to_jsonable(self, it):
        self.assertEqual(len(it), 3)

        # Basic usage, with inheritance
        self.assertEqual(set([d['name'] for d in
                              it._build_to_jsonable('_test')()]),
                         {'doc1', 'doc2', 'doc3'})
        self.assertEqual(set([d['name'] for d in
                              it._build_to_jsonable('_test_ext')()]),
                         {'doc1', 'doc2', 'doc3'})

        # No exception is raised if empty jsonable
        self.assertEqual(it._build_to_jsonable('_empty')(), None)

    def test__build_to_jsonable_query_set(self):
        self._test__build_to_jsonable(self.qs)

    def test__build_to_jsonable_set(self):
        self._test__build_to_jsonable(self.s)

    def _test__build_translate_to(self, it):
        query = {'excluded': 'bla',
                 'name': 'gobble'}

        # Basic usage, with inheritance
        # (checking the proper method is called)
        self.assertEqual(it._build_translate_to('_test')(query),
                         {'name': 'gobble'})
        self.assertEqual(it._build_translate_to('_test_ext')(query),
                         {'name': 'gobble'})

        # No exception is raised if empty jsonable
        self.assertEqual(it._build_translate_to('_empty')(query), None)

    def test__build_translate_to_query_set(self):
        self._test__build_translate_to(self.qs)

    def test__build_translate_to_set(self):
        self._test__build_translate_to(self.s)

    def _test__build_translate_order_to(self, it):
        query = MultiDict([('excluded', 'bla'),
                           ('name', 'gobble'),
                           ('order', 'name'),
                           ('order', 'excluded')])
        noorder_query = MultiDict([('excluded', 'bla'),
                                   ('name', 'gobble')])

        # Basic usage, with inheritance
        # (checking the proper method is called)
        self.assertEqual(it._build_translate_order_to('_test')(query),
                         ['name'])
        self.assertEqual(it._build_translate_order_to('_test_ext')(query),
                         ['name'])
        self.assertEqual(
            it._build_translate_order_to('_test_ext')(noorder_query), [])

        # No exception is raised if empty jsonable
        self.assertEqual(it._build_translate_order_to('_empty')(query), None)

    def test__build_translate_order_to_query_set(self):
        self._test__build_translate_order_to(self.qs)

    def test__build_translate_order_to_set(self):
        self._test__build_translate_order_to(self.s)

    def _test___getattribute__(self, it):
        # Regular attributes are found
        it.__class__.a = '1'
        self.assertEqual(it.__getattribute__('a'), '1')

        # Asking for `to_` returns the attribute
        it.__class__.to_ = 'to'
        it._document.to_ = 'document_to'
        self.assertEqual(it.__getattribute__('to_'), 'to')

        # Asking for 'translate_to_' returns the attribute
        it.__class__.translate_to_ = 'translate_to'
        it._document.translate_to_ = 'document_translate_to'
        self.assertEqual(it.__getattribute__('translate_to_'), 'translate_to')

        # to_* attributes raise an exception if the _* type_string isn't
        # defined in the Document class and the to_* attribute doesn't exist.
        self.assertRaises(AttributeError, it.__getattribute__,
                          'to_absent')

        # Same for 'tranlsate_to_*'
        self.assertRaises(AttributeError, it.__getattribute__,
                          'tranlsate_to_absent')

        # If the attribute exists (but not the type_string in the Document
        # class), the attribute is found.
        it.__class__.to_foo = 'bar'
        self.assertEqual(it.__getattribute__('to_foo'), 'bar')

        # Same for 'translate_to_*'
        it.__class__.translate_to_foo = 'bar'
        self.assertEqual(it.__getattribute__('translate_to_foo'), 'bar')

        # But if the attribute exists as well as the type_string in the
        # Document class, the type_string shadows the attribute.
        it.__class__.to_foo = 'bar'
        it._document._foo = ['a']
        self.assertIsInstance(it.__getattribute__('to_foo'), MethodType)

        # Same for 'translate_to_*'
        it.__class__.translate_to_foo = 'bar'
        it._document._foo = ['a']
        self.assertIsInstance(it.__getattribute__('translate_to_foo'),
                              MethodType)

        # `to_mongo` is skipped even if _mongo type_string exists
        it._document._mongo = ['gobble']
        self.assertRaises(AttributeError, it.__getattribute__,
                          'to_mongo')

    def test___getattribute___query_set(self):
        self._test___getattribute__(self.qs)

    def test___getattribute___set(self):
        self._test___getattribute__(self.s)


class JSONDocumentMixinTestCase(TypeStringTester):

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

        # Deep attributes
        self.assertEqual(to_jsonable('_deep'),
                         {'jm1_a1': '11', 'jm2_l2': [5, 6],
                          'jm1': {'jm11_a11': '111', 'jm12_l12': [9, 10]},
                          'jm1_l1_jm': [{'a11': '111'}, {'l12': [9, 10]}]})
        self.assertEqual(to_jsonable('_listdeep'),
                         {'l_jm_bs': ['jm1_b', 'jm2_b']})
        self.assertRaises(AttributeError, to_jsonable, '_wrongdeep')
        self.assertRaises(ValueError, to_jsonable, '_toodeep')
        self.assertRaises(AttributeError, to_jsonable, '_wrongdeepcount')

        # Default-valued attributes
        self.assertEqual(to_jsonable('_defval'),
                         {'default_d': 'd_def',
                          'l_jm': [{'default_d1': 'd1_def'},
                                   {'default_d2': 'd2_def'}]})

        # Default-valued deep attributes
        self.assertEqual(to_jsonable('_deepdefval'),
                         {'only_jm1_a1': ['11'],
                          'jm1': {'default_c11': 'c11_def',
                                  'only_jm11_a11': ['111', 'jm12_def']}})

    def test__to_jsonable(self):
        # Examine all cases not involving EmptyJsonableException
        self.to_jsonable_all_but_empty(self.jm._to_jsonable)

        # The special case of EmptyJsonableException
        self.assertRaises(helpers.EmptyJsonableException,
                          self.jm._to_jsonable, '_empty')

    def test__jsonablize(self):
        ## With a raw attribute, not an attribute name

        # With a JSONDocumentMixin attribute
        attr_jsonablize = partial(self.jm._jsonablize, attr_or_name=self.jm,
                                  is_attr_name=False)
        self.to_jsonable_all_but_empty(attr_jsonablize)
        self.assertRaises(helpers.EmptyJsonableException, attr_jsonablize,
                          '_empty')

        # With a JSONDocumentMixin attribute, from attribute name
        parent_jm = helpers.JSONDocumentMixin()
        parent_jm.jm = self.jm
        attr_jsonablize = partial(parent_jm._jsonablize, attr_or_name='jm',
                                  is_attr_name=True)
        self.to_jsonable_all_but_empty(attr_jsonablize)
        self.assertRaises(helpers.EmptyJsonableException, attr_jsonablize,
                          '_empty')

        # The following tests do not do full checks, they just make sure
        # _jsonablized forwards the attributes to the right subfunction.

        # With list attributes
        self.assertEqual(self.jm._jsonablize('_regex',
                                             [self.jm1, self.jm2],
                                             is_attr_name=False),
                         [{'trans_jm11': {'trans_a11': '111',
                                          'trans_l11': [7, 8]},
                           'trans_jm12': {'trans_a12': '121',
                                          'trans_l12': [9, 10]}},
                          {'trans_a2': '21',
                           'trans_l2': [5, 6]}])
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl', [self.jm1, self.jm2],
                          is_attr_name=False)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext', [self.jm1, self.jm2],
                          is_attr_name=False)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext_ext', [self.jm1, self.jm2],
                          is_attr_name=False)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext_ext_ext', [self.jm1, self.jm2],
                          is_attr_name=False)

        # With list attributes, from attribute name
        self.assertEqual(self.jm._jsonablize('_regex', 'l_jm',
                                             is_attr_name=True),
                         [{'trans_jm11': {'trans_a11': '111',
                                          'trans_l11': [7, 8]},
                           'trans_jm12': {'trans_a12': '121',
                                          'trans_l12': [9, 10]}},
                          {'trans_a2': '21',
                           'trans_l2': [5, 6]}])
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl', 'l_jm', is_attr_name=True)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext', 'l_jm', is_attr_name=True)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext_ext', 'l_jm', is_attr_name=True)
        self.assertRaises(AttributeError, self.jm._jsonablize,
                          '_absentl_ext_ext_ext', 'l_jm',
                          is_attr_name=True)

        # With a datetime attribute
        self.assertEqual(self.jm._jsonablize(None, self.jm.date,
                                             is_attr_name=False),
                         '2012-09-12T20:12:54.123456Z')

        # With a datetime attribute, from attribute name
        self.assertEqual(self.jm._jsonablize(None, 'date',
                                             is_attr_name=True),
                         '2012-09-12T20:12:54.123456Z')

        # With something else
        self.assertEqual(self.jm._jsonablize(None, self.jm.a,
                                             is_attr_name=False), '1')

        # With something else, from attribute name
        self.assertEqual(self.jm._jsonablize(None, 'a',
                                             is_attr_name=True), '1')

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

        ## With JSONDocumentMixin attribute
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
                         '2012-09-12T20:12:54.123456Z')

        ## With something else
        self.assertEqual(self.jm._build_to_jsonable(None)('a'), '1')
        self.assertEqual(self.jm._build_to_jsonable(None)('a'), '1')
