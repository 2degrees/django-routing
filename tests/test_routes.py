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

from nose.tools import assert_false
from nose.tools import assert_not_equal
from nose.tools import eq_
from nose.tools import ok_

from django_routing.routes import BaseRoute
from django_routing.routes import DuplicatedRouteNameError
from django_routing.routes import NonExistingRouteError

from tests.assertions import assert_raises_substring
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


class TestBaseRoute(object):

    def test_repr(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        expected_repr = 'BaseRoute({!r}, {!r}, {!r})'.format(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        eq_(expected_repr, repr(route))

    def test_iterator(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        sub_routes = tuple(route)

        eq_(FAKE_SUB_ROUTES, sub_routes)

    def test_len(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        eq_(len(FAKE_SUB_ROUTES), len(route))

    def test_boolean_representation(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        ok_(route)

    def test_getting_name(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        eq_(FAKE_ROUTE_NAME, route.get_name())

    def test_getting_view(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        eq_(FAKE_VIEW, route.get_view())


class TestBaseRouteEquality(object):

    def _assert_equivalent_routes(self, route_1, route_2):
        ok_(route_1 == route_2)
        assert_false(route_1 != route_2)

        ok_(route_2 == route_1)
        assert_false(route_2 != route_1)

    def _assert_non_equivalent_routes(self, route_1, route_2):
        ok_(route_1 != route_2)
        assert_false(route_1 == route_2)

        ok_(route_2 != route_1)
        assert_false(route_2 == route_1)

    def test_routes_with_same_attributes(self):
        route_1 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        route_2 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        self._assert_equivalent_routes(route_1, route_2)

    def test_routes_with_different_attributes(self):
        self._assert_non_equivalent_routes(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(object(), FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            )
        self._assert_non_equivalent_routes(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(FAKE_VIEW, 'another_name', FAKE_SUB_ROUTES),
            )
        self._assert_non_equivalent_routes(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, []),
            )

    def test_non_route(self):
        self._assert_non_equivalent_routes(
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES),
            None,
            )

    def test_sibling_specializations_with_same_attributes(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )

        specialized_route_1 = generalized_route.create_specialization()
        specialized_route_2 = generalized_route.create_specialization()

        self._assert_equivalent_routes(specialized_route_1, specialized_route_2)

    def test_sibling_specializations_with_different_attributes(self):
        generalized_route = BaseRoute(
            None,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )

        specialized_route_1 = \
            generalized_route.create_specialization(FAKE_VIEW)
        specialized_route_2 = generalized_route.create_specialization()

        self._assert_non_equivalent_routes(
            specialized_route_1,
            specialized_route_2,
            )

    def test_sibling_specializations_with_same_specialized_sub_routes(self):
        generalized_sub_route = BaseRoute(None, None, FAKE_SUB_ROUTES)
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [generalized_sub_route],
            )

        specialized_sub_route_1 = generalized_sub_route.create_specialization()
        specialized_route_1 = generalized_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route_1],
            )

        specialized_sub_route_2 = generalized_sub_route.create_specialization()
        specialized_route_2 = generalized_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route_2],
            )

        self._assert_equivalent_routes(specialized_route_1, specialized_route_2)

    def test_specializations_from_equivalent_generalizations(self):
        generalized_route_1 = BaseRoute(
            None,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route_1 = generalized_route_1.create_specialization()

        generalized_route_2 = BaseRoute(
            None,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route_2 = generalized_route_2.create_specialization()

        self._assert_equivalent_routes(
            specialized_route_1,
            specialized_route_2,
            )

    def test_specialization_vs_non_specialization(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        specialized_route = generalized_route.create_specialization()

        route = BaseRoute(None, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        self._assert_non_equivalent_routes(specialized_route, route)

    def test_generalization_vs_specialization(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)

        specialized_route = generalized_route.create_specialization()

        self._assert_non_equivalent_routes(generalized_route, specialized_route)


class TestRouteRetrieval(object):

    def test_existing_direct_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(FAKE_VIEW, sub_route_name)
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_indirect_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(FAKE_VIEW, sub_route_name)
        route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [BaseRoute(None, None, [sub_route])],
            )

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_own_route(self):
        route_name = 'route_1'
        route = BaseRoute(FAKE_VIEW, route_name)

        retrieved_route = route.get_route_by_name(route_name)
        eq_(route, retrieved_route)

    def test_non_existing_sub_route(self):
        sub_route = BaseRoute(FAKE_VIEW, 'sub_route_1')
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        non_existing_route_name = 'non_existing'
        with assert_raises_substring(
            NonExistingRouteError,
            non_existing_route_name,
            ):
            route.get_route_by_name(non_existing_route_name)


class TestInitializationValidation(object):

    def test_unique_route_names(self):
        BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            (
                BaseRoute(FAKE_VIEW, 'sub_route_1'),
                BaseRoute(FAKE_VIEW, 'sub_route_2'),
                ),
            )

    def test_sibling_sub_routes_with_duplicated_names(self):
        duplicated_route_name = 'sub_route_1'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                FAKE_ROUTE_NAME,
                (
                    BaseRoute(FAKE_VIEW, duplicated_route_name),
                    BaseRoute(FAKE_VIEW, duplicated_route_name),
                    ),
                )

    def test_sub_route_duplicating_direct_ancestor_name(self):
        duplicated_route_name = 'route_name'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                duplicated_route_name,
                [BaseRoute(FAKE_VIEW, duplicated_route_name)],
                )

    def test_sub_route_duplicating_indirect_ancestor_name(self):
        duplicated_route_name = 'route_name'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                duplicated_route_name,
                [
                    BaseRoute(
                        None,
                        None,
                        [BaseRoute(FAKE_VIEW, duplicated_route_name)],
                        ),
                    ],
                )

    def test_sub_route_duplicating_cousin_name(self):
        duplicated_route_name = 'sub_route_1'
        duplicated_sub_route = BaseRoute(FAKE_VIEW, duplicated_route_name)

        conflicting_sub_route_1 = BaseRoute(None, None, [duplicated_sub_route])
        conflicting_sub_route_2 = BaseRoute(None, None, [duplicated_sub_route])

        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                FAKE_ROUTE_NAME,
                (conflicting_sub_route_1, conflicting_sub_route_2),
                )
