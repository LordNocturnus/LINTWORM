import re

import parser


if __name__ == "__main__":

    text = open("G:/pythonprojects/NEST/WIZARD/git/commands.py", "r").read()
    test = parser.Parser(text)
    test.parse()
    print("finished")
