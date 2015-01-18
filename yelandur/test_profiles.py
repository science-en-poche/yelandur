# -*- coding: utf-8 -*-

import ecdsa

from .models import User, Exp, Device, Profile
from .helpers import APITestCase, sha256hex


# TODO: add CORS test

# ## TODO: URL-query tests

# get public
#   get with some operators on public fields numbers/strings/lists,
#       with combinations and ids
#   get with some operators on private fields numbers/strings/lists,
#       with combinations and ids, ignored
#   get with some operators on unexisting fields numbers/strings/lists,
#       with combinations and ids, ignored
#   get with date, combinations
#   get with date list, combinations
#   get with order, combinations
#   get with order on private or unexisting field, combinations, ignored
#   get with limit
#   error with malformed query on valid field: unknown operator, too deep
#   error on not string/number/date/list of {string,number,date} field
#   error on regexp on not string or list of string field
#   error with un-parsable number
#   error with malformed date query value
#   error with limit as non-number
#   error with order on non-number/string/date field

# get private
#   get with some operators on public fields numbers/strings/lists,
#       with combinations and ids
#   get with some operators on private fields numbers/strings/lists,
#       with combinations and ids
#   get with some operators on unexisting fields numbers/strings/lists,
#       with combinations and ids, ignored
#   get with order, combinations
#   get with order on private or unexisting field, combinations, ignored
#   get with limit
#   error with malformed query on valid field: unknown operator, too deep
#   error on not string/number/date/list of {string,number,date} field
#   error on regexp on not string or list of string field
#   error with un-parsable number
#   error with malformed date query value
#   error with limit as non-number
#   error with order on non-number/string/date field


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
        self.p1_dict_public = {'id': sha256hex(self.p1_vk.to_pem()),
                               'vk_pem': self.p1_vk.to_pem()}
        self.p1_dict_private = self.p1_dict_public.copy()
        self.p1_dict_private.update(
            {'exp_id': self.exp_nd.exp_id,
             'device_id': self.d1.device_id,
             'profile_data': {'occupation': 'student'},
             'n_results': 0})

        # A second without device
        self.p2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p2_vk = self.p2_sk.verifying_key
        self.p2_dict_public = {'id': sha256hex(self.p2_vk.to_pem()),
                               'vk_pem': self.p2_vk.to_pem()}
        self.p2_dict_private = self.p2_dict_public.copy()
        self.p2_dict_private.update(
            {'exp_id': self.exp_gp.exp_id,
             'profile_data': {'occupation': 'social worker'},
             'device_id': None,
             'n_results': 0})

        # A third and fourth for bad signing
        self.p3_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p4_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)

        # Error 400 too many signatures
        self.error_400_too_many_signatures_dict = {
            'error': {'status_code': 400,
                      'type': 'TooManySignatures',
                      'message': 'Too many signatures provided'}}

        # Error 400 device does not exist
        self.error_400_device_does_not_exist_dict = {
            'error': {'status_code': 400,
                      'type': 'DeviceNotFound',
                      'message': 'The requested device was not found'}}

        # Error 400 experiment does not exist
        self.error_400_experiment_does_not_exist_dict = {
            'error': {'status_code': 400,
                      'type': 'ExperimentNotFound',
                      'message': 'The requested experiment was not found'}}

        # Error 403 invalid signature
        self.error_403_invalid_signature_dict = {
            'error': {'status_code': 403,
                      'type': 'BadSignature',
                      'message': 'The signature is invalid'}}

        # Error 403 device already set
        self.error_403_device_already_set_dict = {
            'error': {'status_code': 403,
                      'type': 'DeviceAlreadySet',
                      'message': 'Device is already set'}}

    def create_profiles(self):
        self.p1 = Profile.create(self.p1_vk.to_pem(),
                                 self.exp_nd, {'occupation': 'student'},
                                 self.d1)
        self.p2 = Profile.create(self.p2_vk.to_pem(),
                                 self.exp_gp, {'occupation': 'social worker'})

    def test_profile_get_no_auth(self):
        self.create_profiles()

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_profile_get_with_auth(self):
        self.create_profiles()

        ## GET with auth to accessible profile (owner, collab)

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # As owner without a device
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['id']), self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # As owner without device
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['id']), self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['id']), self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_profile_get_not_found(self):
        ### With auth

        ## GET with auth to privately-accessible profile

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ### Without auth

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    def test_profile_put_data_successful(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_occupation': 'striker',
               'age': 25}}},
            self.p1_sk)
        self.p1_dict_private['profile_data'].pop('occupation')
        self.p1_dict_private['profile_data']['next_occupation'] = 'striker'
        self.p1_dict_private['profile_data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            self.p2_sk)
        self.p2_dict_private['profile_data'].pop('occupation')
        self.p2_dict_private['profile_data']['next_occupation'] = 'playerin'
        self.p2_dict_private['profile_data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        ## And the same with ignore authentication

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_second_occupation': 'partier',
               'age': 26}}},
            self.p1_sk, self.sophia)
        self.p1_dict_private['profile_data'].pop('next_occupation')
        self.p1_dict_private['profile_data'][
            'next_second_occupation'] = 'partier'
        self.p1_dict_private['profile_data']['age'] = 26
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_second_occupation': 'performer',
               'age': 31}}},
            self.p2_sk, self.sophia)
        self.p2_dict_private['profile_data'].pop('next_occupation')
        self.p2_dict_private['profile_data'][
            'next_second_occupation'] = 'performer'
        self.p2_dict_private['profile_data']['age'] = 31
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_data_ignore_additional_fields(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_occupation': 'striker',
               'age': 25},
              'id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p1_sk)
        self.p1_dict_private['profile_data'].pop('occupation')
        self.p1_dict_private['profile_data']['next_occupation'] = 'striker'
        self.p1_dict_private['profile_data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'profile_data':
              {'next_occupation': 'playerin',
               'age': 30},
              'id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p2_sk)
        self.p2_dict_private['profile_data'].pop('occupation')
        self.p2_dict_private['profile_data']['next_occupation'] = 'playerin'
        self.p2_dict_private['profile_data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_empty_data_empties(self):
        self.create_profiles()

        ## Pushing without any `data` field doesn't do anything

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['id']),
            {'profile': {}}, self.p1_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile': {}}, self.p2_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        # Note that above, not providing a `device_id` field for p2 does not
        # remove the device from the device (that tie is irreversible).

        ## But pushing with an empty `data` field empties the data

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['id']),
            {'profile': {'profile_data': {}}}, self.p1_sk)
        self.p1_dict_private['profile_data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile': {'profile_data': {}}}, self.p2_sk)
        self.p2_dict_private['profile_data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_device_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'device_id': self.d2.device_id}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_device_reversed_signatures_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'device_id': self.d2.device_id}},
            [self.d2_sk, self.p2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_device_and_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['profile_data'].pop('occupation')
        self.p2_dict_private['profile_data']['next_occupation'] = 'playerin'
        self.p2_dict_private['profile_data']['age'] = 30
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_device_and_empty_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['profile_data'] = {}
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_device_and_data_ignore_additional_fields(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data':
              {'next_occupation': 'playerin',
               'age': 30},
              'id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored'},
             'some-other-stuff': 'also-ignored'},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2.device_id
        self.p2_dict_private['profile_data'].pop('occupation')
        self.p2_dict_private['profile_data']['next_occupation'] = 'playerin'
        self.p2_dict_private['profile_data']['age'] = 30
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_profile_put_404_not_found(self):
        # With only data posted
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'profile_data':
                                        {'next_occupation': 'playerin',
                                         'age': 30}}},
                                      self.p2_sk)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With both data and device posted
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'profile_data':
                                        {'next_occupation': 'playerin',
                                         'age': 30}}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

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
        # signature), malformed data dict, (device already set makes no sense
        # with profile not existing). `PUT`ing both data and device here,
        # but the missing # signature implies that the device will
        # automatically be ignored.
        data, status_code = self.put('/profiles/non-existing',
                                     {'profile':
                                      {'device_id': 'non-exising-device',
                                       'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # Too many signatures, malformed JSON postsig, invalid signature
        #data, status_code = self.sput('/profiles/non-existing',
                                      #'{"malformed JSON": "bla"',
                                      #[self.p2_sk, self.d1_sk, self.d2_sk],
                                      #dump_json_data=False)
        #self.assertEqual(status_code, 404)
        #self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, missing field (device_id), invalid signature
        # (profile, device), malformed data dict, (device already set makes
        # no sense with profile not existing).
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'profile_data': 'non-dict'}},
                                      [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Too many signatures, device does not exist, invalid signature
        # (profile, device), malformed data dict, (device already set makes
        # no sense with profile does not exist)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'profile_data': 'non-dict'}},
                                      [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # Malformed JSON postsig
        # (with one signature)
        #data, status_code = self.sput('/profiles/non-existing',
                                      #'{"malformed JSON": "bla"',
                                      #[self.p2_sk],
                                      #dump_json_data=False)
        #self.assertEqual(status_code, 404)
        #self.assertEqual(data, self.error_404_does_not_exist_dict)

        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # (with two signatures)
        #data, status_code = self.sput('/profiles/non-existing',
                                      #'{"malformed JSON": "bla"',
                                      #[self.p2_sk, self.d2_sk],
                                      #dump_json_data=False)
        #self.assertEqual(status_code, 404)
        #self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Missing field (device_id), (device does not exist makes no sense with
        # missing device_id), invalid signature (profile), malformed data dict,
        # (device already set makes no sense with profile not existing)
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'profile_data': 'non-dict'}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'profile_data': 'non-dict'}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Device does not exist, invalid signature (profile, device),
        # malformed data dict, (device already set makes no sense with
        # profile does not exist) (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'profile_data': 'non-dict'}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': 'non-existing',
                                        'profile_data': 'non-dict'}},
                                      [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Invalid signature (device, profile), malformed data dict
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'profile_data': 'non-dict'}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'profile_data': 'non-dict'}},
                                      [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Invalid signature (device, profile)
        # (with one signature)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'profile_data': {'age': 30}}},
                                      [self.p2_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # (with two signatures)
        data, status_code = self.sput('/profiles/non-existing',
                                      {'profile':
                                       {'device_id': self.d2.device_id,
                                        'profile_data': {'age': 30}}},
                                      [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    def test_profile_put_400_malformed_json_presig(self):
        self.create_profiles()

        data, status_code = self.put('/profiles/{}'.format(
            self.p1_dict_public['id']),
            '{"malformed JSON": "bla"', dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priorities test for malformed JSON since it excludes anything
    # else

    def test_profile_put_400_malformed_signature(self):
        self.create_profiles()

        # (no `payload`)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'signatures':
             [{'protected': 'bla',
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`payload` is not a base64url string)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': {},
             'signatures':
             [{'protected': 'bla',
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
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
            self.p2_dict_public['id']), {'payload': 'bla'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signatures` is not a list)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures': 30})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures': {}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures': 'bli'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `protected` in a signature)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`protected is not a base64url string)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': {},
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 30,
               'signature': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
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
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla'},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signature` is not base64url a string)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla',
               'signature': {}},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
            {'payload': 'bla',
             'signatures':
             [{'protected': 'bla',
               'signature': 30},
              {'protected': 'bla',
               'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.put('/profiles/{}'.format(
            self.p2_dict_public['id']),
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

    def test_profile_put_400_missing_signature(self):
        self.create_profiles()

        data, status_code = self.put('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_profile_put_400_missing_signature_error_priorities(self):
        self.create_profiles()

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), device
        # does not exist, (invalid signature makes no sense with missing
        # signature), malformed data dict, device already set. `PUT`ing both
        # data and device here, but the missing signature implies that the
        # device will automatically be ignored.
        data, status_code = self.put('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': 'non-exising-device',
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), (invalid
        # signature makes no sense with missing signature), malformed data
        # dict, device already set. `PUT`ing both data and device here, but
        # the missing signature implies that the device will automatically
        # be ignored.
        data, status_code = self.put('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Missing signature, (too many signatures makes no sense with missing
        # signature), (malformed JSON postsig then amounts to malformed JSON
        # presig), (missing field only makes sense if we're in the
        # device-setting scenario because of two signatures present), (invalid
        # signature makes no sense with missing signature), device already
        # set. `PUT`ing both data and device here, but the missing signature
        # implies that the device will automatically be ignored.
        data, status_code = self.put('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d1.device_id,
              'profile_data': {'age': 30}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_profile_put_400_too_many_signatures(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p2_sk, self.d2_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    def test_profile_put_400_too_many_signatures_error_priorities(self):
        self.create_profiles()

        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # Too many signatures, malformed JSON postsig, invalid signature
        #data, status_code = self.sput('/profiles/{}'.format(
            #self.p2.profile_id), '{"malformed JSON": "bla"',
            #[self.p1_sk, self.d1_sk, self.d2_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, missing field (device_id), invalid signature
        # (profile, device), malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'profile_data': 'non-dict'}},
            [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, device does not exist, invalid signature
        # (profile, device), malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, invalid signature (profile, device),
        # malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d2_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Too many signatures, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p1_sk, self.d2_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    # FIXME: can't do this test yet since python-jws checks for JSON
    # conformity before signing.

    #def test_profile_put_400_malformed_json_postsig(self):
        #self.create_profiles()

        ## (with one signature)
        #data, status_code = self.sput('/profiles/{}'.format(
            #self.p2.profile_id), '{"malformed JSON": "bla"',
            #[self.p2_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

        ## (with two signatures)
        #data, status_code = self.sput('/profiles/{}'.format(
            #self.p2.profile_id), '{"malformed JSON": "bla"',
            #[self.p2_sk, self.d2_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    def test_profile_put_400_missing_field(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), {'profile': {'profile_data': {'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), {'no-profile': {'profile_data': {'age': 30}}},
            self.p2_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_profile_put_400_missing_field_error_priorities(self):
        self.create_profiles()

        # Missing field (device_id), (device does not exist makes no sense with
        # missing device_id), invalid signature (profile, device),
        # malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id), {'profile': {'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field, malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id), {'profile': {'profile_data': 'non-dict'}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id), {'profile': {'profile_data': {'age': 30}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_profile_put_400_device_does_not_exist(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'profile_data': {'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

    def test_profile_put_400_device_does_not_exist_error_priorities(self):
        self.create_profiles()

        # Device does not exist, invalid signature (profile, device),
        # malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

        # Device does not exist, malformed data dict, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

        # Device does not exist, device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': 'non-existing',
              'profile_data': {'age': 30}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

    def test_profile_put_403_invalid_signature(self):
        self.create_profiles()

        # Only profile
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id), {'profile': {'profile_data': {'age': 30}}},
            [self.p1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Only device
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Both profile and device
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    def test_profile_put_403_invalid_signature_error_priorities(self):
        self.create_profiles()

        # Invalid signature (device, profile), malformed data dict,
        # device already set
        # (with one signature)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # (with two signatures, only wrong profile)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)
        # (only wrong device)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.p3_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)
        # (both device and profile wrong)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.p3_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid signature (device, profile), device already set
        # (with one signature)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # (with two signatures, only wrong profile)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)
        # (only wrong device)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p1_sk, self.p3_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)
        # (both device and profile wrong)
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p2_sk, self.p3_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    def test_profile_put_400_malformed_data(self):
        self.create_profiles()

        # One signature
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Two signatures
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_profile_put_400_malformed_data_error_priorities(self):
        self.create_profiles()

        # Device already set
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_profile_put_403_device_already_set(self):
        self.create_profiles()

        data, status_code = self.sput('/profiles/{}'.format(
            self.p1.profile_id),
            {'profile':
             {'device_id': self.d2.device_id,
              'profile_data': {'age': 30}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_device_already_set_dict)

    # No error priority tests since the device being already set is the last
    # possible error

    def test_root_get_no_auth(self):
        ## Empty array

        # Public access
        data, status_code = self.get('/profiles')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        # Private access
        data, status_code = self.get('/profiles?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        ## With profiles
        self.create_profiles()

        # Public access
        data, status_code = self.get('/profiles')
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_public, data['profiles'])
        self.assertIn(self.p2_dict_public, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        # Private access
        data, status_code = self.get('/profiles?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_get_no_auth_by_id(self):
        ## Emtpy array

        # Public access
        data, status_code = self.get('/profiles?ids[]={}'.format(
            'non-existing'))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        # Private access
        data, status_code = self.get(
            '/profiles?ids[]={}&access=private'.format(
                self.p1_dict_public['id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        ## With profiles
        self.create_profiles()

        # Public access
        data, status_code = self.get('/profiles?ids[]={}'.format(
            self.p1_dict_public['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p1_dict_public]})

        # Public access, two profiles
        data, status_code = self.get('/profiles?ids[]={}&ids[]={}'.format(
            self.p1_dict_public['id'], self.p2_dict_public['id']))
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_public, data['profiles'])
        self.assertIn(self.p2_dict_public, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        # Private access
        data, status_code = self.get(
            '/profiles?ids[]={}&access=private'.format(
                self.p1_dict_public['id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_get_with_auth(self):
        #### Empty array

        # Public access
        data, status_code = self.get('/profiles', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        # Private access
        data, status_code = self.get('/profiles?access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        #### With profiles
        self.create_profiles()

        ### Public access
        data, status_code = self.get('/profiles', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_public, data['profiles'])
        self.assertIn(self.p2_dict_public, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        ### Private access

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles?access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p1_dict_private]})

        # As collaborator
        data, status_code = self.get('/profiles?access=private', self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p1_dict_private]})

        # As owner without device
        data, status_code = self.get('/profiles?access=private', self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p2_dict_private]})

    def test_root_get_with_auth_by_id(self):
        #### Empty array

        # Public access
        data, status_code = self.get('/profiles?ids[]={}'.format(
            'non-existing'), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        # Private access
        data, status_code = self.get(
            '/profiles?ids[]={}&access=private'.format('non-existing'),
            self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': []})

        #### With profiles
        self.create_profiles()
        p3_vk = self.p3_sk.verifying_key
        Profile.create(p3_vk.to_pem(), self.exp_gp, {'occupation': 'none'},
                       self.d1)
        p3_dict_public = {'id': sha256hex(p3_vk.to_pem()),
                          'vk_pem': p3_vk.to_pem()}
        p3_dict_private = p3_dict_public.copy()
        p3_dict_private.update({'exp_id': self.exp_gp.exp_id,
                                'device_id': self.d1.device_id,
                                'profile_data': {'occupation': 'none'},
                                'n_results': 0})
        p4_vk = self.p4_sk.verifying_key
        Profile.create(p4_vk.to_pem(), self.exp_nd,
                       {'occupation': 'say what?'})
        p4_dict_public = {'id': sha256hex(p4_vk.to_pem()),
                          'vk_pem': p4_vk.to_pem()}
        p4_dict_private = p4_dict_public.copy()
        p4_dict_private.update({'exp_id': self.exp_nd.exp_id,
                                'profile_data': {'occupation': 'say what?'},
                                'device_id': None,
                                'n_results': 0})

        ### Public access, one profile
        data, status_code = self.get('/profiles?ids[]={}'.format(
            self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p1_dict_public]})

        ### Public access, two profiles
        data, status_code = self.get('/profiles?ids[]={}&ids[]={}'.format(
            self.p1_dict_public['id'], p3_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_public, data['profiles'])
        self.assertIn(p3_dict_public, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        ### Private access

        ## GET with auth with private access to accessible profiles (owner,
        ## collab)

        # As owner, one profile
        data, status_code = self.get(
            '/profiles?ids[]={}&access=private'.format(
                self.p1_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profiles': [self.p1_dict_private]})

        # As owner, two profiles
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p1_dict_public['id'], p4_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_private, data['profiles'])
        self.assertIn(p4_dict_private, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        # As collaborator, two profiles
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p1_dict_public['id'], p4_dict_public['id']), self.bill)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p1_dict_private, data['profiles'])
        self.assertIn(p4_dict_private, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        # As owner without device, two profiles
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p2_dict_public['id'], p3_dict_public['id']),
            self.sophia)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['profiles'])
        self.assertIn(self.p2_dict_private, data['profiles'])
        self.assertIn(p3_dict_private, data['profiles'])
        self.assertEqual(len(data['profiles']), 2)

        ## GET on non-accessible profiles

        # From jane
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p2_dict_public['id'], p4_dict_public['id']),
            self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # From bill
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p1_dict_public['id'], p3_dict_public['id']),
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # From sophia
        data, status_code = self.get(
            '/profiles?ids[]={}&ids[]={}&access=private'.format(
                self.p1_dict_public['id'], p4_dict_public['id']),
            self.sophia)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_root_post_data_successful(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'vk_pem': self.p2_vk.to_pem(),
                                         'exp_id': self.exp_gp.exp_id,
                                         'profile_data':
                                         {'occupation': 'social worker'}}},
                                       self.p2_sk, self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_root_post_data_ignore_additional_data(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'id': 'blabedibla',
                                         'vk_pem': self.p2_vk.to_pem(),
                                         'exp_id': self.exp_gp.exp_id,
                                         'profile_data':
                                         {'occupation': 'social worker'},
                                         'more-ignored': 'stuff'},
                                        'and still': 'more'},
                                       self.p2_sk, self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_root_post_data_complete_missing_fields(self):
        # With no `data` field, which is completed with an empty dict
        # (Authentication is ignored)
        p3_vk = self.p3_sk.verifying_key
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': p3_vk.to_pem(),
              'exp_id': self.exp_gp.exp_id}},
            self.p3_sk, self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data,
                         {'profile':
                          {'id': sha256hex(p3_vk.to_pem()),
                           'vk_pem': p3_vk.to_pem(),
                           'exp_id': self.exp_gp.exp_id,
                           'device_id': None,
                           'profile_data': {},
                           'n_results': 0}})

    def test_root_post_device_and_data_successful(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'vk_pem': self.p1_vk.to_pem(),
                                         'device_id': self.d1.device_id,
                                         'exp_id': self.exp_nd.exp_id,
                                         'profile_data':
                                         {'occupation': 'student'}}},
                                       [self.p1_sk, self.d1_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p1_dict_private})

    def test_root_post_device_and_data_successful_reversed_signatures(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'vk_pem': self.p1_vk.to_pem(),
                                         'device_id': self.d1.device_id,
                                         'exp_id': self.exp_nd.exp_id,
                                         'profile_data':
                                         {'occupation': 'student'}}},
                                       [self.d1_sk, self.p1_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p1_dict_private})

    def test_root_post_device_and_data_ignore_additional_data(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'id': 'blabedibla',
                                         'vk_pem': self.p1_vk.to_pem(),
                                         'device_id': self.d1.device_id,
                                         'exp_id': self.exp_nd.exp_id,
                                         'profile_data':
                                         {'occupation': 'student'},
                                         'more-ignored': 'stuff'},
                                        'and still': 'more'},
                                       [self.p1_sk, self.d1_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # With an ignored device_id because of a single signature
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'id': 'blabedibla',
                                         'vk_pem': self.p2_vk.to_pem(),
                                         'device_id': self.d2.device_id,
                                         'exp_id': self.exp_gp.exp_id,
                                         'profile_data':
                                         {'occupation': 'social worker'},
                                         'more-ignored': 'stuff'},
                                        'and still': 'more'},
                                       self.p2_sk, self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    def test_root_post_device_and_data_ignore_additional_data_revsigs(self):
        # (Authentication is ignored)
        data, status_code = self.spost('/profiles',
                                       {'profile':
                                        {'id': 'blabedibla',
                                         'vk_pem': self.p1_vk.to_pem(),
                                         'device_id': self.d1.device_id,
                                         'exp_id': self.exp_nd.exp_id,
                                         'profile_data':
                                         {'occupation': 'student'},
                                         'more-ignored': 'stuff'},
                                        'and still': 'more'},
                                       [self.d1_sk, self.p1_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'profile': self.p1_dict_private})

    def test_root_post_complete_missing_fields(self):
        # With no `data` field, which is completed with an empty dict
        # (Authentication is ignored)
        p3_vk = self.p3_sk.verifying_key
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': p3_vk.to_pem(),
              'device_id': self.d1.device_id,
              'exp_id': self.exp_gp.exp_id}},
            [self.p3_sk, self.d1_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data,
                         {'profile':
                          {'id': sha256hex(p3_vk.to_pem()),
                           'vk_pem': p3_vk.to_pem(),
                           'device_id': self.d1.device_id,
                           'exp_id': self.exp_gp.exp_id,
                           'profile_data': {},
                           'n_results': 0}})

    def test_root_post_complete_missing_fields_reversed_signatures(self):
        # With no `data` field, which is completed with an empty dict
        # (Authentication is ignored)
        p3_vk = self.p3_sk.verifying_key
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': p3_vk.to_pem(),
              'device_id': self.d1.device_id,
              'exp_id': self.exp_gp.exp_id}},
            [self.d1_sk, self.p3_sk], self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data,
                         {'profile':
                          {'id': sha256hex(p3_vk.to_pem()),
                           'vk_pem': p3_vk.to_pem(),
                           'device_id': self.d1.device_id,
                           'exp_id': self.exp_gp.exp_id,
                           'profile_data': {},
                           'n_results': 0}})

    def test_root_post_400_malformed_json_presig(self):
        data, status_code = self.post('/profiles',
                                      '{"malformed JSON": "bla"',
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priorities test for malformed JSON since it excludes anything
    # else

    def test_root_post_400_malformed_signature(self):
        # (no `payload`)
        data, status_code = self.post('/profiles',
                                      {'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`payload` is not a base64url string)
        data, status_code = self.post('/profiles',
                                      {'payload': {},
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'abcde',  # Incorrect padding
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signatures`)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signatures` is not a list)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures': 30})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures': {}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures': 'bli'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `protected` in a signature)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`protected is not a base64url string)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': {},
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 30,
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'abcde',
                                         'signature': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signature` in a signature)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signature` is not base64url a string)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': {}},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 30},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/profiles',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'abcde'},
                                        {'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priorities test for malformed JSON since it excludes anything
    # else

    def test_root_post_400_missing_signature(self):
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_root_post_400_missing_signature_error_priorities(self):
        self.create_profiles()

        # (Too many signatures make no sense with missing signature),
        # (malformed JSON postsig with missing signature amounts to malformed
        # JSON presig), missing field (key), device does not exist,
        # (invalid signature makes no sense with missing signature),
        # malformed data, experiment not found, (key already registered
        # makes no sense with missing key)
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (Too many signatures make no sense with missing signature),
        # (malformed JSON postsig with missing signature amounts to malformed
        # JSON presig), missing field (exp), device does not exist, (invalid
        # signature makes no sense with missing signature), (experiment not
        # found makes no sense with missing exp_id), malformed data dict,
        # key already registered.
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Missing device_id only makes sense with two or more signatures

        # Device does not exist, (invalid signature makes no sense with missing
        # signature), malformed data dict, experiment not found, key already
        # registered.
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (invalid signature makes no sense with missing signature),
        # malformed data dict, experiment not found, key already registered.
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (invalid signature makes no sense with missing signature),
        # experiment not found, key already registered.
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Key already registered
        data, status_code = self.post(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_root_post_400_too_many_signatures(self):
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    def test_root_post_400_too_many_signatures_error_priorities(self):
        self.create_profiles()

        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # Malformed JSON postsig
        #data, status_code = self.spost(
            #'/profiles', '{"malformed JSON": "bla"',
            #[self.p1_sk, self.d1_sk, self.d2_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Missing field (key), device does not exist, invalid signature
        # (profile, device), malformed data dict, experiment not found,
        # (key already registered makes no sense with missing key).
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Missing field (exp), device does not exist, invalid signature
        # (profile, device), (experiment not found makes no sense with
        # missing exp_id), malformed data dict, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Missing field (device), invalid signature, malformed data dict,
        # experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Device does not exist, invalid signature (profile, device),
        # malformed data dict, experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Invalid signature, malformed data dict, experiment not found,
        # key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Malformed data dict, experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    # FIXME: can't do this test yet since python-jws checks for JSON
    # conformity before signing.

    #def test_root_post_400_malformed_json_postsig(self):
        ## With one signature
        #data, status_code = self.spost(
            #'/profiles', '{"malformed JSON": "bla"',
            #self.p1_sk, dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

        ## With two signatures
        #data, status_code = self.spost(
            #'/profiles', '{"malformed JSON": "bla"',
            #[self.p1_sk, self.d1_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    def test_root_post_400_missing_field(self):
        # No 'profile' root
        data, status_code = self.spost(
            '/profiles',
            {'no-profile': {}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # (two signatures)
        # Missing key
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing experiment
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing device
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_root_post_400_missing_field_error_priorities(self):
        self.create_profiles()

        # Missing field (key), device does not exist, invalid signature
        # (profile, device), malformed data dict, experiment not found,
        # (key already registered makes no sense with missing key).
        # (two signatures, otherwise 'device does not exist' makes no sense)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (exp), device does not exist, invalid signature
        # (profile, device), (experiment not found makes no sense with
        # missing exp_id), malformed data dict, key already registered.
        # (two signatures, otherwise 'device does not exist' makes no sense)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (device), (device does not exist makes no sense here),
        # invalid signature, malformed data dict, experiment not found,
        # key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (key), invalid signature (profile, device),
        # malformed data dict, experiment not found, (key already registered
        # makes no sense with missing key).
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            self.p3_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (exp), invalid signature (profile, device),
        # (experiment not found makes no sense with missing exp),
        # malformed data dict, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # The 'missing device' here is the same as previously as we had already
        # removed the 'device does not exist'.

        # Malformed data dict, experiment not found, missing field (key).
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Experiment not found, missing field (key).
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Malformed data dict, key already registered, missing field (exp).
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Key already registered, missing field (exp).
        # (one signature)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)
        # (two signatures)
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (device), malformed data dict, experiment not found,
        # key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (device), experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing field (device), key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_root_post_400_device_does_not_exist(self):
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': 'non-existing-device',
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

    def test_root_post_400_device_does_not_exist_error_priorities(self):
        self.create_profiles()

        # Invalid signature, malformed data dict, experiment not found,
        # key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

        # Malformed data dict, experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

        # Experiment not found, key already registered.
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': 'non-existing-device',
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': 'non-existing-device',
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_device_does_not_exist_dict)

    def test_root_post_403_invalid_signature(self):
        ## One signature

        # Invalid profile signature
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        ## Two signatures

        # Invalid profile signature
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid device signature
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Both signatures invalid
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    def test_root_post_403_invalid_signature_error_priorities(self):
        self.create_profiles()

        ## One signature

        # Invalid profile signature, malformed data dict, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': 'non-dict'}},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid profile signature, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': {'occupation': 'student'}}},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid profile signature, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        ## Two signatures

        # Invalid profile signature, malformed data dict, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid profile signature, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid profile signature, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d1_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid device signature, malformed data dict, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid device signature, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Invalid device signature, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Both signatures invalid, malformed data dict, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existin-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Both signatures invalid, experiment not found,
        # key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existin-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # Both signatures invalid, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    def test_root_post_400_malformed_data(self):
        ## One signature
        # String
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Number
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': 123}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # List
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': [1, 2, 3]}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        ## Two signatures
        # String
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Number
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': 123}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # List
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': [1, 2, 3]}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_root_post_400_malformed_data_error_priorities(self):
        self.create_profiles()

        ## One signature, string only
        # Experiment not found, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-exp',
              'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': 'non-dict'}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        ## Two signatures, string only
        # Experiment not found, key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-exp',
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': 'non-dict'}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    def test_root_post_400_experiment_not_found(self):
        # One signature
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_experiment_does_not_exist_dict)

        # Two signatures
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_experiment_does_not_exist_dict)

    def test_root_post_400_experiment_not_found_error_priorities(self):
        self.create_profiles()

        ## One signature

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_experiment_does_not_exist_dict)

        ## Two signatures

        # Key already registered
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': 'non-existing-exp',
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_experiment_does_not_exist_dict)

    def test_root_post_409_key_already_registered(self):
        self.create_profiles()

        # One signature
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'profile_data': {'occupation': 'student'}}},
            self.p1_sk)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

        # Two signatures
        data, status_code = self.spost(
            '/profiles',
            {'profile':
             {'vk_pem': self.p1_vk.to_pem(),
              'exp_id': self.exp_nd.exp_id,
              'device_id': self.d1.device_id,
              'profile_data': {'occupation': 'student'}}},
            [self.p1_sk, self.d1_sk])
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

    # No error priority tests since the key already being registered is the
    # last possible error
