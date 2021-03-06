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

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from itertools import chain

from django_routing._utils import are_objects_inequivalent


class RoutingException(Exception):
    pass


class DuplicatedRouteError(RoutingException):
    pass


class NonExistingRouteError(RoutingException):
    pass


class InvalidSpecializationError(RoutingException):
    pass


class _BaseRoute(object):

    __metaclass__ = ABCMeta

    name = abstractproperty()

    view = abstractproperty()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_views_equivalent = self.view == other.view
            are_names_equivalent = self.name == other.name
            are_sub_routes_equivalent = self.sub_routes == other.sub_routes

            are_routes_equivalent = all((
                are_views_equivalent,
                are_names_equivalent,
                are_sub_routes_equivalent,
                ))
        else:
            are_routes_equivalent = NotImplemented

        return are_routes_equivalent

    __ne__ = are_objects_inequivalent

    def get_route_by_name(self, route_name):
        if self.name == route_name:
            matching_route = self
        else:
            matching_route = self._get_sub_route_by_name(route_name)

        if not matching_route:
            exc_message = 'self {!r} does not contain one named {!r}'.format(
                self.name,
                route_name,
                )
            raise NonExistingRouteError(exc_message)

        return matching_route

    def _get_sub_route_by_name(self, route_name):
        matching_sub_route = None
        for sub_route in self.sub_routes:
            try:
                matching_sub_route = sub_route.get_route_by_name(route_name)
            except NonExistingRouteError:
                pass
            else:
                break

        return matching_sub_route

    def get_route_names(self):
        route_names = []

        if self.name:
            route_names.append(self.name)

        for sub_route in self.sub_routes:
            sub_route_names = sub_route.get_route_names()
            route_names.extend(sub_route_names)

        return route_names

    def _require_route_name_not_in_route(self, route_name):
        route_names = self.get_route_names()
        if route_name in route_names:
            raise DuplicatedRouteError(route_name)

    def create_specialization(
        self,
        view=None,
        additional_sub_routes=(),
        specialized_sub_routes=(),
        ):
        route_specialization = _RouteSpecialization(
            view,
            self,
            additional_sub_routes,
            specialized_sub_routes,
            )
        return route_specialization


class Route(_BaseRoute):

    def __init__(self, view, name, sub_routes=()):
        super(Route, self).__init__()

        self._view = view
        self._name = name

        for sub_route in sub_routes:
            sub_route._require_route_name_not_in_route(#pylint:disable=W0212
                name,
                )
        self.sub_routes = _RouteCollection(sub_routes)

    def __repr__(self):
        repr_template = '<{class_name} view={view!r} name={name!r} with ' \
            '{sub_route_count} sub-routes>'
        repr_ = repr_template.format(
            class_name=self.__class__.__name__,
            name=self.name,
            view=self.view,
            sub_route_count=len(self.sub_routes),
            )
        return repr_

    @property
    def name(self):
        return self._name

    @property
    def view(self):
        return self._view


class _BaseRouteCollection(object):

    __metaclass__ = ABCMeta

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_routes_equivalent = tuple(self) == tuple(other)
        else:
            are_routes_equivalent = NotImplemented
        return are_routes_equivalent

    __ne__ = are_objects_inequivalent

    def __len__(self):
        # Cannot call tuple() or list() on self because these functions use
        # len() internally, causing an infinite recursion
        routes = set(self)
        routes_count = len(routes)
        return routes_count

    @abstractmethod
    def __iter__(self):
        pass  # pragma: no cover


class _RouteCollection(_BaseRouteCollection):

    def __init__(self, routes):
        super(_RouteCollection, self).__init__()

        self._routes = []
        for route in routes:
            self._add_route(route)

    def _add_route(self, route):
        self._validate_new_route(route)
        self._routes.append(route)

    def _validate_new_route(self, route):
        _require_route_names_uniqueness_in_collection(self, route)

        if not route.name:
            self._require_uniqueness_of_unnamed_route_in_collection(route)

    def _require_uniqueness_of_unnamed_route_in_collection(self, route):
        if route in self:
            raise DuplicatedRouteError(repr(route))

    def __repr__(self):
        repr_ = '{class_name}({routes})'.format(
            class_name=self.__class__.__name__,
            routes=self._routes,
            )
        return repr_

    def __iter__(self):
        return iter(self._routes)


