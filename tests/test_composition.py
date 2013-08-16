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

#pylint:disable=R0201

from nose.tools import eq_

from django_routing.routes import Route
from django_routing.routes import DuplicatedRouteError
from django_routing.routes import NonExistingRouteError

from tests.assertions import assert_equivalent
from tests.assertions import assert_non_equivalent
from tests.assertions import assert_raises_substring
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


def test_repr():
    route = Route(None, None, FAKE_SUB_ROUTES)
    expected_sub_routes_repr = '_RouteCollection({!r})'.format(
        list(FAKE_SUB_ROUTES),
        )
    eq_(expected_sub_routes_repr, repr(route.sub_routes))


def test_iterator():
    route = Route(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
    sub_routes = tuple(route.sub_routes)

    eq_(FAKE_SUB_ROUTES, sub_routes)


def test_length():
    route = Route(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
    eq_(len(FAKE_SUB_ROUTES), len(route.sub_routes))


class TestEquality(object):

    def test_sub_routes_with_same_attributes(self):
        route_1 = Route(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        route_2 = Route(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        assert_equivalent(route_1.sub_routes, route_2.sub_routes)

    def test_sub_routes_with_different_attributes(self):
        sub_route_1 = Route(FAKE_VIEW, FAKE_ROUTE_NAME)
        route_1 = Route(None, None, [sub_route_1])

        sub_route_2 = Route(FAKE_VIEW, None)
        route_2 = Route(None, None, [sub_route_2])

        assert_non_equivalent(route_1.sub_routes, route_2.sub_routes)

    def test_non_sub_route_collection(self):
        route = Route(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        assert_non_equivalent(route.sub_routes, None)


class TestRetrieval(object):

    def test_existing_direct_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = Route(FAKE_VIEW, sub_route_name)
        route = Route(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_indirect_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = Route(FAKE_VIEW, sub_route_name)
        route = Route(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [Route(None, None, [sub_route])],
            )

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_own_route(self):
        route_name = 'route_1'
        route = Route(FAKE_VIEW, route_name)

        retrieved_route = route.get_route_by_name(route_name)
        eq_(route, retrieved_route)

    def test_non_existing_sub_route(self):
        sub_route = Route(FAKE_VIEW, 'sub_route_1')
        route = Route(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        non_existing_route_name = 'non_existing'
        with assert_raises_substring(
            NonExistingRouteError,
            non_existing_route_name,
            ):
            route.get_route_by_name(non_existing_route_name)


class TestRouteInitializationValidation(object):

    def test_unique_route_names(self):
        Route(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            (
                Route(FAKE_VIEW, 'sub_route_1'),
                Route(FAKE_VIEW, 'sub_route_2'),
                ),
            )

    def test_sibling_sub_routes_with_duplicated_names(self):
        duplicated_route_name = 'sub_route_1'
        sub_route_1 = Route(FAKE_VIEW, duplicated_route_name)
        sub_route_2 = Route(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            Route(FAKE_VIEW, FAKE_ROUTE_NAME, (sub_route_1, sub_route_2))

    def test_equivalent_sibling_sub_routes_without_names(self):
        sub_route_1 = Route(FAKE_VIEW, None)
        sub_route_2 = Route(FAKE_VIEW, None)
        with assert_raises_substring(DuplicatedRouteError, repr(sub_route_1)):
            Route(FAKE_VIEW, FAKE_ROUTE_NAME, (sub_route_1, sub_route_2))

    def test_sub_route_duplicating_direct_ancestor_name(self):
        duplicated_route_name = 'route_name'
        sub_route = Route(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            Route(FAKE_VIEW, duplicated_route_name, [sub_route])

    def test_sub_route_duplicating_indirect_ancestor_name(self):
        duplicated_route_name = 'route_name'
        intermediate_sub_route = Route(
            None,
            None,
            [Route(FAKE_VIEW, duplicated_route_name)],
            )
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            Route(
                FAKE_VIEW,
                duplicated_route_name,
                [intermediate_sub_route],
                )

    def test_sub_route_duplicating_cousin_name(self):
        duplicated_route_name = 'duplicated_route_name'

        leaf_sub_route_1 = Route(FAKE_VIEW, duplicated_route_name)
        intermediate_sub_route_1 = Route(object(), None, [leaf_sub_route_1])

        leaf_sub_route_2 = Route(None, duplicated_route_name)
        intermediate_sub_route_2 = Route(object(), None, [leaf_sub_route_2])

        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            Route(
                FAKE_VIEW,
                FAKE_ROUTE_NAME,
                (intermediate_sub_route_1, intermediate_sub_route_2),
                )
