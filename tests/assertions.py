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
from nose.tools import assert_raises_regexp
from nose.tools import ok_


def assert_raises_substring(exception_class, exception_message_substring):
    exception_message_regex = '^.*{}.*$'.format(exception_message_substring)
    return assert_raises_regexp(exception_class, exception_message_regex)


def assert_equivalent(object_1, object_2):
    ok_(object_1 == object_2)
    assert_false(object_1 != object_2)

    ok_(object_2 == object_1)
    assert_false(object_2 != object_1)


def assert_non_equivalent(object_1, object_2):
    ok_(object_1 != object_2)
    assert_false(object_1 == object_2)

    ok_(object_2 != object_1)
    assert_false(object_2 == object_1)
