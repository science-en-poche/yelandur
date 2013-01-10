import unittest
import re

import ecdsa
import jws
from ecdsa.util import sigencode_der, sigdecode_string
from jws.utils import base64url_decode
import pymongo

from yelandur import init, helpers


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

    def test_build_gravatar_id(self):
        # One example case
        self.assertEqual(helpers.build_gravatar_id('johndoe@example.com'),
                         'fd876f8cd6a58277fc664d47ea10ad19',
                         'bad gravatar id')


class JsonifyTestCase(unittest.TestCase):

    def setUp(self):
        self.app = init.create_app(mode='test')

    def tearDown(self):
        c = pymongo.Connection()
        c.drop_database(self.app.config['MONGODB_DB'])
        c.close()

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


class JSONMixinTestCase(unittest.TestCase):

    def setUp(self):
        self.jm = helpers.JSONMixin()
        self.jm._jsonable1 = ['a']
        self.jm._jsonable1_ext = ['b']
        self.jm._jsonable2_ext = ['c']
        self.jm._jsonable2_ext_ext_ext = ['d']
        self.jm._jsonable3 = ['c']
        self.jm._jsonable5 = [(r'/^reg_([0-9])$/', r'\1_ins')]
        self.jm._jsonable5_ext = ['a']
        self.jm.a = [1, 2]
        self.jm.b = '2'
        self.jm.reg_1 = 'reg_1'
        self.jm.reg_2 = 'reg_2'

        nested_jm = helpers.JSONMixin()
        nested_jm._jsonable2 = ['aa']
        nested_jm._jsonable2_ext = ['bb']
        nested_jm._jsonable2_ext_ext = ['cc']
        nested_jm._jsonable3 = []
        nested_jm._jsonable5 = []
        nested_jm._jsonable5_ext = ['aa']
        nested_jm.aa = '11'
        nested_jm.bb = '22'
        nested_jm.cc = '33'

        self.jm.reg_3 = nested_jm
        self.jm.c = nested_jm
        self.jm.d = '4'

        self.bad_regexes = ['/test', 'test/', 'te/st', '/', '//']
        self.bad_counts = ['ntest', 'test', 'n_', 'n']

    def test__is_regex(self):
        msg = 'bad regex recognition'

        # Example of correct regex
        self.assertTrue(self.jm._is_regex('/test/'), msg)

        # Examples of incorrect regexes
        for br in self.bad_regexes:
            self.assertFalse(self.jm._is_regex(br), msg)

    def test__get_regex_string(self):
        # Example of correct regex
        self.assertEqual(self.jm._get_regex_string('/test/'), 'test',
                         'bad regex extraction')

        # Examples of incorrect regexes
        for br in self.bad_regexes:
            self.assertRaises(ValueError, self.jm._get_regex_string, br)

    def test__is_count(self):
        msg = 'bad count recognition'

        # Example of correct count
        self.assertTrue(self.jm._is_count('n_test'), msg)

        # Examples of incorrect counts
        for bc in self.bad_counts:
            self.assertFalse(self.jm._is_count(bc), msg)

    def test__get_count_string(self):
        # Example of correct count
        self.assertEqual(self.jm._get_count_string('n_test'), 'test',
                         'bad count string extraction')

        # Examples of incorrect counts
        for bc in self.bad_counts:
            self.assertRaises(ValueError, self.jm._get_count_string, bc)

    def test__get_includes(self):
        msg = 'bad includes getting'

        # Examples of includes
        self.assertEqual(self.jm._get_includes('_jsonable1'), ['a'], msg)
        self.assertEqual(self.jm._get_includes('_jsonable1_ext'), ['a', 'b'],
                         msg)
        self.assertEqual(self.jm._get_includes('_jsonable2'), [], msg)
        self.assertEqual(self.jm._get_includes('_jsonable2_ext'), ['c'], msg)
        self.assertEqual(self.jm._get_includes('_jsonable2_ext_ext'), ['c'],
                         msg)
        self.assertEqual(self.jm._get_includes('_jsonable2_ext_ext_ext'),
                         ['c', 'd'], msg)
        self.assertEqual(self.jm._get_includes('_jsonable0'), [], msg)

        # Examples of bad type strings
        self.assertRaises(ValueError, self.jm._get_includes, 'jsonable')
        self.assertRaises(ValueError, self.jm._get_includes, '_1jsonable')
        self.assertRaises(ValueError, self.jm._get_includes, '_jsonable_')

    def test__parse_preinc(self):
        msg = 'bad preinc parsing'

        # Examples of preincs to parse
        self.assertEqual(self.jm._parse_preinc('test'), ('test', 'test'), msg)
        self.assertEqual(self.jm._parse_preinc(('test', 'test')),
                         ('test', 'test'), msg)

    def test__find_type_string(self):
        msg = 'bad type string finding'

        # Example type strings
        self.assertEqual(self.jm._find_type_string('_jsonable1'),
                         '_jsonable1', msg)
        self.assertEqual(self.jm._find_type_string('_jsonable1_ext'),
                         '_jsonable1_ext', msg)
        self.assertEqual(self.jm._find_type_string('_jsonable2_ext'),
                         '_jsonable2_ext', msg)
        self.assertEqual(self.jm._find_type_string('_jsonable2_ext_ext'),
                         '_jsonable2_ext', msg)
        self.assertEqual(self.jm._find_type_string('_jsonable2_ext_ext_ext'),
                         '_jsonable2_ext_ext_ext', msg)

        # Example absent type strings
        self.assertRaises(AttributeError, self.jm._find_type_string,
                          '_jsonable2')
        self.assertRaises(AttributeError, self.jm._find_type_string,
                          '_jsonable0')

    def test__insert_jsonable(self):
        msg = 'bad jsonable insertion'

        # Example insertions
        res = {}
        self.jm._insert_jsonable('_jsonable1', res, ('a', 'a_ins'))
        self.assertEqual(res, {'a_ins': [1, 2]}, msg)

        res = {}
        self.jm._insert_jsonable('_jsonable1_ext', res, ('b', 'b_ins'))
        self.assertEqual(res, {'b_ins': '2'}, msg)

        res = {}
        self.jm._insert_jsonable('_jsonable2_ext', res, ('c', 'c_ins'))
        self.assertEqual(res, {'c_ins': {'aa': '11', 'bb': '22'}}, msg)

        res = {}
        self.jm._insert_jsonable('_jsonable2_ext_ext', res, ('c', 'c_ins'))
        self.assertEqual(res, {'c_ins': {'aa': '11', 'bb': '22', 'cc': '33'}},
                         msg)

        res = {}
        self.jm._insert_jsonable('_jsonable3', res, ('c', 'c_ins'))
        self.assertEqual(res, {}, msg)

        # If, in a nested attribute, no parent can be found for the given
        # type_string, an AttributeError should be raised.
        res = {}
        self.assertRaises(AttributeError, self.jm._insert_jsonable,
                          '_jsonable4', res, ('c', 'c_ins'))

    def test__insert_count(self):
        # Example insertions
        res = {}
        self.jm._insert_count(res, ('n_a', 'n_a_ins'))
        self.assertEqual(res, {'n_a_ins': 2}, 'bad count insertion')

    def test__insert_regex(self):
        msg = 'bad regex insertion'

        # Example insertions
        res = {}
        self.jm._insert_regex('_jsonable5', res,
                              (r'/^reg_([0-9])$/', r'\1_ins'))
        self.assertEqual(res, {'1_ins': 'reg_1', '2_ins': 'reg_2'}, msg)

        res = {}
        self.jm._insert_regex('_jsonable5_ext', res,
                              (r'/^reg_([0-9])$/', r'\1_ins'))
        self.assertEqual(res, {'1_ins': 'reg_1', '2_ins': 'reg_2',
                               '3_ins': {'aa': '11'}}, msg)
