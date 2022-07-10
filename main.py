from datetime import datetime
import pandas as pd
import os

import parser
import util


def lintworm(path, report_path=os.getcwd(), report_name=None, classregex=util.standard_classregex,
             functionregex=util.standard_functionregex, methodregex=util.standard_methodregex,
             columns=util.standard_columns, hash_path=None, level="documented"):

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

    df = pd.DataFrame([], columns=columns)

    if hash_path:
        try:
            hash_df = pd.read_csv(hash_path)
        except OSError:
            hash_df = pd.DataFrame([], columns=["path", "basic comments", "multiline comments", "formatted multiline",
                                                "documented", "hash"])

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
        hashed = False
        try:
            valid = True
            text = open(p, "r").read()
            if hash_path:
                hashed, in_df, text_hash = util.check_hash(text, hash_df, p, level)
        except UnicodeDecodeError:
            valid = False

        if valid and hashed:
            code = parser._Parser("", p, regex)
            code.basic_comments = hash_df["basic comments"][hash_df["path"] == p].iloc[0]
            code.ml_comment = hash_df["multiline comments"][hash_df["path"] == p].iloc[0]
            code.ml_formatted = hash_df["formatted multiline"][hash_df["path"] == p].iloc[0]
            code.documented = hash_df["documented"][hash_df["path"] == p].iloc[0]
        elif valid:
            if "\t" in text:
                text = util.replace_tabs(text)

            code = parser._Parser(text, p, regex)

            code.parse()
            code.parameter_check()
            code.check()
        else:
            code = parser._Parser("", p, regex)

        df = code.report(pd.DataFrame([], columns=columns), columns)
        if hash_path:
            if not in_df:
                print("hashing", p)
                new_hash = pd.DataFrame([[p, code.basic_comments, code.ml_comment, code.ml_formatted, code.documented,
                                          text_hash]], columns=["path", "basic comments", "multiline comments",
                                                                "formatted multiline", "documented", "hash"])
                hash_df = pd.concat([hash_df, new_hash], ignore_index=True)
            else:
                hash_df["basic comments"][hash_df["path"] == p].loc[0] = code.basic_comments
                hash_df["multiline comments"][hash_df["path"] == p].loc[0] = code.ml_comment
                hash_df["formatted multiline"][hash_df["path"] == p].loc[0] = code.ml_formatted
                hash_df["documented"][hash_df["path"] == p].loc[0] = code.documented
                hash_df["hash"][hash_df["path"] == p].loc[0] = text_hash

        try:
            df = pd.concat([pd.read_csv(report_path), df], ignore_index=True)
        except OSError:
            pass
        df.to_csv(report_path, index=False)

        print("finished:", p)
    hash_df.to_csv(hash_path, index=False)
    return df


if __name__ == "__main__":
    test = lintworm("G:/pythonprojects/NEST/WIZARD", hash_path="G:/pythonprojects/NEST/LINTWORM/hash.csv")
