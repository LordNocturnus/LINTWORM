from datetime import datetime
import pandas as pd
import os

from code_pieces import Code
import parser


def simple_start(path, report=None, classregex=parser.standard_classregex, functionregex=parser.standard_functionregex,
                 methodregex=parser.standard_methodregex):
    if report:
        report = report + "/LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"
    paths = []
    for path, subdirs, files in os.walk(path):
        for name in files:
            if name[-3:] == ".py":
                paths.append(os.path.join(path, name))

    for p in paths:
        f = open(p, "r").readlines()
        lines = []
        for line in f:
            if "\t" in line:
                line = parser.replace_tabs(line)
            lines.append([len(line) - len(line.lstrip(' ')), line])

        code = Code("__main__", -1, p, classregex=classregex, functionregex=functionregex, methodregex=methodregex)
        code.parse(0, lines)
        code.check()
        if report:
            try:
                df = pd.read_csv(report)
            except OSError:
                df = pd.DataFrame([], columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                               "raises", "basic comments", "multiline comments", "formatted multiline",
                                               "Documented"])
            df = code.report(df)
            df.to_csv(report, index=False)


def analyse_file(path, classregex, functionregex, methodregex, report=None):
    f = open(path, "r").readlines()
    data = [0, 0]
    lines = []
    for line in f:
        if "\t" in line:
            line = parser.replace_tabs(line)
        lines.append([len(line) - len(line.lstrip(' ')), line])

    code = Code("__main__", -1, path, classregex=classregex, functionregex=functionregex, methodregex=methodregex)
    code.parse(0, lines)
    code.check()
    if report:
        try:
            df = pd.read_csv(report)
        except OSError:
            df = pd.DataFrame([], columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                           "raises", "basic comments", "multiline comments", "formatted multiline",
                                           "Documented"])
        df = code.report(df)
        df.to_csv(report, index=False)
    #print(f"finished file {path}")

    return data


if __name__ == "__main__":
    #window_start(path="G:/pythonprojects/NEST/LINTWORM", graph="percent", report=True)
    simple_start(path="G:/pythonprojects/NEST/WIZARD", report="G:/pythonprojects/NEST/LINTWORM")
