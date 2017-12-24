""" Unit tests for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os
import json
import glob

import unittest


from ..template import UnrestrictedLoader, SearchPathLoader, Environment, StdLib, StringRenderer


DATADIR = os.path.join(os.path.dirname(__file__), "template_data")


class TemplateTest(unittest.TestCase):

    def setUp(self):
        loader = UnrestrictedLoader()
        self._env = Environment({"lib": StdLib() }, loader=loader)
        self._env.enable_code()

        loader = SearchPathLoader(DATADIR)
        self._env2 = Environment({"lib": StdLib() }, loader=loader)
        self._env2.enable_code()

    def tearDown(self):
        self._env = None
        self._env2 = None

    def test_compare(self):
        self.do_test_compare(self._env)
        self.do_test_compare(self._env2)

    def do_test_compare(self, env):
        """ Run tests by applying template to input and comparing output. """

        with open(os.path.join(DATADIR, "data.json"), "rU") as handle:
            data = json.load(handle)

        for path in sorted(glob.glob(os.path.join(DATADIR, "*.tmpl"))):
            source = path

            tmpl = self._env.load_file(filename=source)
            rndr = StringRenderer()
            tmpl.render(rndr, data)

            target = source[:-5] + ".txt"
            contents = rndr.get()

            with open(target, "rU") as handle:
                target_contents = handle.read()

            self.assertEqual(
                contents,
                target_contents,
                "render compare failed: {0}".format(os.path.basename(path))
            )

            sections = rndr.get_sections()
            for section in sections:
                target = source[:-5] + "_" + section + ".txt"
                contents = rndr.get_section(section)

                with open(target, "rU") as handle:
                    target_contents = handle.read()

                self.assertEqual(
                    contents,
                    target_contents,
                    "render comapre failed: {0}:{1}".format(
                        os.path.basename(path),
                        section
                ))

    def test_search_path(self):
        """ Test the search path loader. """
        paths = [
            os.path.join(DATADIR, "searchpath/1"),
            os.path.join(DATADIR, "searchpath/2"),
            os.path.join(DATADIR, "searchpath/3")
        ]

        target = os.path.join(DATADIR, "searchpath/output.txt")
        
        loader=SearchPathLoader(paths)
        env = Environment({"lib": StdLib()}, loader=loader)


        with open(os.path.join(DATADIR, "data.json"), "rU") as handle:
            data = json.load(handle)

        tmpl = env.load_file("/main.tmpl")
        rndr = StringRenderer()
        tmpl.render(rndr, data)

        contents = rndr.get()

        with open(target, "rU") as handle:
            target_contents = handle.read()

        self.assertEqual(
            contents,
            target_contents,
            "render compare failed during search path test"
        )


def suite():
    return unittest.makeSuite(TemplateTest)


