""" Provide the nodes for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"

__all__ = [
    "Node", "NodeList",  "TextNode", "IfNode", "ForNode", "SwitchNode",
    "EmitNode", "IncludeNode", "ReturnNode", "AssignNode", "SectionNode",
    "UseSectionNode", "ScopeNode", "VarNode", "ErrorNode","ImportNode",
    "DoNode"
]


from .errors import *
from .renderers import StringRenderer


class Node(object):
    """ A node is a part of the expression that is rendered. """

    def __init__(self, template, line):
        """ Initialize the node. """
        self._template = template
        self._line = line
        self._env = template._env

    def render(self, renderer):
        """ Render the node to a renderer. """
        raise NotImplementedError


class NodeList(object):
    """ A list of nodes. """

    def __init__(self):
        """Initialize. """
        self._nodes = []

    def append(self, node):
        """ Append a node to the list. """
        self._nodes.append(node)

    def extend(self, nodelist):
        """ Extend one node list with another. """
        self._nodes.extend(nodelist._nodes)

    def render(self, renderer):
        """ Render all nodes. """
        for node in self._nodes:
            node.render(renderer)

    def __getitem__(self, n):
        return self._nodes[n]


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, line, text):
        """ Initialize a text node. """
        Node.__init__(self, template, line)
        self._text = text

    def render(self, renderer):
        """ Render content from a text node. """
        renderer.render(self._text)


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, line, expr):
        """ Initialize the if node. """
        Node.__init__(self, template, line)
        self._ifs = [(expr, NodeList())]
        self._else = None
        self._nodes = self._ifs[0][1]

    def add_elif(self, expr):
        """ Add an if section. """
        # TODO: error if self._else exists
        self._ifs.append((expr, NodeList()))
        self._nodes = self._ifs[-1][1]

    def add_else(self):
        """ Add an else. """
        self._else = NodeList()
        self._nodes = self._else

    def render(self, renderer):
        """ Render the if node. """
        for (expr, nodes) in self._ifs:
            result = expr.eval()
            if result:
                nodes.render(renderer)
                return

        if self._else:
            self._else.render(renderer)


class ForNode(Node):
    """ A node for handling for loops. """

    def __init__(self, template, line, var, cvar, expr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self._var = var
        self._cvar = cvar
        self._expr = expr

        self._for = NodeList()
        self._else = None
        self._nodes = self._for

    def add_else(self):
        """ Add an else section. """
        self._else = NodeList()
        self._nodes = self._else

    def render(self, renderer):
        """ Render the for node. """
        env = self._env

        # Iterate over each value
        values = self._expr.eval()
        do_else = True
        if values:
            index = 0
            for var in values:
                do_else = False
                if self._cvar:
                    env.set(self._cvar, index)
                env.set(self._var, var)
                index += 1
                                    
                # Execute each sub-node
                self._for.render(renderer)

        if do_else and self._else:
            self._else.render(renderer)


class SwitchNode(Node):
    """ A node for basic if/elif/elif/else nesting. """
    types = ["lt", "le", "gt", "ge", "ne", "eq", "bt"]
    argc = [1, 1, 1, 1, 1, 1, 2]
    cbs = [
        lambda *args: args[0] < args[1],
        lambda *args: args[0] <= args[1],
        lambda *args: args[0] > args[1],
        lambda *args: args[0] >= args[1],
        lambda *args: args[0] != args[1],
        lambda *args: args[0] == args[1],
        lambda *args: args[0] >= args[1] and args[0] <= args[2]
    ]

    def __init__(self, template, line, expr):
        """ Initialize the switch node. """
        Node.__init__(self, template, line)
        self._expr = expr
        self._default = NodeList()
        self._cases = []
        self._nodes = self._default

    def add_case(self, cb, exprs):
        """ Add a case node. """
        self._cases.append((cb, NodeList(), exprs))
        self._nodes = self._cases[-1][1]

    def render(self, renderer):
        """ Render the node. """
        value = self._expr.eval()

        for cb, nodes, exprs in self._cases:
            params = [expr.eval() for expr in exprs]
            if cb(value, *params):
                nodes.render(renderer)
                return

        self._default.render(renderer)


class EmitNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Render the output. """
        renderer.render(str(self._expr.eval()))


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, expr, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self._expr = expr
        self._assigns = assigns
        self._retvar = retvar

    def render(self, renderer):
        """ Actually do the work of including the template. """
        try:
            template = self._env.load_file(
                str(self._expr.eval()),
                self._template._filename
            )
        except (IOError, OSError, RestrictedError) as e:
            raise TemplateError(
                str(e),
                self._template._filename,
                self._line
            )

        context = {}
        for (var, expr) in self._assigns:
            context[var] = expr.eval()

        template.render(renderer, context, self._retvar)


class ReturnNode(Node):
    """ A node to set a return variable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._assigns = assigns

    def render(self, renderer):
        """ Set the return nodes. """

        result = {}
        for (var, expr) in self._assigns:
            result[var] = expr.eval()

        self._env.set(":return:", result, 2)


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns, where):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._assigns = assigns
        self._where = where

    def render(self, renderer):
        """ Set the value. """
        env = self._env

        for (var, expr) in self._assigns:
            env.set(var, expr.eval(), self._where)


class SectionNode(Node):
    """ A node to redirect template output to a section. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._expr = expr
        self._nodes = NodeList()

    def render(self, renderer):
        """ Redirect output to a section. """

        section = str(self._expr.eval())
        renderer.push_section(section)
        self._nodes.render(renderer)
        renderer.pop_section()


class UseSectionNode(Node):
    """ A node to use a section in the output. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Render the section to the output. """

        section = str(self._expr.eval())
        renderer.render(renderer.get_section(section))


class ScopeNode(Node):
    """ Create and remove scopes. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._assigns = assigns
        self._nodes = NodeList()

    def render(self, renderer):
        """ Render the scope. """
        env = self._env
        env._push_scope()
        try:
            for (var, expr) in self._assigns:
                env.set(var, expr.eval())

            self._nodes.render(renderer)
        finally:
            env._pop_scope()


class VarNode(Node):
    """ Capture output into a variable. """

    def __init__(self, template, line, var):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._var = var
        self._nodes = NodeList()

    def render(self, renderer):
        """ Render the results and capture into a variable. """

        new_renderer = StringRenderer()
        self._nodes.render(new_renderer)
        self._env.set(self._var, new_renderer.get())

class ErrorNode(Node):
    """ Raise an error from the template. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._expr = expr

    def render(self, renderer):
        """ Raise the error. """
        raise RaisedError(
            str(self._expr.eval()),
            self._template._filename,
            self._line
        )

class ImportNode(Node):
    """ Import a library to a variable in the current scope. """
    def __init__(self, template, line, assigns, where=0):
        Node.__init__(self, template, line)
        self._assigns = assigns
        self._where = where

    def render(self, renderer):
        """ Do the import. """
        where = self._where
        env = self._env

        for (var, expr) in self._assigns:
            name = expr.eval()
            try:
                imp = env.load_import(name)
                env.set(var, imp, where)
            except KeyError:
                raise UnknownImportError(
                    "No such import: {0}".format(name),
                    self._template._filename,
                    self._line
                )

class DoNode(Node):
    """ Evaluate expressions and discard the rsults. """

    def __init__(self, template, line, nodes):
        """ Initialize. """
        Node.__init__(self, template, line)
        self._nodes = nodes

    def render(self, renderer):
        """ Set the value. """
        for node in self._nodes:
            node.eval();

