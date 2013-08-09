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
from itertools import chain


class RoutingException(Exception):
    pass


class DuplicatedRouteNameError(RoutingException):
    pass


class NonExistingRouteError(RoutingException):
    pass


class InvalidSpecializationError(RoutingException):
    pass


class BaseRoute(object):

    __metaclass__ = ABCMeta

    def __init__(self, view, name, sub_routes=()):
        super(BaseRoute, self).__init__()

        self._generalized_route = None
        self._specialized_sub_routes_by_name = {}
        self._specialized_sub_routes_without_name = []

        self._view = view
        self._name = name

        self._sub_routes = []
        for sub_route in sub_routes:
            self._add_sub_route(sub_route)

    def __repr__(self):
        if self._is_specialization:
            repr_ = '<Specialization of {!r} with view {!r}>'.format(
                self._generalized_route,
                self._view,
                )
        else:
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
            are_generalizations_equivalent = \
                self._generalized_route == other._generalized_route
            are_views_equivalent = self.get_view() == other.get_view()
            are_names_equivalent = self.get_name() == other.get_name()
            are_sub_routes_equivalent = tuple(self) == tuple(other)

            are_routes_equivalent = all((
                are_generalizations_equivalent,
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
        if self._is_specialization:
            generalization_sub_routes = self._get_generalization_sub_routes()
            all_sub_routes = chain(generalization_sub_routes, self._sub_routes)
        else:
            all_sub_routes = iter(self._sub_routes)

        return all_sub_routes

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
            if specialized_sub_route._is_specialization_of_route(generalized_sub_route):
                sub_route = specialized_sub_route
                break
        else:
            sub_route = generalized_sub_route

        return sub_route

    def get_route_by_name(self, route_name):
        current_route_name = self.get_name()
        if current_route_name == route_name:
            matching_route = self
        else:
            matching_route = self._get_sub_route_by_name(route_name)

        if not matching_route:
            exc_message = 'Route {!r} does not contain one named {!r}'.format(
                current_route_name,
                route_name,
                )
            raise NonExistingRouteError(exc_message)

        return matching_route

    def _get_sub_route_by_name(self, route_name):
        matching_sub_route = None
        for sub_route in self:
            try:
                matching_sub_route = sub_route.get_route_by_name(route_name)
            except NonExistingRouteError:
                pass
            else:
                break

        return matching_sub_route

    def get_name(self):
        if self._is_specialization:
            name = self._generalized_route.get_name()
        else:
            name = self._name
        return name

    def get_view(self):
        if self._view:
            view = self._view
        elif self._is_specialization:
            view = self._generalized_route.get_view()
        else:
            view = None

        return view

    def _add_sub_route(self, sub_route):
        self._validate_new_sub_route_name(sub_route)
        self._sub_routes.append(sub_route)

    def _validate_new_sub_route_name(self, sub_route):
        current_route_names = self._get_route_names()
        candidate_sub_route_names = sub_route._get_route_names()

        for candidate_sub_route_name in candidate_sub_route_names:
            if candidate_sub_route_name in current_route_names:
                raise DuplicatedRouteNameError(candidate_sub_route_name)

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
        specialization = self.__class__(view, None)
        specialization._generalized_route = self

        for sub_route in additional_sub_routes:
            specialization._add_sub_route(sub_route)

        for specialized_sub_route in specialized_sub_routes:
            specialization._add_specialized_sub_route(specialized_sub_route)

        return specialization

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
        specialized_sub_route_name = specialized_sub_route.get_name()
        generalized_sub_route = \
            self._get_sub_route_by_name(specialized_sub_route_name)

        if not generalized_sub_route:
            exc_message = 'No such route {!r} inside {!r}'.format(
                specialized_sub_route_name,
                self.get_name(),
                )
            raise InvalidSpecializationError(exc_message)

        is_specialization_valid = False
        for sub_route in self:
            if specialized_sub_route._is_specialization_of_route(sub_route):
                is_specialization_valid = True
                break

        if not is_specialization_valid:
            exc_message = \
                'Route {!r} is not specializing a sub-route inside {!r}'.format(
                    specialized_sub_route_name,
                    self.get_name(),
                    )
            raise InvalidSpecializationError(exc_message)

    def _is_specialization_of_route(self, route):
        generalized_route = self._generalized_route
        if generalized_route:
            if generalized_route == route:
                is_specialization_of_route = True
            else:
                is_specialization_of_route = \
                    generalized_route._is_specialization_of_route(route)
        else:
            is_specialization_of_route = False
        return is_specialization_of_route

    @property
    def _is_specialization(self):
        return bool(self._generalized_route)
