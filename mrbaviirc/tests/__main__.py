# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file runs the unit tests for mrbaviirc

import unittest

from . import template


# Add our tests
suite = unittest.TestSuite()

suite.addTest(template.suite())


# Run out tests
runner = unittest.TextTestRunner()
runner.run(suite)

