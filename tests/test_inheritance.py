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
from django_routing.routes import DuplicatedRouteError
from django_routing.routes import get_route_by_name
from django_routing.routes import InvalidSpecializationError

from tests.assertions import assert_equivalent
from tests.assertions import assert_non_equivalent
from tests.assertions import assert_raises_substring
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


class TestSpecialization(object):

    def test_repr(self):
        generalized_route = \
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        view = object()
        specialized_route = generalized_route.create_specialization(view)

        expected_repr = '<Specialization of {!r} with view {!r}>'.format(
            generalized_route,
            view,
            )
        eq_(expected_repr, repr(specialized_route))

    def test_length_without_additional_sub_routes(self):
        generalized_route = \
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        specialized_route = generalized_route.create_specialization()
        eq_(len(FAKE_SUB_ROUTES), len(specialized_route.sub_routes))

    def test_length_with_additional_sub_routes(self):
        generalized_route = \
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        additional_sub_routes = [BaseRoute(None, 'additional_sub_route')]
        specialized_route = generalized_route.create_specialization(
            additional_sub_routes=additional_sub_routes,
            )

        expected_length = len(FAKE_SUB_ROUTES) + len(additional_sub_routes)
        eq_(expected_length, len(specialized_route.sub_routes))

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

        eq_(FAKE_ROUTE_NAME, specialized_route.name)
        eq_(FAKE_VIEW, specialized_route.view)
        eq_(FAKE_SUB_ROUTES, tuple(specialized_route.sub_routes))

    def test_getting_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()
        eq_(FAKE_ROUTE_NAME, specialized_route.name)

    #{ Getting routes by name

    def test_getting_current_route_by_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()

        retrieved_route = get_route_by_name(specialized_route, FAKE_ROUTE_NAME)
        eq_(specialized_route, retrieved_route)

    def test_getting_specialized_sub_route_by_name(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization(
            specialized_sub_routes=[]
            )

        retrieved_route = get_route_by_name(specialized_route, FAKE_ROUTE_NAME)
        eq_(specialized_route, retrieved_route)

    def test_getting_additional_sub_route_by_name(self):
        sub_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(None, None, [sub_route])
        specialized_route = generalized_route.create_specialization()

        retrieved_route = get_route_by_name(specialized_route, FAKE_ROUTE_NAME)
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
        eq_(expected_sub_routes, tuple(specialized_route.sub_routes))


class TestEquality(object):

    def test_sibling_specializations_with_same_attributes(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )

        specialized_route_1 = generalized_route.create_specialization()
        specialized_route_2 = generalized_route.create_specialization()

        assert_equivalent(specialized_route_1, specialized_route_2)

    def test_sibling_specializations_with_different_attributes(self):
        generalized_route = BaseRoute(
            None,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )

        specialized_route_1 = \
            generalized_route.create_specialization(FAKE_VIEW)
        specialized_route_2 = generalized_route.create_specialization()

        assert_non_equivalent(specialized_route_1, specialized_route_2)

    def test_sibling_specializations_with_same_sub_routes(self):
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

        assert_equivalent(specialized_route_1, specialized_route_2)

    def test_sibling_specializations_with_different_sub_routes(self):
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

        specialized_sub_route_2 = generalized_sub_route.create_specialization(
            view=object(),
            )
        specialized_route_2 = generalized_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route_2],
            )

        assert_non_equivalent(specialized_route_1, specialized_route_2)

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

        assert_equivalent(specialized_route_1, specialized_route_2)

    def test_specialization_vs_non_specialization(self):
        generalized_route = BaseRoute(None, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        specialized_route = generalized_route.create_specialization()

        route = BaseRoute(None, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        assert_non_equivalent(specialized_route, route)

    def test_non_route(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()

        assert_non_equivalent(None, specialized_route)

    def test_generalization_vs_specialization(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        specialized_route = generalized_route.create_specialization()

        assert_non_equivalent(generalized_route, specialized_route)

    def test_sub_route_collection_against_non_sub_route_collection(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route = generalized_route.create_specialization()

        assert_non_equivalent(specialized_route.sub_routes, None)

    def test_sub_route_collection_against_different_sub_route_collection(self):
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            FAKE_SUB_ROUTES,
            )
        specialized_route_1 = generalized_route.create_specialization()
        specialized_route_2 = generalized_route.create_specialization(
            additional_sub_routes=[BaseRoute(None, None)],
            )

        assert_non_equivalent(
            specialized_route_1.sub_routes,
            specialized_route_2.sub_routes,
            )


class TestSpecializedSubRoutes(object):

    def test_existing_named_sub_routes(self):
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

        eq_((specialized_sub_route,), tuple(specialized_route.sub_routes))

    def test_existing_unnamed_sub_routes(self):
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
        eq_((specialized_sub_route, sub_route), tuple(specialized_route.sub_routes))

    def test_non_existing_named_sub_route(self):
        generalized_route = BaseRoute(None, None)

        non_existing_sub_route_name = 'non_existing_route'
        generalized_sub_route = BaseRoute(None, non_existing_sub_route_name)
        specialized_sub_route = generalized_sub_route.create_specialization()

        with assert_raises_substring(
            InvalidSpecializationError,
            non_existing_sub_route_name,
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[specialized_sub_route],
                )

    def test_non_existing_unnamed_sub_route(self):
        unnamed_sub_route = BaseRoute(None, None)
        generalized_route = BaseRoute(None, None, [unnamed_sub_route])

        unnamed_generalized_sub_route = BaseRoute(FAKE_VIEW, None)
        unnamed_specialized_sub_route = \
            unnamed_generalized_sub_route.create_specialization()

        with assert_raises_substring(
            InvalidSpecializationError,
            repr(unnamed_generalized_sub_route),
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[unnamed_specialized_sub_route],
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

        with assert_raises_substring(DuplicatedRouteError, FAKE_ROUTE_NAME):
            generalized_route.create_specialization(
                specialized_sub_routes=[sub_route],
                )

    def test_adding_duplicate_sub_route_name(self):
        generalized_sub_route = BaseRoute(None, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(FAKE_VIEW, None, [generalized_sub_route])

        duplicated_sub_route_name = 'duplicated_sub_route_name'
        specialized_sub_route = generalized_sub_route.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_sub_route_name)],
            )

        additional_sub_route = BaseRoute(None, duplicated_sub_route_name)

        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_sub_route_name,
            ):
            generalized_route.create_specialization(
                additional_sub_routes=[additional_sub_route],
                specialized_sub_routes=[specialized_sub_route],
                )

    def test_sub_routes_with_duplicated_sub_route_names(self):
        generalized_sub_route_1 = BaseRoute(None, 'sub_route_1')
        generalized_sub_route_2 = BaseRoute(None, 'sub_route_2')
        generalized_route = BaseRoute(
            FAKE_VIEW,
            None,
            [generalized_sub_route_1, generalized_sub_route_2],
            )

        duplicated_sub_route_name = 'duplicated_sub_route_name'
        specialized_sub_route_1 = generalized_sub_route_1.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_sub_route_name)],
            )
        specialized_sub_route_2 = generalized_sub_route_2.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_sub_route_name)],
            )

        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_sub_route_name,
            ):
            generalized_route.create_specialization(
                specialized_sub_routes=[
                    specialized_sub_route_1,
                    specialized_sub_route_2,
                    ],
                )

    def test_named_sub_routes_specializing_common_generalization(self):
        generalized_sub_route = BaseRoute(None, 'sub_route')
        generalized_route = BaseRoute(None, None, [generalized_sub_route])

        specialized_sub_route_1 = \
            generalized_sub_route.create_specialization(FAKE_VIEW)
        specialized_sub_route_2 = generalized_sub_route.create_specialization()

        with assert_raises_substring(
            InvalidSpecializationError,
            'cannot be specialized twice',
            ):
            generalized_route.create_specialization(specialized_sub_routes=[
                specialized_sub_route_1,
                specialized_sub_route_2,
                ])

    def test_unnamed_sub_routes_specializing_common_generalization(self):
        generalized_sub_route = BaseRoute(None, None)
        generalized_route = BaseRoute(None, None, [generalized_sub_route])

        specialized_sub_route_1 = \
            generalized_sub_route.create_specialization(FAKE_VIEW)
        specialized_sub_route_2 = generalized_sub_route.create_specialization()

        with assert_raises_substring(
            InvalidSpecializationError,
            'cannot be specialized twice',
            ):
            generalized_route.create_specialization(specialized_sub_routes=[
                specialized_sub_route_1,
                specialized_sub_route_2,
                ])

    def test_additional_route_on_sub_route_duplicating_name(self):
        duplicated_name = 'duplicated_name'
        generalized_sub_route_1 = BaseRoute(None, duplicated_name)
        generalized_sub_route_2 = BaseRoute(None, 'sub_route')
        generalized_route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [generalized_sub_route_1, generalized_sub_route_2],
            )

        specialized_sub_route_1 = \
            generalized_sub_route_1.create_specialization()

        specialized_sub_route_2 = generalized_sub_route_2.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_name)]
            )

        with assert_raises_substring(DuplicatedRouteError, duplicated_name):
            generalized_route.create_specialization(
                specialized_sub_routes=[
                    specialized_sub_route_1,
                    specialized_sub_route_2,
                    ],
                )


