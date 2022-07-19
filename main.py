from datetime import datetime
import pandas as pd
import os

import parser
import util


def lintworm(path, report_path=os.getcwd(), report_name=None, classregex=util.standard_classregex,
             functionregex=util.standard_functionregex, methodregex=util.standard_methodregex,
             columns=util.standard_columns, hash_path=None, level="documented", filter=None):

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

    df = pd.DataFrame([], columns=columns)

    if hash_path:
        try:
            hash_df = pd.read_csv(hash_path)
        except OSError:
            hash_df = pd.DataFrame([], columns=["path", "hashed", "basic comments", "multiline comments",
                                                "formatted multiline", "documented", "hash"])

    if isinstance(filter, os.PathLike) or type(filter) == str:
        filter = util.PathFilter.from_file(filter)
    elif type(filter) == list or type(filter) == tuple:
        filter = util.PathFilter(filter)
    else:
        filter = util.PathFilter([])

    paths = []
    if os.path.isfile(path):
        if path[-3:] == ".py" and not filter.match(path):
            paths.append(os.path.normpath(path))
    else:
        paths = filter.walk_dir(path)

    for p in paths:
        if not p.name[-3:] == ".py":
            continue
        hashed = False
        try:
            valid = True
            text = open(p.path, "r").read()
            if hash_path:
                hashed, in_df, text_hash = util.check_hash(text, hash_df, p.path, level)
        except UnicodeDecodeError:
            valid = False

        if valid and hashed:
            code = parser._Parser("", p.path, regex)
            code.basic_comments = hash_df["basic comments"][hash_df["path"] == p.path].iloc[0]
            code.ml_comment = hash_df["multiline comments"][hash_df["path"] == p.path].iloc[0]
            code.ml_formatted = hash_df["formatted multiline"][hash_df["path"] == p.path].iloc[0]
            code.documented = hash_df["documented"][hash_df["path"] == p.path].iloc[0]
        elif valid:
            if "\t" in text:
                text = util.replace_tabs(text)

            code = parser._Parser(text, p.path, regex)

            code.parse()
            code.parameter_check()
            code.check()
        else:
            code = parser._Parser("", p.path, regex)

        df = code.report(pd.DataFrame([], columns=columns), columns)
        if hash_path:
            if not in_df:
                print("hashing", p.path)
                new_hash = pd.DataFrame([[p.path, True, code.basic_comments, code.ml_comment, code.ml_formatted,
                                          code.documented, text_hash]], columns=["path", "hashed", "basic comments",
                                                                                 "multiline comments",
                                                                                 "formatted multiline", "documented",
                                                                                 "hash"])
                hash_df = pd.concat([hash_df, new_hash], ignore_index=True)
            else:
                index = hash_df["basic comments"][hash_df["path"] == p.path].index[0]
                hash_df.at[index, "basic comments"] = code.basic_comments
                hash_df.at[index, "multiline comments"] = code.ml_comment
                hash_df.at[index, "formatted multiline"] = code.ml_formatted
                hash_df.at[index, "documented"] = code.documented
                hash_df.at[index, "hash"] = text_hash

        try:
            df = pd.concat([pd.read_csv(report_path), df], ignore_index=True)
        except OSError:
            pass
        df.to_csv(report_path, index=False)

        print("finished:", p.path)
    hash_df.to_csv(hash_path, index=False)
    return df


def check_integrity(path, hash_path):
    """
        checks if any python files in path have changed compared to when the hash file was last run over the files in
        path

    :param path:        {Pathlike}  path in which to check all python files in
    :param hash_path:   {Pathlike}  path to a lintworm created hash file which is used to compare hashes

    :return:            {Bool, str} found a file with a changed hash, path to edited file
    :return:            {Bool, str} all files have the same hash values as in the hash file
    """

    hash_df = pd.read_csv(hash_path)

    paths = []
    if os.path.isfile(path):
        if path[-3:] == ".py":
            paths.append(os.path.normpath(path))
    else:
        for p, subdirs, files in os.walk(path):
            for name in files:
                if name[-3:] == ".py":
                    paths.append(os.path.normpath(os.path.join(p, name)))

    for p in paths:
        try:
            text = open(p, "r").read()
            valid, _, _ = util.check_hash(text, hash_df, p, "hashed")
        except UnicodeDecodeError:
            valid = False
        if not valid:
            return False, p

    return True, ""


if __name__ == "__main__":
    test = lintworm("G:/pythonprojects/NEST/LINTWORM", filter=["*\\parser.py", "*\\.git", "*\\.idea"])

    test2 = lintworm("G:/pythonprojects/NEST/LINTWORM", hash_path="G:/pythonprojects/NEST/LINTWORM/hash.csv")
    temp = check_integrity("G:/pythonprojects/NEST/LINTWORM/parser.py", "G:/pythonprojects/NEST/LINTWORM/hash.csv")
