# -*- coding: utf-8; -*-

"""

This package contains all classes and other code used to access
data. Always use the interfaces defined here - do not communicate
directly with the database.

"""

__all__ = ["jobs"]

import random

def RandomHexString(i):
    """

    Returns a random string of hexadecimal characters of length i

    """

    return "".join([random.choice("0123456789abcdef") for i in xrange(i)])