class TestMultipleSpecialization(object):

    def test_no_change(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        intermediate_route = generalized_route.create_specialization()
        specialized_route = intermediate_route.create_specialization()

        eq_(FAKE_ROUTE_NAME, specialized_route.name)
        eq_(FAKE_VIEW, specialized_route.view)

    def test_additional_sub_route(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)

        intermediate_route = generalized_route.create_specialization()

        sub_route = BaseRoute(None, None)
        specialized_route = intermediate_route.create_specialization(
            additional_sub_routes=[sub_route],
            )

        eq_((sub_route,), tuple(specialized_route.sub_routes))

    def test_additional_duplicated_sub_route(self):
        sub_route_1 = BaseRoute(None, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(FAKE_VIEW, None, [sub_route_1])

        intermediate_route = generalized_route.create_specialization()

        sub_route_2 = BaseRoute(None, FAKE_ROUTE_NAME)
        with assert_raises_substring(DuplicatedRouteError, FAKE_ROUTE_NAME):
            intermediate_route.create_specialization(
                additional_sub_routes=[sub_route_2],
                )

    def test_specializing_sub_route(self):
        generalized_sub_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(None, None, [generalized_sub_route])

        intermediate_route = generalized_route.create_specialization()

        specialized_sub_route = generalized_sub_route.create_specialization()
        specialized_route = intermediate_route.create_specialization(
            specialized_sub_routes=[specialized_sub_route],
            )

        eq_((specialized_sub_route,), tuple(specialized_route.sub_routes))

    def test_specializing_with_invalid_sub_route(self):
        """
        The same validation routines as in the single inheritance case should be
        used.

        """
        sub_route_1 = BaseRoute(None, FAKE_ROUTE_NAME)
        generalized_route = BaseRoute(None, None, [sub_route_1])

        intermediate_route = generalized_route.create_specialization()

        sub_route_2 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        with assert_raises_substring(
            InvalidSpecializationError,
            FAKE_ROUTE_NAME
            ):
            intermediate_route.create_specialization(
                specialized_sub_routes=[sub_route_2.create_specialization()],
                )

    def test_sub_routes_with_duplicated_sub_route_names(self):
        generalized_sub_route_1 = BaseRoute(None, 'sub_route_1')
        generalized_sub_route_2 = BaseRoute(None, 'sub_route_2')
        generalized_route = BaseRoute(
            FAKE_VIEW,
            None,
            [generalized_sub_route_1, generalized_sub_route_2],
            )

        intermediate_route = generalized_route.create_specialization()

        duplicated_sub_route_name = 'duplicated_sub_route_name'
        specialized_sub_route_1 = generalized_sub_route_1.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_sub_route_name)],
            )
        specialized_sub_route_2 = generalized_sub_route_2.create_specialization(
            additional_sub_routes=[BaseRoute(None, duplicated_sub_route_name)],
            )

        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_sub_route_name,
            ):
            intermediate_route.create_specialization(
                specialized_sub_routes=[
                    specialized_sub_route_1,
                    specialized_sub_route_2,
                    ],
                )


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

        eq_(specialized_route_sub_routes, tuple(specialized_route.sub_routes))

    def test_sibling_sub_routes_with_duplicated_name(self):
        duplicated_route_name = 'route_name'
        generalized_route = BaseRoute(
            None,
            None,
            [BaseRoute(None, duplicated_route_name)],
            )
        sub_route = BaseRoute(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            generalized_route.create_specialization(
                additional_sub_routes=[sub_route],
                )

    def test_sub_route_duplicating_route_name(self):
        duplicated_route_name = 'route_name'
        generalized_route = BaseRoute(FAKE_VIEW, duplicated_route_name)
        sub_route = BaseRoute(None, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
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

        eq_(view, specialized_route.view)

    def test_previously_set(self):
        generalized_route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)

        overridden_view = object()
        specialized_route = \
            generalized_route.create_specialization(view=overridden_view)

        eq_(overridden_view, specialized_route.view)
