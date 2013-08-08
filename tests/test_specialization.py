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

from nose.tools import assert_not_equal
from nose.tools import eq_

from django_routing.routes import BaseRoute
from django_routing.routes import DuplicatedRouteNameError
from django_routing.routes import InvalidSpecializationError

from tests.assertions import assert_raises_substring
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


class TestSpecialization(object):

    def test_repr(self):
        generalized_route = \
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        specialized_route = generalized_route.create_specialization()
        expected_repr = 'BaseRoute({!r}, {!r}, {!r})'.format(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        eq_(expected_repr, repr(specialized_route))

    def test_reference(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route = generalized_route.create_specialization()
        assert_not_equal(generalized_route, specialized_route)

    def test_no_change(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route = generalized_route.create_specialization()

        eq_(FAKE_ROUTE_NAME, specialized_route.get_name())
        eq_(FAKE_VIEW, specialized_route.get_view())
        eq_(FAKE_SUB_ROUTES, tuple(specialized_route))

    def test_getting_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()
        eq_(FAKE_ROUTE_NAME, specialized_route.get_name())

    #{ Getting routes by name

    def test_getting_current_route_by_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()

        retrieved_route = specialized_route.get_route_by_name(FAKE_ROUTE_NAME)
        eq_(specialized_route, retrieved_route)

    def test_getting_specialized_sub_route_by_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization(
            specialized_sub_routes=[]
            )

        retrieved_route = specialized_route.get_route_by_name(FAKE_ROUTE_NAME)
        eq_(specialized_route, retrieved_route)

    def test_getting_additional_sub_route_by_name(self):
        sub_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(None, None, [sub_route])
        specialized_route = generalized_route.create_specialization()

        retrieved_route = specialized_route.get_route_by_name(FAKE_ROUTE_NAME)
        eq_(sub_route, retrieved_route)

    #}

    def test_sub_routes_order(self):
        generalized_sub_route1 = BaseRoute(None, 'sub_route_1')
        generalized_sub_route2 = BaseRoute(None, 'sub_route_2')
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            (generalized_sub_route1, generalized_sub_route2),
            )

        additional_sub_route = BaseRoute(None, 'additional_sub_route')
        specialized_sub_route = generalized_sub_route1.create_specialization()

        specialized_route = generalized_route.create_specialization(
            additional_sub_routes=[additional_sub_route],
            specialized_sub_routes=[specialized_sub_route],
            )

        expected_sub_routes = (
            specialized_sub_route,
            generalized_sub_route2,
            additional_sub_route,
            )
        eq_(expected_sub_routes, tuple(specialized_route))


class TestSpecializedSubRoutes(object):

    def test_direct_named_sub_routes(self):
        generalized_sub_route_name = 'sub_route_name'
        generalized_sub_route = BaseRoute(None, generalized_sub_route_name)
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [generalized_sub_route],
            )

        specialized_sub_route = generalized_sub_route.create_specialization(
            view=FAKE_VIEW,
            )
        specialized_route = generalized_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route],
            )

        eq_((specialized_sub_route,), tuple(specialized_route))

    def test_direct_unnamed_sub_routes(self):
        generalized_sub_route = BaseRoute(FAKE_VIEW, None)
        sub_route = BaseRoute(None, None)
        generalized_route = BaseRoute(
            None,
            FAKE_ROUTE_NAME,
            [generalized_sub_route, sub_route],
            )

        specialized_sub_route = generalized_sub_route.create_specialization()
        specialized_route = generalized_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route],
            )

        # A second sub-route without name shouldn't override the first sub-route
        eq_((specialized_sub_route, sub_route), tuple(specialized_route))

    def test_non_existing_sub_route(self):
        generalized_route = BaseRoute(None, None)

        non_existing_sub_route_name = 'non_existing_route'
        sub_route = BaseRoute(None, non_existing_sub_route_name)

        with assert_raises_substring(
            InvalidSpecializationError,
            non_existing_sub_route_name,
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[sub_route],
                )

    def test_sub_route_with_non_specialized_route(self):
        sub_route_name = 'sub_route_name'
        generalized_sub_route = BaseRoute(None, sub_route_name)
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [generalized_sub_route],
            )
        unspecialized_route = BaseRoute(None, sub_route_name)

        with assert_raises_substring(
            InvalidSpecializationError,
            sub_route_name,
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[unspecialized_route],
                )

    def test_sub_route_specializing_current_route(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)

        sub_route = generalized_route.create_specialization()

        with assert_raises_substring(
            InvalidSpecializationError,
            FAKE_ROUTE_NAME,
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[sub_route],
                )

    def test_specializations(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        intermediate_route = generalized_route.create_specialization()
        specialized_route = intermediate_route.create_specialization()

        eq_(FAKE_ROUTE_NAME, specialized_route.get_name())


class TestAdditionalSubRoutes(object):

    def test_uniquely_named_sub_routes(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        additional_route = BaseRoute(FAKE_VIEW, 'new_name')
        specialized_route = generalized_route.create_specialization(
            additional_sub_routes=[additional_route],
            )

        specialized_route_sub_routes = FAKE_SUB_ROUTES + (additional_route,)

        eq_(specialized_route_sub_routes, tuple(specialized_route))

    def test_sub_routes_with_duplicated_name(self):
        duplicated_route_name = 'route_name'
        generalized_route = BaseRoute(FAKE_VIEW, duplicated_route_name)
        sub_route = BaseRoute(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            generalized_route.create_specialization(
                additional_sub_routes=[sub_route],
                )


class TestSettingViews(object):

    def test_previously_unset(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)

        view = object()
        specialized_route = generalized_route.create_specialization(view=view)

        eq_(view, specialized_route.get_view())

    def test_previously_set(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)

        overridden_view = object()
        specialized_route = \
            generalized_route.create_specialization(view=overridden_view)

        eq_(overridden_view, specialized_route.get_view())
