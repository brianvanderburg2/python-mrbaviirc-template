""" Provide a simple command line input and test for the template engine. """

__author__      = "Brian Allen Vanderburg II"
__copyright__   = "Copyright 2016"
__license__     = "Apache License 2.0"


from . import *


if __name__ == "__main__":
    try:
        import sys
        import argparse
        
        import json

        parser = argparse.ArgumentParser(description="Template Test")
        parser.add_argument("-c", dest="count", default=1, help="Render the template this many times")
        parser.add_argument("-p", dest="show", default=None, action="store_true", help="Print compiled templates.")
        parser.add_argument("template", help="Location of the template")
        parser.add_argument("data", nargs="?", help="Location of the data json")

        args = parser.parse_args()

        filters = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "equal": lambda x, y: x == y,
            "odd": lambda x: x % 2 == 1,
            "even": lambda x: x % 2 == 0,
            "mod": lambda x, y: x % y
        }

        e = Environment(filters)
        t = e.load_file(args.template)

        if args.show:
            for t in e._cache:
                print("Template: {0}".format(t))
                print("========================================")
                print(e._cache[t]._code)
                print("")
        else:
            data = json.loads(open(args.data, "rU").read())
            o = StreamRenderer(sys.stdout)

            for i in range(int(args.count)):
                data["cycle"] = i + 1
                t.render(o, data)
    except Error as e:
        print("{0}: {1}".format(type(e).__name__, e.message))

        




