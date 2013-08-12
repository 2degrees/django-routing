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
    def __len__(self):
        pass

    @interface_method
    def __iter__(self):
        pass

    @interface_method
    def get_name(self):
        pass

    @interface_method
    def get_view(self):
        pass

    @interface_method
    def get_route_by_name(self, route_name):
        pass

    @interface_method
    def create_specialization(
        self,
        view=None,
        additional_sub_routes=(),
        specialized_sub_routes=(),
        ):
        pass


@implement_interface(_IRoute)
class BaseRoute(object):

    def __init__(self, view, name, sub_routes=()):
        super(BaseRoute, self).__init__()

        self._view = view
        self._name = name

        self._sub_routes = []
        for sub_route in sub_routes:
            self._add_sub_route(sub_route)

    def __repr__(self):
        route_class_name = self.__class__.__name__
        repr_ = '{class_name}({view!r}, {name!r}, {sub_routes!r})'.format(
            class_name=route_class_name,
            name=self.get_name(),
            view=self.get_view(),
            sub_routes=tuple(self),
            )
        return repr_

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            are_views_equivalent = self.get_view() == other.get_view()
            are_names_equivalent = self.get_name() == other.get_name()
            are_sub_routes_equivalent = tuple(self) == tuple(other)

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

    def __len__(self):
        # Cannot call tuple() or list() on self because these functions use
        # len() internally, causing an infinite recursion
        sub_routes = set(self)
        sub_routes_count = len(sub_routes)
        return sub_routes_count

    def __nonzero__(self):
        return True

    def __iter__(self):
        return iter(self._sub_routes)

    def get_route_by_name(self, route_name):
        current_route_name = self.get_name()
        if current_route_name == route_name:
            matching_route = self
        else:
            matching_route = _get_sub_route_by_name(self, route_name)

        if not matching_route:
            exc_message = 'Route {!r} does not contain one named {!r}'.format(
                current_route_name,
                route_name,
                )
            raise NonExistingRouteError(exc_message)

        return matching_route

    def get_name(self):
        return self._name

    def get_view(self):
        return self._view

    def _add_sub_route(self, sub_route):
        self._validate_new_sub_route(sub_route)
        self._sub_routes.append(sub_route)

    def _validate_new_sub_route(self, sub_route):
        self._validate_new_sub_route_names_recursively(sub_route)

        if not sub_route.get_name():
            self._validate_new_unnamed_sub_route(sub_route)

    def _validate_new_sub_route_names_recursively(self, sub_route):
        current_route_names = self._get_route_names()
        candidate_sub_route_names = sub_route._get_route_names()

        for candidate_sub_route_name in candidate_sub_route_names:
            if candidate_sub_route_name in current_route_names:
                raise DuplicatedRouteError(candidate_sub_route_name)

    def _validate_new_unnamed_sub_route(self, sub_route):
        if sub_route in self:
            exc_message = \
                'Duplicated unnamed sub-route in {!r}'.format(self.get_name())
            raise DuplicatedRouteError(exc_message)

    def _get_route_names(self):
        route_names = []

        current_route_name = self.get_name()
        if current_route_name:
            route_names.append(current_route_name)

        for sub_route in self:
            sub_route_names = sub_route._get_route_names()
            route_names.extend(sub_route_names)

        return route_names

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
            for sub_route in chain(self, self._generalized_route):
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

    def __nonzero__(self):
        return True

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

    def get_name(self):
        name = self._generalized_route.get_name()
        return name

    def get_view(self):
        specialized_sub_route_view = self._specialized_route.get_view()
        if specialized_sub_route_view:
            view = specialized_sub_route_view
        else:
            view = self._generalized_route.get_view()

        return view

    def get_route_by_name(self, route_name):
        current_route_name = self.get_name()
        if current_route_name == route_name:
            matching_route = self
        else:
            matching_route = _get_sub_route_by_name(self, route_name)

        if not matching_route:
            exc_message = 'Route {!r} does not contain one named {!r}'.format(
                current_route_name,
                route_name,
                )
            raise NonExistingRouteError(exc_message)

        return matching_route

    def _validate_new_sub_route(self, sub_route):
        self._generalized_route._validate_new_sub_route(sub_route)

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


def _get_sub_route_by_name(route, route_name):
    matching_sub_route = None
    for sub_route in route:
        try:
            matching_sub_route = sub_route.get_route_by_name(route_name)
        except NonExistingRouteError:
            pass
        else:
            break

    return matching_sub_route
