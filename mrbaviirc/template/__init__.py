# \file
# \author Brian Allen Vanderburg II
# \copyright MIT license
# \date 2016
#
# This file provides a simple light-weight template engine.

# Credits
################################################################################

# Templite
#------------------------------------------------------------------------------
# Some portions of the code in the template package were originally based on
# the Templite class in the 500 lines or less project.  However, the code
# has been largely rewritten and refactored to my own needs.  Still some of the
# original ideas originated with Templite
#


from .errors import *
from .renderers import *
from .env import Environment
from .template import Template


