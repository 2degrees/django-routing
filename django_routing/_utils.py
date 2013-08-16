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


def are_objects_inequivalent(object_1, object_2):
    are_objects_equivalent = object_1.__eq__(object_2)
    if are_objects_equivalent == NotImplemented:
        are_objects_inequivalent_ = NotImplemented
    else:
        are_objects_inequivalent_ = not are_objects_equivalent
    return are_objects_inequivalent_
