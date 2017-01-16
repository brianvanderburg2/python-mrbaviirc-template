""" Unit tests for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


import os
import json
import glob

import unittest


from .. import FileSystemLoader, Environment, StdLib, StringRenderer


DATADIR = os.path.join(os.path.dirname(__file__), "template_data")


class TemplateTest(unittest.TestCase):

    def setUp(self):
        loader = FileSystemLoader(DATADIR)
        self._env = Environment({"lib": StdLib() }, loader=loader)

    def tearDown(self):
        self._env = None

    def test_compare(self):
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


def suite():
    return unittest.makeSuite(TemplateTest)


