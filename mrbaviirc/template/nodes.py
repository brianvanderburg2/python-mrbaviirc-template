""" Provide the nodes for the template engine. """
# pylint: disable=too-few-public-methods,too-many-arguments

__author__ = "Brian Allen Vanderburg II"
__copyright__ = "Copyright 2016"
__license__ = "Apache License 2.0"

__all__ = [
    "Node", "NodeList", "TextNode", "IfNode", "ForIterNode", "ForIncrNode",
    "SwitchNode", "EmitNode", "IncludeNode", "ReturnNode", "AssignNode",
    "SectionNode", "UseSectionNode", "ScopeNode", "VarNode", "ErrorNode",
    "ImportNode", "DoNode", "UnsetNode", "CodeNode", "ExpandNode", "HookNode",
    "BreakNode", "ContinueNode"
]


from .errors import TemplateError, RaisedError, UnknownImportError, RestrictedError, AbortError
from .renderers import StringRenderer


class Node(object):
    """ A node is a part of the expression that is rendered. """

    RENDER_BREAK = 1
    RENDER_CONTINUE = 2

    def __init__(self, template, line):
        """ Initialize the node. """
        self.template = template
        self.line = line
        self.env = template.env

    def render(self, renderer, scope):
        """ Render the node to a renderer.
            If a value is returned other than None, then for most other
            nodes it should return that value instantly.  Certain nodes
            may use the value in a special manor, such as break and
            continue nodes.
        """
        raise NotImplementedError


class NodeList(object):
    """ A list of nodes. """

    def __init__(self):
        """Initialize. """
        self.nodes = []

    def append(self, node):
        """ Append a node to the list. """
        self.nodes.append(node)

    def extend(self, nodelist):
        """ Extend one node list with another. """
        self.nodes.extend(nodelist.nodes)

    def render(self, renderer, scope):
        """ Render all nodes. """
        if scope.abort_fn and scope.abort_fn():
            raise AbortError("Nodelist render aborted")

        for node in self.nodes:
            result = node.render(renderer, scope)
            if result in (Node.RENDER_BREAK, Node.RENDER_CONTINUE):
                return result

    def __getitem__(self, index):
        return self.nodes[index]


class TextNode(Node):
    """ A node that represents a raw block of text. """

    def __init__(self, template, line, text):
        """ Initialize a text node. """
        Node.__init__(self, template, line)
        self.text = text

    def render(self, renderer, scope):
        """ Render content from a text node. """
        renderer.render(self.text)


class IfNode(Node):
    """ A node that manages if/elif/else. """

    def __init__(self, template, line, expr):
        """ Initialize the if node. """
        Node.__init__(self, template, line)
        self.ifs_nodes = [(expr, NodeList())]
        self.else_nodes = None
        self.nodes = self.ifs_nodes[0][1]

    def add_elif(self, expr):
        """ Add an if section. """
        # TODO: error if self.elses exists
        self.ifs_nodes.append((expr, NodeList()))
        self.nodes = self.ifs_nodes[-1][1]

    def add_else(self):
        """ Add an else. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, renderer, scope):
        """ Render the if node. """
        for (expr, nodes) in self.ifs_nodes:
            result = expr.eval(scope)
            if result:
                return nodes.render(renderer, scope)

        if self.else_nodes:
            return self.else_nodes.render(renderer, scope)


class ForIterNode(Node):
    """ A node for handling iteration for loops. """

    def __init__(self, template, line, var, cvar, expr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self.var = var
        self.cvar = cvar
        self.expr = expr

        self.for_nodes = NodeList()
        self.else_nodes = None
        self.nodes = self.for_nodes

    def add_else(self):
        """ Add an else section. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, renderer, scope):
        """ Render the for node. """
        # Iterate over each value
        values = self.expr.eval(scope)
        do_else = True
        if values:
            index = 0
            for var in values:
                do_else = False
                if self.cvar:
                    scope.set(self.cvar, index)
                scope.set(self.var, var)
                index += 1

                # Execute each sub-node
                result = self.for_nodes.render(renderer, scope)
                if result == Node.RENDER_BREAK:
                    break
                elif result == Node.RENDER_CONTINUE:
                    continue

        if do_else and self.else_nodes:
            return self.else_nodes.render(renderer, scope)


