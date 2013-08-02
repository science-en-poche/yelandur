# -*- coding: utf-8 -*-

from unittest import skip

from .models import Device
from .helpers import APITestCase


# TODO: add CORS test


class ExpsTestCase(APITestCase):

    maxDiff = None

    def setUp(self):
        super(ExpsTestCase, self).setUp()

        # A test device to work with
        self.d1 = Device.create('public key of d1')
        self.d2 = Device.create('public key of d2')

    @skip('not implementation yet')
    def test_root_get(self):
        # Successful GET
        # Empty GET
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_successful(self):
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_successful_ignore_additional_data(self):
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_malformed(self):
        # Bad JSON
        # Good JSON but no root 'device' object
        # Good JSON but no 'vk_pem'
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_already_registered(self):
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_device_get(self):
        # Successful GET
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_device_get_not_found(self):
        # 404
        # Ignore authentication
        pass