class _RouteSpecialization(_BaseRoute):

    def __init__(
        self,
        view,
        generalized_route,
        additional_sub_routes,
        specialized_sub_routes,
        ):
        for sub_route in chain(additional_sub_routes, specialized_sub_routes):
            sub_route._require_route_name_not_in_route(#pylint:disable=W0212
                generalized_route.name,
                )

        super(_RouteSpecialization, self).__init__()
        self._view = view
        self._generalized_route = generalized_route

        self.sub_routes = _RouteSpecializationCollection(
            generalized_route.sub_routes,
            specialized_sub_routes,
            additional_sub_routes,
            )

    def __repr__(self):
        repr_ = '<Specialization of {!r} with view {!r}>'.format(
            self._generalized_route,
            self.view,
            )
        return repr_

    def __eq__(self, other):
        are_equivalent = super(_RouteSpecialization, self).__eq__(other)

        if are_equivalent != NotImplemented:
            other_generalization = \
                _RouteSpecialization.get_route_generalization(other)
            are_generalized_routes_equivalent = \
                 self._generalized_route == other_generalization
            are_equivalent = are_equivalent and \
                are_generalized_routes_equivalent

        return are_equivalent

    @property
    def name(self):
        name = self._generalized_route.name
        return name

    @property
    def view(self):
        if self._view:
            view = self._view
        else:
            view = self._generalized_route.view

        return view

    @staticmethod
    def get_route_generalization(route):
        return route._generalized_route  #pylint:disable=W0212


class _RouteSpecializationCollection(_BaseRouteCollection):

    def __init__(
        self,
        generalized_routes,
        specialized_routes,
        additional_routes,
        ):
        super(_RouteSpecializationCollection, self).__init__()

        self._generalized_routes = generalized_routes

        self._additional_routes = additional_routes
        for additional_route in additional_routes:
            _require_route_names_uniqueness_in_collection(
                generalized_routes,
                additional_route,
                )

        self._specialized_routes = []
        for specialized_route in specialized_routes:
            self._add_specialized_route(specialized_route)

    def _add_specialized_route(self, specialized_route):
        self._validate_specialized_route(specialized_route)
        self._specialized_routes.append(specialized_route)

    def _validate_specialized_route(self, specialized_route):
        self._require_route_to_be_specialization(specialized_route)

        specialized_route_generalization = \
            _RouteSpecialization.get_route_generalization(specialized_route)
        self._require_generalized_route_in_collection(
            specialized_route_generalization,
            )
        self._require_route_not_already_specialized(
            specialized_route_generalization,
            )

        _require_route_names_uniqueness_in_collection(self, specialized_route)

    @staticmethod
    def _require_route_to_be_specialization(route):
        if not _is_route_specialized(route):
            exc_message = 'Route {!r} is not specialized'.format(route)
            raise InvalidSpecializationError(exc_message)

    def _require_generalized_route_in_collection(self, generalized_route):
        for existing_generalized_route in self._generalized_routes:
            is_specialization_valid = _is_specialization_of_route(
                generalized_route,
                existing_generalized_route,
                )
            if is_specialization_valid:
                break
        else:
            exc_message = 'No such generalization {!r}'.format(
                generalized_route,
                )
            raise InvalidSpecializationError(exc_message)

    def _require_route_not_already_specialized(self, route):
        for existing_specialized_route in self._specialized_routes:
            if _is_specialization_of_route(existing_specialized_route, route):
                raise InvalidSpecializationError(
                    'Route {!r} cannot be specialized twice'.format(route)
                    )

    def __repr__(self):
        repr_ = '{}({!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self._generalized_routes,
            self._specialized_routes,
            self._additional_routes,
            )
        return repr_

    def __iter__(self):
        generalized_routes_as_specializations = \
            self._get_generalized_routes_as_specializations()
        all_sub_routes = chain(
            generalized_routes_as_specializations,
            self._additional_routes,
            )
        return all_sub_routes

    def _get_generalized_routes_as_specializations(self):
        for generalized_route in self._generalized_routes:
            route = self._get_specialized_route_for_generalization(
                generalized_route,
                )
            yield route

    def _get_specialized_route_for_generalization(self, generalized_route):
        for specialized_route in self._specialized_routes:
            if _is_specialization_of_route(specialized_route, generalized_route):
                route = specialized_route
                break
        else:
            route = generalized_route

        return route


def _is_specialization_of_route(specialized_route, generalized_route):
    if _is_route_specialized(specialized_route):
        specialized_route_generalization = \
            _RouteSpecialization.get_route_generalization(specialized_route)
        is_specialization_of_route = _is_specialization_of_route(
            specialized_route_generalization,
            generalized_route,
            )
    else:
        is_specialization_of_route = generalized_route == specialized_route
    return is_specialization_of_route


def _is_route_specialized(route):
    return isinstance(route, _RouteSpecialization)


def _require_route_names_uniqueness_in_collection(route_collection, route):
    route_collection_route_names = []
    for existing_route in route_collection:
        route_collection_route_names.extend(existing_route.get_route_names())

    if _is_route_specialized(route):
        route_generalization = \
            _RouteSpecialization.get_route_generalization(route)
        generalized_route_names = route_generalization.get_route_names()
    else:
        generalized_route_names = []

    candidate_sub_route_names = route.get_route_names()
    for candidate_sub_route_name in candidate_sub_route_names:
        is_sub_route_name_duplicated = \
            candidate_sub_route_name in route_collection_route_names and \
                candidate_sub_route_name not in generalized_route_names
        if is_sub_route_name_duplicated:
            raise DuplicatedRouteError(candidate_sub_route_name)