class ForIncrNode(Node):
    """ A node for handling increment for loops. """

    def __init__(self, template, line, init, test, incr):
        """ Initialize the for node. """
        Node.__init__(self, template, line)
        self.init = init
        self.test = test
        self.incr = incr

        self.for_nodes = NodeList()
        self.else_nodes = None
        self.nodes = self.for_nodes

    def add_else(self):
        """ Add an else section. """
        self.else_nodes = NodeList()
        self.nodes = self.else_nodes

    def render(self, renderer, scope):
        """ Render the for node. """
        # Init
        for (var, expr) in self.init:
            scope.set(var, expr.eval(scope))

        # Test
        do_else = True
        while bool(self.test.eval(scope)):
            do_else = False

            # Render nodes
            result = self.for_nodes.render(renderer, scope)
            if result == Node.RENDER_BREAK:
                break

            # Incr
            for (var, expr) in self.incr:
                scope.set(var, expr.eval(scope))

        if do_else and self.else_nodes:
            return self.else_nodes.render(renderer, scope)


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
        self.expr = expr
        self.default_nodes = NodeList()
        self.cases_nodes = []
        self.nodes = self.default_nodes

    def add_case(self, testfunc, exprs):
        """ Add a case node. """
        self.cases_nodes.append((testfunc, NodeList(), exprs))
        self.nodes = self.cases_nodes[-1][1]

    def render(self, renderer, scope):
        """ Render the node. """
        value = self.expr.eval(scope)

        for testfunc, nodes, exprs in self.cases_nodes:
            params = [expr.eval(scope) for expr in exprs]
            if testfunc(value, *params):
                return nodes.render(renderer, scope)

        return self.default_nodes.render(renderer, scope)


class EmitNode(Node):
    """ A node to output some value. """

    def __init__(self, template, line, expr):
        """ Initialize the node. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Render the output. """
        renderer.render(str(self.expr.eval(scope)))


class IncludeNode(Node):
    """ A node to include another template. """

    def __init__(self, template, line, expr, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.assigns = assigns
        self.retvar = retvar

    def render(self, renderer, scope):
        """ Actually do the work of including the template. """
        try:
            template = self.env.load_file(
                str(self.expr.eval(scope)),
                self.template
            )
        except (IOError, OSError, RestrictedError) as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )

        context = {}
        for (var, expr) in self.assigns:
            context[var] = expr.eval(scope)

        retval = template.nested_render(renderer, context, scope)
        if self.retvar:
            scope.set(self.retvar, retval)


class ReturnNode(Node):
    """ A node to set a return variable. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, renderer, scope):
        """ Set the return nodes. """

        result = {}
        for (var, expr) in self.assigns:
            result[var] = expr.eval(scope)

        current = scope.template_scope.setdefault(":return:", {})
        current.update(result)


class ExpandNode(Node):
    """ A node to expand variables into the current scope. """

    def __init__(self, template, line, expr):
        """ Initialize """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Expand the variables. """

        result = self.expr.eval(scope)
        try:
            scope.update(result)
        except (KeyError, TypeError, ValueError) as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )


class AssignNode(Node):
    """ Set a variable to a subvariable. """

    def __init__(self, template, line, assigns, where):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.where = where

    def render(self, renderer, scope):
        """ Set the value. """
        for (var, expr) in self.assigns:
            scope.set(var, expr.eval(scope), self.where)


