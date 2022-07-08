import re

import parser
import util

if __name__ == "__main__":

    text = util.replace_tabs(open("G:/pythonprojects/NEST/LINTWORM/parser.py", "r").read())
    test = parser.Parser(text)
    _ = test.parse()
    print("finished")
