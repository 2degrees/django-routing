from nose.tools import eq_

from django_routing.routes import BaseRoute
from django_routing.routes import DuplicatedRouteError
from django_routing.routes import get_route_by_name
from django_routing.routes import NonExistingRouteError

from tests.assertions import assert_equivalent
from tests.assertions import assert_non_equivalent
from tests.assertions import assert_raises_substring
from tests.fixtures import FAKE_ROUTE_NAME
from tests.fixtures import FAKE_SUB_ROUTES
from tests.fixtures import FAKE_VIEW


def test_repr():
    route = BaseRoute(None, None, FAKE_SUB_ROUTES)
    expected_sub_routes_repr = '_RouteCollection({!r})'.format(
        list(FAKE_SUB_ROUTES),
        )
    eq_(expected_sub_routes_repr, repr(route.sub_routes))


def test_iterator():
    route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
    sub_routes = tuple(route.sub_routes)

    eq_(FAKE_SUB_ROUTES, sub_routes)


def test_length():
    route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
    eq_(len(FAKE_SUB_ROUTES), len(route.sub_routes))


class TestEquality(object):

    def test_sub_routes_with_same_attributes(self):
        route_1 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        route_2 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)

        assert_equivalent(route_1.sub_routes, route_2.sub_routes)

    def test_sub_routes_with_different_attributes(self):
        sub_route_1 = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME)
        route_1 = BaseRoute(None, None, [sub_route_1])

        sub_route_2 = BaseRoute(FAKE_VIEW, None)
        route_2 = BaseRoute(None, None, [sub_route_2])

        assert_non_equivalent(route_1.sub_routes, route_2.sub_routes)

    def test_non_sub_route_collection(self):
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, FAKE_SUB_ROUTES)
        assert_non_equivalent(route.sub_routes, None)


class TestRetrieval(object):

    def test_existing_direct_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(FAKE_VIEW, sub_route_name)
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        retrieved_route = get_route_by_name(route, sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_indirect_sub_route(self):
        sub_route_name = 'sub_route_1'
        sub_route = BaseRoute(FAKE_VIEW, sub_route_name)
        route = BaseRoute(
            FAKE_VIEW,
            FAKE_ROUTE_NAME,
            [BaseRoute(None, None, [sub_route])],
            )

        retrieved_route = get_route_by_name(route, sub_route_name)
        eq_(sub_route, retrieved_route)

    def test_existing_own_route(self):
        route_name = 'route_1'
        route = BaseRoute(FAKE_VIEW, route_name)

        retrieved_route = get_route_by_name(route, route_name)
        eq_(route, retrieved_route)

    def test_non_existing_sub_route(self):
        sub_route = BaseRoute(FAKE_VIEW, 'sub_route_1')
        route = BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, [sub_route])

        non_existing_route_name = 'non_existing'
        with assert_raises_substring(
            NonExistingRouteError,
            non_existing_route_name,
            ):
            get_route_by_name(route, non_existing_route_name)


class TestRouteInitializationValidation(object):

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
        sub_route_1 = BaseRoute(FAKE_VIEW, duplicated_route_name)
        sub_route_2 = BaseRoute(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, (sub_route_1, sub_route_2))

    def test_equivalent_sibling_sub_routes_without_names(self):
        sub_route_1 = BaseRoute(FAKE_VIEW, None)
        sub_route_2 = BaseRoute(FAKE_VIEW, None)
        with assert_raises_substring(DuplicatedRouteError, repr(sub_route_1)):
            BaseRoute(FAKE_VIEW, FAKE_ROUTE_NAME, (sub_route_1, sub_route_2))

    def test_sub_route_duplicating_direct_ancestor_name(self):
        duplicated_route_name = 'route_name'
        sub_route = BaseRoute(FAKE_VIEW, duplicated_route_name)
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            BaseRoute(FAKE_VIEW, duplicated_route_name, [sub_route])

    def test_sub_route_duplicating_indirect_ancestor_name(self):
        duplicated_route_name = 'route_name'
        intermediate_sub_route = BaseRoute(
            None,
            None,
            [BaseRoute(FAKE_VIEW, duplicated_route_name)],
            )
        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                duplicated_route_name,
                [intermediate_sub_route],
                )

    def test_sub_route_duplicating_cousin_name(self):
        duplicated_route_name = 'duplicated_route_name'

        leaf_sub_route_1 = BaseRoute(FAKE_VIEW, duplicated_route_name)
        intermediate_sub_route_1 = BaseRoute(object(), None, [leaf_sub_route_1])

        leaf_sub_route_2 = BaseRoute(None, duplicated_route_name)
        intermediate_sub_route_2 = BaseRoute(object(), None, [leaf_sub_route_2])

        with assert_raises_substring(
            DuplicatedRouteError,
            duplicated_route_name,
            ):
            BaseRoute(
                FAKE_VIEW,
                FAKE_ROUTE_NAME,
                (intermediate_sub_route_1, intermediate_sub_route_2),
                )
