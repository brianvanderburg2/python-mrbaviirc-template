""" pytest-capable tests for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2018"
__license__     = "Apache License 2.0"


import os
import json
import glob

import pytest

from mrbaviirc.template import UnrestrictedLoader, Environment, StdLib, StringRenderer
from mrbaviirc.template import PrefixLoader, PrefixPathLoader, SearchPathLoader
from mrbaviirc.template import AbortError

def hook1a(env, template, line, renderer, scope, params):
    renderer.render("Hook1 A: {0}\n".format(line))

def hook1b(env, template, line, renderer, scope, params):
    renderer.render("Hook1 B: {0}\n".format(line))
    if "count" in params:
        renderer.render("Count: {0}\n".format(params["count"]))

    u1 = scope.userdata["user1"]
    u2 = scope.userdata["user2"]
    if u1 is not None:
        renderer.render("User1: {0}\n".format(u1))
    if u2 is not None:
        renderer.render("User2: {0}\n".format(u2))

def register_hooks(env):
    env.register_hook("hook1", hook1a)
    env.register_hook("hook1", hook1b)

DATADIR = os.path.join(os.path.dirname(__file__), "template_data")

def test_compare_unrestricted_loader():
    loader = UnrestrictedLoader()
    env = Environment(loader=loader, allow_code=True)
    register_hooks(env)

    do_test_compare(env, False)


def test_compare_search_path_loader():
    loader = SearchPathLoader(DATADIR)
    env = Environment(loader=loader, allow_code=True)
    register_hooks(env)

    do_test_compare(env, True)


def test_compare_prefix_loader():
    loader = PrefixLoader()
    loader.add_prefix("", PrefixPathLoader(DATADIR, allow_code=True))

    env = Environment(loader=loader)
    register_hooks(env)
    env.allow_code()

    do_test_compare(env, True)

def test_abort_fn():
    loader = PrefixLoader()
    loader.add_prefix("", PrefixPathLoader(DATADIR, allow_code=True))

    env = Environment(loader=loader)

    template = env.load_file("comment_1.tmpl")
    rndr = StringRenderer()

    def abort_fn1():
        return True

    def abort_fn2():
        return False

    with pytest.raises(AbortError):
        template.render(rndr, None, None, abort_fn1)

    template.render(rndr, None, None, abort_fn2)

def do_test_compare(env, search_path_loader):
    """ Run tests by applying template to input and comparing output. """

    with open(os.path.join(DATADIR, "data.json"), "r", newline=None) as handle:
        data = json.load(handle)

    data["lib"] = StdLib()
    userdata = {"user1": 10, "user2": 20}

    for path in sorted(glob.glob(os.path.join(DATADIR, "*.tmpl"))):
        source = path if not search_path_loader else os.path.basename(path)

        tmpl = env.load_file(filename=source)
        rndr = StringRenderer()
        tmpl.render(rndr, data, userdata)

        target = path[:-5] + ".txt"
        contents = rndr.get()

        with open(target, "r", newline=None) as handle:
            target_contents = handle.read()

        assert contents == target_contents, "Mismatch in file " +  target
        #self.assertEqual(
        #    contents,
        #    target_contents,
        #    "render compare failed: {0}".format(os.path.basename(path))
        #)

        sections = rndr.get_sections()
        for section in sections:
            target = path[:-5] + "_" + section + ".txt"
            contents = rndr.get_section(section)

            with open(target, "r", newline=None) as handle:
                target_contents = handle.read()

            assert contents == target_contents, "Mismatch in file " + target
            #self.assertEqual(
            #    contents,
            #    target_contents,
            #    "render comapre failed: {0}:{1}".format(
            #        os.path.basename(path),
            #        section
            #))


def test_search_path():
    """ Test the search path loader. """
    paths = [
        os.path.join(DATADIR, "searchpath/1"),
        os.path.join(DATADIR, "searchpath/2"),
        os.path.join(DATADIR, "searchpath/3")
    ]
    loader = SearchPathLoader(paths)

    return do_test_search_path(loader)


def test_prefix_path():
    """ Test the prefix loader. """
    paths = [
        os.path.join(DATADIR, "searchpath/1"),
        os.path.join(DATADIR, "searchpath/2"),
        os.path.join(DATADIR, "searchpath/3")
    ]
    loader = PrefixLoader()

    for path in paths:
        loader.add_prefix("", PrefixPathLoader(path))

    return do_test_search_path(loader)


def do_test_search_path(loader):
    """ Test the search path loader. """
    target = os.path.join(DATADIR, "searchpath/output.txt")
    env = Environment(loader=loader)


    with open(os.path.join(DATADIR, "data.json"), "r", newline=None) as handle:
        data = json.load(handle)

    data["lib"] = StdLib()

    tmpl = env.load_file("/main.tmpl")
    rndr = StringRenderer()
    tmpl.render(rndr, data)

    contents = rndr.get()

    with open(target, "r", newline=None) as handle:
        target_contents = handle.read()

    assert contents == target_contents


def test_load_text():
    """ Test the search path loader. """
    paths = [
        os.path.join(DATADIR, "searchpath/1"),
        os.path.join(DATADIR, "searchpath/2"),
        os.path.join(DATADIR, "searchpath/3")
    ]
    loader = SearchPathLoader(paths)

    target = os.path.join(DATADIR, "loadtext/output.txt")
    env = Environment(loader=loader)

    with open(os.path.join(DATADIR, "data.json"), "r", newline=None) as handle:
        data = json.load(handle)

    with open(os.path.join(DATADIR, "loadtext/main.tmpl"), "r", newline=None) as handle:
        text = handle.read()

    data["lib"] = StdLib()

    tmpl = env.load_text(text, "loadtext/main.tmpl")
    rndr = StringRenderer()
    tmpl.render(rndr, data)

    contents = rndr.get()

    with open(target, "r", newline=None) as handle:
        target_contents = handle.read()

    assert contents == target_contents

