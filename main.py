import pandas as pd

import parser
import util

if __name__ == "__main__":
    columns = ["path",
               "name",
               "type",
               "start line",
               "end line",
               "inputs",
               # "found inputs",
               # "missing inputs",
               "returns",
               # "found returns",
               "raises",
               # "found raises",
               # "missing raises",
               "parameters",
               # "found parameters",
               # "missing parameters",
               "basic comments",
               "multiline comments",
               "formatted multiline",
               "Documented"]

    regex = {"class": util.process_regex(util.standard_classregex),
             "function": util.process_regex(util.standard_functionregex),
             "method": util.process_regex(util.standard_methodregex)}

    df = pd.DataFrame([], columns=columns)
    text = util.replace_tabs(open("G:/pythonprojects/NEST/LINTWORM/parser.py", "r").read())
    test1 = parser.Parser(text, "G:/pythonprojects/NEST/LINTWORM/parser.py", regex)
    test1.parse()
    test1.parameter_check()
    test1.check()
    df = test1.report(df, columns)
    df.to_csv("G:/pythonprojects/NEST/LINTWORM/Report_1.csv", index=False)

    print("finished 1")

    df = pd.DataFrame([], columns=columns)
    text = util.replace_tabs(open("G:/pythonprojects/NEST/WIZARD/git/commands.py", "r").read())
    test2 = parser.Parser(text, "G:/pythonprojects/NEST/WIZARD/git/commands.py", regex)
    test2.parse()
    test2.parameter_check()
    test2.check()
    df = test2.report(df, columns)
    df.to_csv("G:/pythonprojects/NEST/LINTWORM/Report_2.csv", index=False)

    print("finished 2")