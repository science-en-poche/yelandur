# -*- coding: utf-8 -*-

from unittest import skip

import ecdsa

from .models import User, Exp, Device, Profile
from .helpers import APITestCase, sha256hex


class ProfilesTestCase(APITestCase):

    def setUp(self):
        super(ProfilesTestCase, self).setUp()

        # Some users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.bill = User.get_or_create_by_email('bill@example.com')
        self.bill.set_user_id('bill')
        self.sophia = User.get_or_create_by_email('sophia@example.com')
        self.sophia.set_user_id('sophia')

        # Two experiments to work with
        self.exp_nd = Exp.create('numerical-distance', self.jane,
                                 'The numerical distance experiment, '
                                 'on smartphones', [self.bill])
        self.exp_gp = Exp.create('gender-priming', self.sophia,
                                 'Controversial gender priming effects')

        # Two devices to work with
        self.d1_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.d1 = Device.create(self.d1_sk.verifying_key.to_pem())
        self.d2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.d2 = Device.create(self.d2_sk.verifying_key.to_pem())

        ## Four profiles to work with

        # One with a device
        self.p1_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p1_vk = self.p1_sk.verifying_key
        self.p1_dict_public = {'profile_id': sha256hex(self.p1_vk.to_pem()),
                               'vk_pem': self.p1_vk.to_pem()}
        self.p1_dict_private = self.p1_dict_public.copy()
        self.p1_dict_private.extend({'exp_id': self.exp_nd['exp_id'],
                                     'device_id': self.d1.device_id,
                                     'data': {'occupation': 'student'},
                                     'n_results': 0})

        # A second without device
        self.p2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p2_vk = self.p2_sk.verifying_key
        self.p2_dict_public = {'profile_id': sha256hex(self.p2_vk.to_pem()),
                               'vk_pem': self.p2_vk.to_pem()}
        self.p2_dict_private = self.p2_dict_public.copy()
        self.p2_dict_private.extend({'exp_id': self.exp_gp['exp_id'],
                                     'data': {'occupation': 'social worker'},
                                     'n_results': 0})

        # A third and fourth for bad signing
        self.p3_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p4_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)

        # Error 400 missing signature
        self.error_400_missing_signature_dict = {}
            'error': {'status_code': 400,
                      'type': 'MissingSignature',
                      'message': 'A signature is missing for this operation'}}

        # Error 400 too many signatures
        self.error_400_too_many_signatures_dict = {}
            'error': {'status_code': 400,
                      'type': 'TooManySignatures',
                      'message': 'Too many signatures provided'}}

    def create_profiles(self):
        self.p1 = Profile.create(self.p1_vk.to_pem(),
                                 self.exp_nd, {'occupation': 'student'},
                                 self.d1)
        self.p2 = Profile.create(self.p2_vk.to_pem(),
                                 self.exp_gp, {'occupation': 'social worker'})

    @skip('not implemented yet')
    def test_profile_get_no_auth(self):
        self.create_profiles()

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_profile_get_with_auth(self):
        self.create_profiles()

        ## GET with auth to accessible profile (owner, collab)

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    @skip('not implemented yet')
    def test_profile_get_not_found(self):
        ### With auth

        ## GET with auth to privately-accessible profile

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ### Without auth

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    @skip('not implemented yet')
    def test_profile_put_data_successful(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'striker',
               'age': 25}}},
            self.p1_sk)
        self.p1_dict_private['data'].pop('occupation')
        self.p1_dict_private['data']['next_occupation'] = 'striker'
        self.p1_dict_private['data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            self.p2_sk)
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        ## And the same with ignore authentication

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_second_occupation': 'partier',
               'age': 26}}},
            self.p1_sk, self.sophia)
        self.p1_dict_private['data'].pop('next_occupation')
        self.p1_dict_private['data']['next_second_occupation'] = 'playerin'
        self.p1_dict_private['data']['age'] = 26
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_second_occupation': 'performer',
               'age': 31}}},
            self.p2_sk, self.sophia)
        self.p2_dict_private['data'].pop('next_occupation')
        self.p2_dict_private['data']['next_second_occupation'] = 'performer'
        self.p2_dict_private['data']['age'] = 31
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_data_ignore_additional_fields(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'striker',
               'age': 25},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p1_sk)
        self.p1_dict_private['data'].pop('occupation')
        self.p1_dict_private['data']['next_occupation'] = 'striker'
        self.p1_dict_private['data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'playerin',
               'age': 30},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p2_sk)
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_empty_data_empties(self):
        self.create_profiles()

        ## Pushing without any `data` field doesn't do anything

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile': {}}, self.p1_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile': {}}, self.p2_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        # Note that above, not providing a `device_id` field for p2 does not
        # remove the device from the device (that tie is irreversible).

        ## But pushing with an empty `data` field empties the data

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile': {'data': {}}}, self.p1_sk)
        self.p1_dict_private['data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile': {'data': {}}}, self.p2_sk)
        self.p2_dict_private['data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2.device_id}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['age'] = 30
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_empty_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'data': {}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['data'] = {}
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_data_ignore_additional_fields(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'data':
              {'next_occupation': 'playerin',
               'age': 30},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored'},
             'some-other-stuff': 'also-ignored'},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['data']['age'] = 30
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_404_not_found(self):
        # With only data posted
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'data':
                                        {'next_occupation': 'playerin',
                                         'age': 30}}},
                                      self.p2_sk)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With both data and device posted
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'data':
                                        {'next_occupation': 'playerin',
                                         'age': 30}}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    @skip('not implemented yet')
    def test_profile_put_404_not_found_error_priorities(self):
        # Malformed JSON presig
        data, status_code = self.put('/profiles/non-existing',
                                     '{"malformed JSON": "bla"',
                                     dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Malformed signature
        # (no `payload`)
        data, status_code = self.put('/profiles/non-existing',
                                     {'signatures':
                                      [{'protected': 'bla',
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (`payload` is not a base64url string)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': {},
                                      'signatures':
                                      [{'protected': 'bla',
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'abcde',  # Incorrect padding
                                      'signatures':
                                      [{'protected': 'bla',
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (no `signatures`)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla'})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (`signatures` is not a list)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures': 30})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures': {}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures': 'bli'})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (no `protected` in a signature)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (`protected is not a base64url string)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': {},
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 30,
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 'abcde',
                                        'signature': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (no `signature` in a signature)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 'bla'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (`signature` is not base64url a string)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 'bla',
                                        'signature': {}},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 'bla',
                                        'signature': 30},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.put('/profiles/non-existing',
                                     {'payload': 'bla',
                                      'signatures':
                                      [{'protected': 'bla',
                                        'signature': 'abcde'},
                                       {'protected': 'bla',
                                        'signature': 'bla'}]})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), device
        # does not exist, (invalid signature makes no sense with missing
        # signature), (device already taken makes no sense with device not
        # existing). `PUT`ing both data and device here, but the missing
        # signature implies that the device will automatically be ignored.
        data, status_code = self.put('/profiles/non-existing',
                                     {'profile':
                                      {'device_id': 'non-exising-device',
                                       'data': {'age': 30}}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), (invalid
        # signature makes no sense with missing signature), device already
        # taken. `PUT`ing both data and device here, but the missing signature
        # implies that the device will automatically be ignored.
        data, status_code = self.put('/profiles/non-existing',
                                     {'profile':
                                      {'device_id': self.d1.device_id,
                                       'data': {'age': 30}}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, malformed JSON postsig, invalid signature
        data, status_code = self.sput('/profiles/non-existing',
                                      '{"malformed JSON": "bla"',
                                      [self.p2_sk, self.d1_sk, self.d2_sk],
                                      dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, missing field (device_id), invalid signature
        # (profile, device), (device already taken makes no sense with device
        # not existing).
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'data': {'age': 30}}},
                                      [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, device does not exist, invalid signature
        # (profile, device), (device already taken makes no sense with device
        # does not exist)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'data': {'age': 30}}},
                                      [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, invalid signature (profile, device), device
        # already taken
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d1.device_id,
                                        'data': {'age': 30}}},
                                      [self.p2_sk, self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Malformed JSON postsig
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      '{"malformed JSON": "bla"',
                                      [self.p2_sk],
                                      dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      '{"malformed JSON": "bla"',
                                      [self.p2_sk, self.d2_sk],
                                      dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Missing field (device_id), (device does not exist makes no sense with
        # missing device_id), invalid signature (profile), (device already
        # taken makes no sense with missing device_id)
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'data': {'age': 30}}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'data': {'age': 30}}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Device does not exist, invalid signature (profile, device), (device
        # already taken makes no sense with device does not exist)
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'data': {'age': 30}}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'data': {'age': 30}}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Invalid signature (device, profile), device already taken
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d1.device_id,
                                        'data': {'age': 30}}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d1.device_id,
                                        'data': {'age': 30}}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Device already taken
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d1.device_id,
                                        'data': {'age': 30}}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d1.device_id,
                                        'data': {'age': 30}}},
                                      [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_presig(self):
        self.create_profiles()

        data, status_code = self.put('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            '{"malformed JSON": "bla"', dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(status_code, self.error_400_malformed_dict)

    # No error priorities test for malformed JSON since it excludes anything
    # else

    @skip('not implemented yet')
    def test_profile_put_400_malformed_signature(self):
        self.create_profiles()

        # (no `payload`)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'signatures':
             [{'protected': 'bla',
               'signature': 'bla'},
              {'protected': 'bla',
              'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`payload` is not a base64url string)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': {},
             'signatures':
             [{'protected': 'bla',
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'abcde',  # Incorrect padding
             'signatures':
             [{'protected': 'bla',
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signatures`)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']), {'payload': 'bla'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signatures` is not a list)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures': 30})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures': {}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures': 'bli'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `protected` in a signature)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`protected is not a base64url string)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': {},
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 30,
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'abcde',
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signature` in a signature)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signature` is not base64url a string)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla',
               'signature': {}},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla',
               'signature': 30},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.d2_dict['profile_id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla',
               'signature': 'abcde'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priorities test for malformed signature since it excludes
    # anything else

    @skip('not implemented yet')
    def test_profile_put_400_missing_signature(self):
        self.create_profiles()

        data, status_code = self.put('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'data': {'age': 30}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_signature_dict)

    @skip('not implemented yet')
    def test_profile_put_400_missing_signature_error_priorities(self):
        self.create_profiles()

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), device
        # does not exist, (invalid signature makes no sense with missing
        # signature), (device already taken makes no sense with device not
        # existing). `PUT`ing both data and device here, but the missing
        # signature implies that the device will automatically be ignored.
        data, status_code = self.put('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': 'non-exising-device',
              'data': {'age': 30}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_signature_dict)

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), (invalid
        # signature makes no sense with missing signature), device already
        # taken. `PUT`ing both data and device here, but the missing signature
        # implies that the device will automatically be ignored.
        data, status_code = self.put('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d1.device_id,
              'data': {'age': 30}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_signature_dict)

    @skip('not implemented yet')
    def test_profile_put_400_too_many_signatures(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'data': {'age': 30}}},
            [self.p2_sk, self.d2_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    @skip('not implemented yet')
    def test_profile_put_400_too_many_signatures_error_priorities(self):
        self.create_profiles()

        # Too many signatures, malformed JSON postsig, invalid signature
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), '{"malformed JSON": "bla"',
            [self.p1_sk, self.d1_sk, self.d2_sk], dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, missing field (device_id), invalid signature
        # (profile, device), (device already taken makes no sense with device
        # not existing).
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'data': {'age': 30}}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, device does not exist, invalid signature
        # (profile, device), (device already taken makes no sense with device
        # does not exist)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'data': {'age': 30}}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, invalid signature (profile, device), device
        # already taken
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d1.device_id,
              'data': {'age': 30}}},
            [self.p1_sk, self.p3_sk, self.d4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_postsig(self):
        self.create_profiles()

        # (with one signature)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), '{"malformed JSON": "bla"',
            [self.p2_sk], dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), '{"malformed JSON": "bla"',
            [self.p2_sk, self.d2_sk], dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_profile_put_400_missing_field(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), {'profile': {'data': {'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    @skip('not implemented yet')
    def test_profile_put_400_missing_field_error_priorities(self):
        self.create_profiles()

        # Missing field (device_id), (device does not exist makes no sense with
        # missing device_id), invalid signature (profile, device), (device
        # already taken makes no sense with missing device_id)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), {'profile': {'data': {'age': 30}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    @skip('not implemented yet')
    def test_profile_put_400_device_does_not_exist(self):
        # With or without added data
        pass

    @skip('not implemented yet')
    def test_profile_put_400_device_does_not_exist_error_priorities(self):
        # With or without added data
        pass

    @skip('not implemented yet')
    def test_profile_put_403_invalid_signature(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_403_invalid_signature_error_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_403_device_already_set(self):
        # For only p2
        pass

    @skip('not implemented yet')
    def test_profile_put_403_device_already_set_error_priorities(self):
        # For only p2
        pass

    @skip('not implemented yet')
    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/profiles', self.jane, False)
        # Redirects to '/profiles/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/profiles/')))

    @skip('not implemented yet')
    def test_root_get_no_auth(self):
        # Empty array or not

        # GET without auth
        # GET without auth with private access
        pass

    @skip('not implemented yet')
    def test_root_get_with_auth(self):
        # Empty array or not

        # GET with auth with private access
        # GET with auth with private access
        pass

    @skip('not implemented yet')
    def test_root_post_data_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_data_ignore_additional_data(self):
        # E.g. an additional `profile_id`
        pass

    @skip('not implemented yet')
    def test_root_post_data_complete_missing_fields(self):
        pass

    @skip('not implemented yet')
    def test_root_post_device_and_data_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_device_and_data_ignore_additional_data(self):
        # E.g. an additional `profile_id`
        pass

    @skip('not implemented yet')
    def test_root_post_complete_missing_fields(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_postsig(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_postsig_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_field(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_field_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_409_key_already_registered(self):
        pass

    @skip('not implemented yet')
    def test_root_post_409_key_already_registered_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_experiment_not_found(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_experiment_not_found_error_priorities(self):
        pass