class SectionNode(Node):
    """ A node to redirect template output to a section. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr
        self.nodes = NodeList()

    def render(self, renderer, scope):
        """ Redirect output to a section. """

        section = str(self.expr.eval(scope))
        renderer.push_section(section)
        self.nodes.render(renderer, scope)
        renderer.pop_section()


class UseSectionNode(Node):
    """ A node to use a section in the output. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Render the section to the output. """

        section = str(self.expr.eval(scope))
        renderer.render(renderer.get_section(section))


class ScopeNode(Node):
    """ Create and remove scopes. """

    def __init__(self, template, line, assigns):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.nodes = NodeList()

    def render(self, renderer, scope):
        """ Render the scope. """
        new_scope = scope.push()

        for (var, expr) in self.assigns:
            new_scope.set(var, expr.eval(new_scope))

        self.nodes.render(renderer, new_scope)


class CodeNode(Node):
    """ A node to execute python code. """

    def __init__(self, template, line, assigns, retvar):
        """ Initialize the include node. """
        Node.__init__(self, template, line)
        self.assigns = assigns
        self.retvar = retvar
        self.nodes = NodeList()
        self.code = None

    def render(self, renderer, scope):
        """ Actually do the work of including the template. """

        # Must be allowed globally in env and also locally in template
        if not self.env.code_enabled or not self.template.code_enabled:
            raise TemplateError(
                "Use of direct python code not allowed",
                self.template.filename,
                self.line
            )

        # Compile the code only once
        # TODO: does this need lock for threading
        if not self.code:
            # Get the code
            new_renderer = StringRenderer()
            self.nodes.render(new_renderer, scope)
            code = new_renderer.get()

            # Compile it
            try:
                self.code = compile(code, "<string>", "exec")
            except Exception as error:
                raise TemplateError(
                    str(error),
                    self.template.filename,
                    self.line
                )

        # Execute the code
        data = {}
        for (var, expr) in self.assigns:
            data[var] = expr.eval(scope)

        try:
            exec(self.code, data, data)
        except Exception as error:
            raise TemplateError(
                str(error),
                self.template.filename,
                self.line
            )

        # Handle return values
        if self.retvar:
            scope.set(self.retvar, data)


class VarNode(Node):
    """ Capture output into a variable. """

    def __init__(self, template, line, var):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.var = var
        self.nodes = NodeList()

    def render(self, renderer, scope):
        """ Render the results and capture into a variable. """

        new_renderer = StringRenderer()
        self.nodes.render(new_renderer, scope)
        scope.set(self.var, new_renderer.get())


class ErrorNode(Node):
    """ Raise an error from the template. """

    def __init__(self, template, line, expr):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.expr = expr

    def render(self, renderer, scope):
        """ Raise the error. """
        raise RaisedError(
            str(self.expr.eval(scope)),
            self.template.filename,
            self.line
        )


class ImportNode(Node):
    """ Import a library to a variable in the current scope. """
    def __init__(self, template, line, assigns):
        Node.__init__(self, template, line)
        self.assigns = assigns

    def render(self, renderer, scope):
        """ Do the import. """
        env = self.env

        for (var, expr) in self.assigns:
            name = expr.eval(scope)
            try:
                imp = env.load_import(name)
                scope.set(var, imp)
            except KeyError:
                raise UnknownImportError(
                    "No such import: {0}".format(name),
                    self.template.filename,
                    self.line
                )


class DoNode(Node):
    """ Evaluate expressions and discard the results. """

    def __init__(self, template, line, exprs):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.exprs = exprs

    def render(self, renderer, scope):
        """ Set the value. """
        for expr in self.exprs:
            expr.eval(scope)


class UnsetNode(Node):
    """ Unset variable at the current scope rsults. """

    def __init__(self, template, line, varlist):
        """ Initialize. """
        Node.__init__(self, template, line)
        self.varlist = varlist

    def render(self, renderer, scope):
        """ Set the value. """
        for item in self.varlist:
            scope.unset(item)


class HookNode(Node):
    """ A node to call a registered hook. """

    def __init__(self, template, line, hook, assigns, reverse):
        """ Initialize """
        Node.__init__(self, template, line)
        self.hook = hook
        self.assigns = assigns
        self.reverse = reverse

    def render(self, renderer, scope):
        """ Expand the variables. """

        hook = self.hook.eval(scope)
        params = {}
        for (name, expr) in self.assigns:
            params[name] = expr.eval(scope)

        self.env.call_hook(
            hook,
            self.template,
            self.line,
            renderer,
            scope,
            params,
            self.reverse
        )


class BreakNode(Node):
    """ Return RENDER_BREAK. """

    def render(self, renderer, scope):
        return Node.RENDER_BREAK


class ContinueNode(Node):
    """ Return RENDER_CONTINUE. """

    def render(self, renderer, scope):
        return Node.RENDER_CONTINUE
