from datetime import datetime
import pandas as pd
import os
import re
import copy

from code_pieces import Code
import parser


def simple_start(path, report_path=None, classregex=parser.standard_classregex, functionregex=parser.standard_functionregex,
                 methodregex=parser.standard_methodregex, columns=tuple()):
    if report_path:
        report_path = report_path + "/LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"

    classregex = copy.deepcopy(classregex)
    functionregex = copy.deepcopy(functionregex)
    methodregex = copy.deepcopy(methodregex)

    classregex["parameter_line"] = re.compile(classregex["parameter_start"] + r"[\w]+" +
                                              classregex["parameter_end"])
    classregex["parameter_start"] = re.compile(classregex["parameter_start"])
    classregex["parameter_end"] = re.compile(classregex["parameter_end"])

    functionregex["parameter_line"] = re.compile(functionregex["parameter_start"] + r"[\w]+" +
                                                 functionregex["parameter_end"])
    functionregex["parameter_start"] = re.compile(functionregex["parameter_start"])
    functionregex["parameter_end"] = re.compile(functionregex["parameter_end"])
    functionregex["return_line"] = re.compile(functionregex["return_start"] + functionregex["return_end"])
    functionregex["return_start"] = re.compile(functionregex["return_start"])
    functionregex["return_end"] = re.compile(functionregex["return_end"])
    functionregex["raise_line"] = re.compile(functionregex["raise_start"] + r"[\w.]+" +
                                             functionregex["raise_end"])
    functionregex["raise_start"] = re.compile(functionregex["raise_start"])
    functionregex["raise_end"] = re.compile(functionregex["raise_end"])

    methodregex["parameter_line"] = re.compile(methodregex["parameter_start"] + r"[\w]+" +
                                               methodregex["parameter_end"])
    methodregex["parameter_start"] = re.compile(methodregex["parameter_start"])
    methodregex["parameter_end"] = re.compile(methodregex["parameter_end"])
    methodregex["return_line"] = re.compile(methodregex["return_start"] + methodregex["return_end"])
    methodregex["return_start"] = re.compile(methodregex["return_start"])
    methodregex["return_end"] = re.compile(methodregex["return_end"])
    methodregex["raise_line"] = re.compile(methodregex["raise_start"] + r"[\w.]+" +
                                           methodregex["raise_end"])
    methodregex["raise_start"] = re.compile(methodregex["raise_start"])
    methodregex["raise_end"] = re.compile(methodregex["raise_end"])

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
        if report_path:
            try:
                df = pd.read_csv(report_path)
            except OSError:
                df = pd.DataFrame([], columns=columns)
            df = code.report(df, columns)
            df.to_csv(report_path, index=False)
        print(f"finished file {p}")


if __name__ == "__main__":
    columns = ["path",
               "name",
               "type",
               "start line",
               "end line",
               #"inputs",
               #"found inputs",
               "missing inputs",
               "returns",
               "found returns",
               #"raises",
               #"found raises",
               "missing raises",
               "parameters",
               "found parameters"
               "basic comments",
               "multiline comments",
               "formatted multiline",
               "Documented"]
    simple_start(path="G:/pythonprojects/NEST/WIZARD", report_path="G:/pythonprojects/NEST/LINTWORM", columns=columns)
    print("finished")
