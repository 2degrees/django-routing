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

from itertools import chain

from interfaces import define as interface
from interfaces import implement as implement_interface
from interfaces import require as interface_method


class RoutingException(Exception):
    pass


class DuplicatedRouteError(RoutingException):
    pass


class NonExistingRouteError(RoutingException):
    pass


class InvalidSpecializationError(RoutingException):
    pass


@interface
class _IRoute(object):
    # TODO: Find better name

    @interface_method
    def get_name(self):
        pass  # pragma: no cover

    @interface_method
    def get_view(self):
        pass  # pragma: no cover

    @interface_method
    def create_specialization(
        self,
        view=None,
        additional_sub_routes=(),
        specialized_sub_routes=(),
        ):
        pass  # pragma: no cover


@implement_interface(_IRoute)
class BaseRoute(object):

    def __init__(self, view, name, sub_routes=()):
        super(BaseRoute, self).__init__()

        self._view = view
        self._name = name

        for sub_route in sub_routes:
            self._require_sub_route_name_different_from_self(sub_route)
        self.sub_routes = _RouteCollection(sub_routes)

    def _require_sub_route_name_different_from_self(self, sub_route):
        sub_route_names = _get_route_names(sub_route)
        route_name = self.get_name()
        if route_name in sub_route_names:
            raise DuplicatedRouteError(route_name)

    def __repr__(self):
        repr_template = '<{class_name} view={view!r} name={name!r} with ' \
            '{sub_route_count} sub-routes>'
        repr_ = repr_template.format(
            class_name=self.__class__.__name__,
            name=self.get_name(),
            view=self.get_view(),
            sub_route_count=len(self.sub_routes),
            )
        return repr_

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_views_equivalent = self.get_view() == other.get_view()
            are_names_equivalent = self.get_name() == other.get_name()
            are_sub_routes_equivalent = self.sub_routes == other.sub_routes

            are_routes_equivalent = all((
                are_views_equivalent,
                are_names_equivalent,
                are_sub_routes_equivalent,
                ))
        else:
            are_routes_equivalent = NotImplemented

        return are_routes_equivalent

    def __ne__(self, other):
        are_routes_equivalent = self.__eq__(other)
        if are_routes_equivalent == NotImplemented:
            are_routes_not_equivalent = NotImplemented
        else:
            are_routes_not_equivalent = not are_routes_equivalent
        return are_routes_not_equivalent

    # _IRoute
    def get_name(self):
        return self._name

    # _IRoute
    def get_view(self):
        return self._view

    # _IRoute
    def create_specialization(
        self,
        view=None,
        additional_sub_routes=(),
        specialized_sub_routes=(),
        ):
        specialized_route = self.__class__(view, None, additional_sub_routes)

        route_specialization = _RouteSpecialization(
            specialized_route,
            self,
            specialized_sub_routes,
            )
        return route_specialization


@interface
class _IRouteCollection(object):
    # TODO: Find better name

    @interface_method
    def __len__(self):
        pass  # pragma: no cover

    @interface_method
    def __iter__(self):
        pass  # pragma: no cover


@implement_interface(_IRouteCollection)
class _RouteCollection(object):

    def __init__(self, routes):
        super(_RouteCollection, self).__init__()

        self._routes = []
        for route in routes:
            self._add_route(route)

    def _add_route(self, route):
        self._validate_new_route(route)
        self._routes.append(route)

    def _validate_new_route(self, route):
        self._require_route_names_uniqueness_in_collection(route)
        if not route.get_name():
            self._require_uniqueness_of_unnamed_route_in_collection(route)

    def _require_route_names_uniqueness_in_collection(self, route):
        current_collection_names = []
        for current_route in self:
            current_collection_names.extend(_get_route_names(current_route))

        route_names = _get_route_names(route)

        for route_name in route_names:
            if route_name in current_collection_names:
                raise DuplicatedRouteError(route_name)

    def _require_uniqueness_of_unnamed_route_in_collection(self, route):
        if route in self:
            raise DuplicatedRouteError(repr(route))

    def __repr__(self):
        repr_ = '{class_name}({routes})'.format(
            class_name=self.__class__.__name__,
            routes=self._routes,
            )
        return repr_

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_routes_equivalent = tuple(self) == tuple(other)
        else:
            are_routes_equivalent = NotImplemented
        return are_routes_equivalent

    def __ne__(self, other):
        are_routes_equivalent = self.__eq__(other)
        if are_routes_equivalent == NotImplemented:
            are_routes_not_equivalent = NotImplemented
        else:
            are_routes_not_equivalent = not are_routes_equivalent
        return are_routes_not_equivalent

    # _IRouteCollection
    def __len__(self):
        # Cannot call tuple() or list() on self because these functions use
        # len() internally, causing an infinite recursion
        routes = set(self)
        routes_count = len(routes)
        return routes_count

    # _IRouteCollection
    def __iter__(self):
        return iter(self._routes)


