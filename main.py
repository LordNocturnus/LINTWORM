from datetime import datetime
import pandas as pd
import os

import parser
import util


def lintworm(path, report_path=os.getcwd(), report_name=None, classregex=util.standard_classregex,
             functionregex=util.standard_functionregex, methodregex=util.standard_methodregex,
             columns=util.standard_columns):

    regex = {"class": util.process_regex(classregex),
             "function": util.process_regex(functionregex),
             "method": util.process_regex(methodregex)}

    if not report_name:
        report_name = "LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"

    report_path = str(os.path.join(os.path.abspath(report_path), os.path.normpath(report_name)))
    columns.append("basic comments")
    columns.append("multiline comments")
    columns.append("formatted multiline")
    columns.append("documented")

    paths = []
    if os.path.isfile(path):
        if path[-3:] == ".py":
            paths.append(path)
    else:
        for p, subdirs, files in os.walk(path):
            for name in files:
                if name[-3:] == ".py":
                    paths.append(os.path.join(p, name))

    for p in paths:
        try:
            text = open(p, "r").read()
            if "\t" in text:
                text = util.replace_tabs(text)

            code = parser._Parser(text, p, regex)

            code.parse()
            code.parameter_check()
            code.check()

        except UnicodeDecodeError:
            code = parser._Parser("", p, regex)

        try:
            df = pd.read_csv(report_path)
        except OSError:
            df = pd.DataFrame([], columns=columns)

        df = code.report(df, columns)
        df.to_csv(report_path, index=False)

        print("finished:", p)

    try:
        return pd.read_csv(report_path)
    except OSError:
        return pd.DataFrame([], columns=columns)


if __name__ == "__main__":
    test = lintworm("G:/pythonprojects/NEST/test")