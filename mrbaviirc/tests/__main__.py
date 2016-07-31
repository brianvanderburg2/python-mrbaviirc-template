""" Main entry point for unit tests. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import unittest

from . import template


# Add our tests
suite = unittest.TestSuite()

suite.addTest(template.suite())


# Run out tests
runner = unittest.TextTestRunner()
runner.run(suite)

