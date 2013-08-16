# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013, 2degrees Limited.
# All Rights Reserved.
#
# This file is part of django-routing
# <https://github.com/2degrees/django-routing/>, which is subject to the
# provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from nose.tools import eq_

from django_routing.routes import BaseRoute

from tests.assertions import assert_equivalent
from tests.assertions import assert_non_equivalent
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


class TestBaseRoute(object):

    def test_repr(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        expected_repr = \
            '<BaseRoute view={!r} name={!r} with {} sub-routes>'.format(
                FAKE_VIEW,
                FAKE_ROUTE_NAME,
                len(FAKE_SUB_ROUTES),
                )
        eq_(expected_repr, repr(route))

    def test_getting_name(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        eq_(FAKE_ROUTE_NAME, route.name)

    def test_getting_view(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        eq_(FAKE_VIEW, route.view)


class TestEquality(object):

    def test_routes_with_same_attributes(self):
        route_1 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        route_2 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        assert_equivalent(route_1, route_2)

    def test_routes_with_different_attributes(self):
        assert_non_equivalent(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(object(), FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            )
        assert_non_equivalent(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(FAKE_VIEW, 'another_name', FAKE_SUB_ROUTES),
            )
        assert_non_equivalent(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, []),
            )

    def test_non_route(self):
        assert_non_equivalent(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            None,
            )
