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
from django_routing.routes import NonExistingRouteError

from tests.assertions import assert_raises_substring


class TestBaseRoute(object):

    def test_repr(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, _FAKE_SUB_ROUTES)
        expected_repr = 'BaseRoute({!r}, {!r}, {!r})'.format(
            _FAKE_VIEW,
            _FAKE_ROUTE_NAME,
            _FAKE_SUB_ROUTES,
            )
        eq_(expected_repr, repr(route))

    def test_iterator(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, _FAKE_SUB_ROUTES)
        sub_routes = tuple(route)

        eq_(_FAKE_SUB_ROUTES, sub_routes)

    def test_name_getter(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME)
        eq_(_FAKE_ROUTE_NAME, route.get_name())

    def test_get_view(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME)
        eq_(_FAKE_VIEW, route.get_view())


class TestRouteRetrieval(object):

    def test_existing_direct_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(_FAKE_VIEW, sub_route_name)
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, [sub_route])

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_indirect_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(_FAKE_VIEW, sub_route_name)
        route = BaseRoute(
            _FAKE_VIEW,
            _FAKE_ROUTE_NAME,
            [BaseRoute(None, None, [sub_route])],
            )

        retrieved_route = route.get_route_by_name(sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_own_route(self):
        route_name = 'route_1'
        route = BaseRoute(_FAKE_VIEW, route_name)

        retrieved_route = route.get_route_by_name(route_name)
        eq_(route, retrieved_route)

    def test_non_existing_sub_route(self):
        sub_route = BaseRoute(_FAKE_VIEW, 'sub_route_1')
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, [sub_route])

        non_existing_route_name = 'non_existing'
        with assert_raises_substring(
            NonExistingRouteError,
            non_existing_route_name,
            ):
            route.get_route_by_name(non_existing_route_name)


class TestInitializationValidation(object):

    def test_unique_route_names(self):
        BaseRoute(
            _FAKE_VIEW,
            _FAKE_ROUTE_NAME,
            (
                BaseRoute(_FAKE_VIEW, 'sub_route_1'),
                BaseRoute(_FAKE_VIEW, 'sub_route_2'),
                ),
            )

    def test_sibling_sub_routes_with_duplicated_names(self):
        duplicated_route_name = 'sub_route_1'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                _FAKE_VIEW,
                _FAKE_ROUTE_NAME,
                (
                    BaseRoute(_FAKE_VIEW, duplicated_route_name),
                    BaseRoute(_FAKE_VIEW, duplicated_route_name),
                    ),
                )

    def test_sub_route_duplicating_direct_ancestor_name(self):
        duplicated_route_name = 'route_name'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                _FAKE_VIEW,
                duplicated_route_name,
                [BaseRoute(_FAKE_VIEW, duplicated_route_name)],
                )

    def test_sub_route_duplicating_indirect_ancestor_name(self):
        duplicated_route_name = 'route_name'
        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                _FAKE_VIEW,
                duplicated_route_name,
                [
                    BaseRoute(
                        None,
                        None,
                        [BaseRoute(_FAKE_VIEW, duplicated_route_name)],
                        ),
                    ],
                )

    def test_sub_route_duplicating_cousin_name(self):
        duplicated_route_name = 'sub_route_1'
        duplicated_sub_route = BaseRoute(_FAKE_VIEW, duplicated_route_name)

        conflicting_sub_route_1 = BaseRoute(None, None, [duplicated_sub_route])
        conflicting_sub_route_2 = BaseRoute(None, None, [duplicated_sub_route])

        with assert_raises_substring(
            DuplicatedRouteNameError,
            duplicated_route_name,
            ):
            BaseRoute(
                _FAKE_VIEW,
                _FAKE_ROUTE_NAME,
                (conflicting_sub_route_1, conflicting_sub_route_2),
                )


class TestSpecialization(object):

    def test_reference(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, _FAKE_SUB_ROUTES)
        specialized_route = route.create_specialization()
        assert_not_equal(route, specialized_route)

    def test_no_change(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, _FAKE_SUB_ROUTES)
        specialized_route = route.create_specialization()

        eq_(_FAKE_ROUTE_NAME, specialized_route.get_name())
        eq_(_FAKE_VIEW, specialized_route.get_view())
        eq_(_FAKE_SUB_ROUTES, tuple(specialized_route))

    def test_additional_sub_routes(self):
        route = BaseRoute(_FAKE_VIEW, _FAKE_ROUTE_NAME, _FAKE_SUB_ROUTES)
        additional_route = BaseRoute(_FAKE_VIEW, 'new_name')
        specialized_route = route.create_specialization(
            additional_sub_routes=additional_route,
            )

        specialized_route_sub_routes = _FAKE_SUB_ROUTES + (additional_route,)

        eq_(specialized_route_sub_routes, tuple(specialized_route))

    def test_additional_sub_route_with_duplicated_name(self):
        assert 0

    def test_specializing_sub_routes(self):
        original_sub_route = BaseRoute(None, None)
        original_route = BaseRoute(
            _FAKE_VIEW,
            _FAKE_ROUTE_NAME,
            [original_sub_route],
            )
        specialized_sub_route = original_sub_route.create_specialization()
        specialized_route = original_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route],
            )

        eq_((specialized_sub_route,), tuple(specialized_route))

    def test_specializing_sub_route_with_non_specialized_route(self):
        original_sub_route = BaseRoute(None, None)
        original_route = BaseRoute(
            _FAKE_VIEW,
            _FAKE_ROUTE_NAME,
            [original_sub_route],
            )
        unspecialized_route_name = 'unspecialized_route_name'
        unspecialized_route = BaseRoute(None, unspecialized_route_name)

        with assert_raises_substring(
            InvalidSpecializationError,
            unspecialized_route_name,
            ):
            original_route.create_specialization(
                specialized_sub_routes=[unspecialized_route],
                )

    def test_overriding_views(self):
        assert 0

    def test_overriding_non_existing_views(self):
        assert 0

    def test_getting_name_of_specialization(self):
        assert 0

    def test_getting_route_by_name(self):
        assert 0

    def test_specializing_specializations(self):
        assert 0


_FAKE_VIEW = object()


_FAKE_ROUTE_NAME = 'name'


_FAKE_SUB_ROUTES = (
    BaseRoute(None, None),
    BaseRoute(None, None),
    )
