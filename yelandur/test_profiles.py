# -*- coding: utf-8 -*-

from .models import User, Exp, Device, Profile
from .helpers import APITestCase


class ProfilesTestCase(APITestCase):

    def setUp(self):
        super(ProfilesTestCase, self).setUp()

