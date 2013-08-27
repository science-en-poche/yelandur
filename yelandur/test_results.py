# -*- coding: utf-8 -*-

from unittest import skip

import ecdsa

from .models import User, Exp, Device
from .helpers import APITestCase, sha256hex


# TODO: add CORS test


class ResultsTestCase(APITestCase):

    def setUp(self):
        super(ResultsTestCase, self).setUp()

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
        self.p1_dict_private.update({'exp_id': self.exp_nd.exp_id,
                                     'device_id': self.d1.device_id,
                                     'data': {'occupation': 'student'},
                                     'n_results': 0})

        # A second without device
        self.p2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p2_vk = self.p2_sk.verifying_key
        self.p2_dict_public = {'profile_id': sha256hex(self.p2_vk.to_pem()),
                               'vk_pem': self.p2_vk.to_pem()}
        self.p2_dict_private = self.p2_dict_public.copy()
        self.p2_dict_private.update({'exp_id': self.exp_gp.exp_id,
                                     'data': {'occupation': 'social worker'},
                                     'n_results': 0})

        # A third and fourth for bad signing
        self.p3_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p4_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)

    @skip('not implemented yet')
    def test_root_no_trailing_slash_should_redirect(self):
        pass

    @skip('not implemented yet')
    def test_root_get_no_auth(self):
        # Empty list, then
        # Without access=private
        # With access=private
        # For an empty result, or not
        pass

    @skip('not implemented yet')
    def test_root_get_with_auth(self):
        # Empty list, then, as outsider/owner/collab
        # Without access=private, as outsider/owner/collab
        # With access=private, as outsider/owner/collab
        # For an empty result, or not, as outsider/owner/collab
        pass

    @skip('not implemented yet')
    def test_result_get_no_auth(self):
        # Does not exist
        # Without access=private
        # With access=private
        # Empty result, or not
        pass

    @skip('not implemented yet')
    def test_result_get_with_auth(self):
        # Does not exist
        # Without access=private, as outsider/owner/collab
        # With access=private, as outsider/owner/collab
        # Empty result, or not, as outsider/owner/collab
        pass

    @skip('not implemented yet')
    def test_root_post_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_in_bulk(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_ignore_additional_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_ignore_in_bulk_additional_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_malformed_json_presig(self):
        pass

    # No error priority test with malformed json presig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_malformed_signature(self):
        pass

    # No error priority test with malformed signature since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_missing_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_missing_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_too_many_signatures(self):
        pass

    @skip('not implemented yet')
    def test_root_post_too_many_signatures_error_priorities(self):
        pass

    # FIXME: can't do this test yet since python-jws checks for JSON
    # conformity before signing.

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_postsig(self):
        pass

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_missing_field(self):
        pass

    @skip('not implemented yet')
    def test_root_post_missing_field_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_profile_does_not_exist(self):
        pass

    @skip('not implemented yet')
    def test_root_post_profile_does_not_exist_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_invalid_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_invalid_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_exp_does_not_exist(self):
        pass

    @skip('not implemented yet')
    def test_root_post_exp_does_not_exist_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_profile_does_not_belong_to_exp(self):
        pass

    # No error-priority test since the profile not belonging to the exp is the
    # last possible error
