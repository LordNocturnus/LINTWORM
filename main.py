from datetime import datetime
import pandas as pd
import os

import parser
import util


def lintworm(path, report_path=os.getcwd(), report_name=None, classregex=util.standard_classregex,
             functionregex=util.standard_functionregex, methodregex=util.standard_methodregex,
             columns=util.standard_columns, filter=None):

    regex = {"class": util.process_regex(classregex),
             "function": util.process_regex(functionregex),
             "method": util.process_regex(methodregex)}

    if not report_name:
        report_name = "LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"

    report_path = str(os.path.join(os.path.abspath(report_path), os.path.normpath(report_name)))
    columns.append("basic comments")
    columns.append("multiline comments")
    columns.append("formatted multiline")
    columns.append("Documented")

    if isinstance(filter, os.PathLike) or type(filter) == str:
        filter = util.PathFilter.from_file(filter)
    elif type(filter) == list or type(filter) == tuple:
        filter = util.PathFilter(filter)
    else:
        filter = util.PathFilter([])

    paths = []
    if os.path.isfile(path):
        if path[-3:] == ".py" and not filter.match(path):
            paths.append(path)
    else:
        paths = filter.walk_dir(path)

    for p in paths:
        if not p.name[-3:] == ".py":
            continue
        try:
            text = open(p.path, "r").read()
            if "\t" in text:
                text = util.replace_tabs(text)

            code = parser._Parser(text, p.path, regex)

            code.parse()
            code.parameter_check()
            code.check()

        except UnicodeDecodeError:
            code = parser._Parser("", p.path, regex)

        try:
            df = pd.read_csv(report_path)
        except OSError:
            df = pd.DataFrame([], columns=columns)

        df = code.report(df, columns)
        df.to_csv(report_path, index=False)

        print("finished:", p.path)

    try:
        return pd.read_csv(report_path)
    except OSError:
        return pd.DataFrame([], columns=columns)


if __name__ == "__main__":
    test = lintworm("G:/pythonprojects/NEST/LINTWORM", filter=["*\\parser.py", "*\\.git", "*\\.idea"])