@implement_interface(_IRoute)
class _RouteSpecialization(object):

    def __init__(
        self,
        specialized_route,
        generalized_route,
        specialized_sub_routes,
        ):
        for sub_route in specialized_route:
            generalized_route._validate_new_sub_route(sub_route)

        super(_RouteSpecialization, self).__init__()
        self._specialized_route = specialized_route
        self._generalized_route = generalized_route

        self._specialized_sub_routes_by_name = {}
        self._specialized_sub_routes_without_name = []

        for specialized_sub_route in specialized_sub_routes:
            self._add_specialized_sub_route(specialized_sub_route)

    def _add_specialized_sub_route(self, specialized_sub_route):
        self._validate_specialized_sub_route(specialized_sub_route)

        specialized_sub_route_name = specialized_sub_route.get_name()
        if specialized_sub_route_name:
            self._specialized_sub_routes_by_name[specialized_sub_route_name] = \
                specialized_sub_route
        else:
            self._specialized_sub_routes_without_name.append(
                specialized_sub_route,
                )

    def _validate_specialized_sub_route(self, specialized_sub_route):
        if self._is_route_specialized(specialized_sub_route):
            is_specialization_valid = False
            for sub_route in self:
                if specialized_sub_route._is_specialization_of_route(sub_route):
                    is_specialization_valid = True
                    break
        else:
            is_specialization_valid = False

        if not is_specialization_valid:
            exc_message = \
                'Route {!r} is not specializing a sub-route inside {!r}'.format(
                    specialized_sub_route.get_name(),
                    self.get_name(),
                    )
            raise InvalidSpecializationError(exc_message)

        current_specialization_names = set(_get_route_names(self)) - \
            set(_get_route_names(self._generalized_route))

        candidate_sub_route_names = \
            _get_route_names(specialized_sub_route)

        for candidate_sub_route_name in candidate_sub_route_names:
            if candidate_sub_route_name in current_specialization_names:
                raise InvalidSpecializationError(candidate_sub_route_name)


    def __repr__(self):
        repr_ = '<Specialization of {!r} with view {!r}>'.format(
            self._generalized_route,
            self._specialized_route.get_view(),
            )
        return repr_

    def __len__(self):
        generalized_route_length = len(self._generalized_route)
        specialized_route_length = len(self._specialized_route)
        return generalized_route_length + specialized_route_length

    def __iter__(self):
        generalization_sub_routes = self._get_generalization_sub_routes()
        all_sub_routes = chain(
            generalization_sub_routes,
            self._specialized_route,
            )
        return all_sub_routes

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_generalized_routes_equivalent = \
                 self._generalized_route == other._generalized_route
            are_specialized_routes_equivalent = \
                self._specialized_route == other._specialized_route
            are_equivalent = are_generalized_routes_equivalent and \
                are_specialized_routes_equivalent
        else:
            are_equivalent = NotImplemented
        return are_equivalent

    def __ne__(self, other):
        are_equivalent = self.__eq__(other)
        if are_equivalent == NotImplemented:
            are_not_equivalent = NotImplemented
        else:
            are_not_equivalent = not are_equivalent
        return are_not_equivalent

    def _get_generalization_sub_routes(self):
        for generalized_sub_route in self._generalized_route:
            sub_route = self._get_specialized_sub_route_for_generalization(
                generalized_sub_route,
                )
            yield sub_route

    def _get_specialized_sub_route_for_generalization(
        self,
        generalized_sub_route,
        ):
        sub_route_name = generalized_sub_route.get_name()
        if sub_route_name:
            sub_route = self._specialized_sub_routes_by_name.get(
                sub_route_name,
                generalized_sub_route,
                )
        else:
            sub_route = \
                self._get_unnamed_specialized_sub_route_for_generalization(
                    generalized_sub_route,
                    )
        return sub_route

    def _get_unnamed_specialized_sub_route_for_generalization(
        self,
        generalized_sub_route,
        ):
        for specialized_sub_route in self._specialized_sub_routes_without_name:
            if specialized_sub_route._is_specialization_of_route(
                generalized_sub_route,
                ):
                sub_route = specialized_sub_route
                break
        else:
            sub_route = generalized_sub_route

        return sub_route

    def _is_specialization_of_route(self, route):
        generalized_route = self._generalized_route
        if generalized_route == route:
            is_specialization_of_route = True
        elif self._is_route_specialized(generalized_route):
            is_specialization_of_route = \
                generalized_route._is_specialization_of_route(route)
        else:
            is_specialization_of_route = False
        return is_specialization_of_route

    # _IRoute
    def get_name(self):
        name = self._generalized_route.get_name()
        return name

    # _IRoute
    def get_view(self):
        specialized_sub_route_view = self._specialized_route.get_view()
        if specialized_sub_route_view:
            view = specialized_sub_route_view
        else:
            view = self._generalized_route.get_view()

        return view

    def _validate_new_sub_route(self, sub_route):
        self._generalized_route._validate_new_sub_route(sub_route)

    # _IRoute
    def create_specialization(
        self,
        view=None,
        additional_sub_routes=(),
        specialized_sub_routes=(),
        ):
        specialized_route = BaseRoute(view, None, additional_sub_routes)

        route_specialization = _RouteSpecialization(
            specialized_route,
            self,
            specialized_sub_routes,
            )
        return route_specialization

    @classmethod
    def _is_route_specialized(cls, route):
        return isinstance(route, cls)


def get_route_by_name(route, route_name):
    current_route_name = route.get_name()
    if current_route_name == route_name:
        matching_route = route
    else:
        matching_route = _get_sub_route_by_name(route, route_name)

    if not matching_route:
        exc_message = 'Route {!r} does not contain one named {!r}'.format(
            current_route_name,
            route_name,
            )
        raise NonExistingRouteError(exc_message)

    return matching_route


def _get_sub_route_by_name(route, route_name):
    matching_sub_route = None
    for sub_route in route.sub_routes:
        try:
            matching_sub_route = get_route_by_name(sub_route, route_name)
        except NonExistingRouteError:
            pass
        else:
            break

    return matching_sub_route


def _get_route_names(route):
    route_names = []

    current_route_name = route.get_name()
    if current_route_name:
        route_names.append(current_route_name)

    for sub_route in route.sub_routes:
        sub_route_names = _get_route_names(sub_route)
        route_names.extend(sub_route_names)

    return route_names
