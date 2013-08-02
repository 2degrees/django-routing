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

        self._view = view
        self._name = name

        self._sub_routes = []
        for sub_route in sub_routes:
            self._add_sub_route(sub_route)

    def __repr__(self):
        route_class_name = self.__class__.__name__
        repr_ = '{class_name}({view!r}, {name!r}, {sub_routes!r})'.format(
            class_name=route_class_name,
            name=self._name,
            view=self._view,
            sub_routes=tuple(self),
            )
        return repr_

    def __iter__(self):
        return iter(self._sub_routes)

    def get_route_by_name(self, route_name):
        if self.get_name() == route_name:
            matching_route = self
        else:
            matching_route = self._get_sub_route_by_name(route_name)

        if not matching_route:
            exc_message = '{!r} does not contain a route named {!r}'.format(
                self,
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
        return self._name

    def get_view(self):
        return self._view

    def _add_sub_route(self, sub_route):
        self._validate_new_sub_route_name(sub_route)
        self._sub_routes.append(sub_route)

    def _validate_new_sub_route_name(self, sub_route):
        current_route_names = self._get_route_names()
        candidate_sub_route_names = sub_route._get_route_names()

        for candidate_sub_route_name in candidate_sub_route_names:
            if candidate_sub_route_name in current_route_names:
                exc_message = 'The route name {!r} is duplicated' \
                    .format(candidate_sub_route_name)
                raise DuplicatedRouteNameError(exc_message)

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
        additional_sub_routes=(),
        specialized_sub_routes=(),
        views_by_route_name=None,
        ):
        return self

