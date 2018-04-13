""" pytest-capable tests for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016-2018"
__license__     = "Apache License 2.0"


import os
import json
import glob

from ...template import UnrestrictedLoader, SearchPathLoader, Environment, StdLib, StringRenderer
from ...template import PrefixLoader, PrefixPathLoader

DATADIR = os.path.join(os.path.dirname(__file__), "template_data")


def test_compare_unrestricted_loader():
    loader = UnrestrictedLoader()
    env = Environment({"lib": StdLib() }, loader=loader)
    env.enable_code()

    do_test_compare(env, False)

def test_compare_search_path_loader():
    loader = SearchPathLoader(DATADIR)
    env = Environment({"lib": StdLib() }, loader=loader)
    env.enable_code()

    do_test_compare(env, True)

def test_compare_prefix_loader():
    loader = PrefixLoader()
    loader.add_prefix("", PrefixPathLoader(DATADIR))

    env = Environment({"lib": StdLib() }, loader=loader)
    env.enable_code()

    do_test_compare(env, True)

def do_test_compare(env, search_path_loader):
    """ Run tests by applying template to input and comparing output. """

    with open(os.path.join(DATADIR, "data.json"), "rU") as handle:
        data = json.load(handle)

    for path in sorted(glob.glob(os.path.join(DATADIR, "*.tmpl"))):
        source = path if not search_path_loader else os.path.basename(path)

        tmpl = env.load_file(filename=source)
        rndr = StringRenderer()
        tmpl.render(rndr, data)

        target = path[:-5] + ".txt"
        contents = rndr.get()

        with open(target, "rU") as handle:
            target_contents = handle.read()

        assert contents == target_contents
        #self.assertEqual(
        #    contents,
        #    target_contents,
        #    "render compare failed: {0}".format(os.path.basename(path))
        #)

        sections = rndr.get_sections()
        for section in sections:
            target = path[:-5] + "_" + section + ".txt"
            contents = rndr.get_section(section)

            with open(target, "rU") as handle:
                target_contents = handle.read()

            assert contents == target_contents
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
    env = Environment({"lib": StdLib()}, loader=loader)


    with open(os.path.join(DATADIR, "data.json"), "rU") as handle:
        data = json.load(handle)

    tmpl = env.load_file("/main.tmpl")
    rndr = StringRenderer()
    tmpl.render(rndr, data)

    contents = rndr.get()

    with open(target, "rU") as handle:
        target_contents = handle.read()

    assert contents == target_contents
    #self.assertEqual(
    #    contents,
    #    target_contents,
    #    "render compare failed during search path test"
    #)



