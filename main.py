from datetime import datetime
import pandas as pd
import os
import pathlib

import parser
import util


def lintworm(path, report_path=os.getcwd(), report_name=None, classregex=util.standard_classregex,
             functionregex=util.standard_functionregex, methodregex=util.standard_methodregex,
             columns=util.standard_columns, hash_path=None, level="documented", file_filter=None,
             class_attribute=False):
    """
        main function of lintwork. It checks all python files in the given folder for a certain level of documentation

    :param path:            {Pathlike}      path in which lintworm should check all python files
    :param report_path:     {Pathlike}      path to which to save the lintworm report to
    :param report_name:     {str}           name of the report file if not given will use LintwormReport_HH_MM_SS.csv
                                            format
    :param classregex:      {dict}          dictionary containing strings that are then compiled into regex checks that
                                            are used for checking documentation of classes. needs to contain strings at
                                            keys "main", "parameter start", "parameter end", "return start",
                                            "return end", "raise start", "raise end" "yield start" and "yield end"
    :param functionregex:   {dict}          dictionary containing strings that are then compiled into regex checks that
                                            are used for checking documentation of classes. needs to contain strings at
                                            keys "main", "parameter start", "parameter end", "return start",
                                            "return end", "raise start", "raise end" "yield start" and "yield end"
    :param methodregex:     {dict}          dictionary containing strings that are then compiled into regex checks that
                                            are used for checking documentation of classes. needs to contain strings at
                                            keys "main", "parameter start", "parameter end", "return start",
                                            "return end", "raise start", "raise end" "yield start" and "yield end"
    :param columns:         {list}          contains strings indicating which columns to add to the report. Can contain
                                            any combination of
                                            "path"               -> path to the python file in which the entry was found
                                            "name"               -> name of the entry (class name, function name etc.)
                                            "type"               -> type of the entry (file, class, function etc.)
                                            "start char"         -> index of the starting character of the entry
                                            "end char"           -> index of the last character of the entry
                                            "inputs"             -> inputs of a function or method
                                            "found inputs"       -> inputs that where found in the docstring of an entry
                                            "missing inputs"     -> inputs that are missing in the docstring of an entry
                                            "returns"            -> number of returns in a function, method or class
                                            "found returns"      -> number of returns found in the docstring of an entry
                                            "yields"             -> number of yields in a function method or class
                                            "found yields"       -> number of yields found in the docstring of an entry
                                            "raises"             -> all errors the entry can raise
                                            "found raises"       -> all errors found in the docstring of an entry
                                            "missing raises"     -> all errors missing in the docstring of an entry
                                            "parameters"         -> parameters of a class
                                            "found parameters"   -> parameters found in the docstring of a class
                                            "missing parameters" -> parameters missing in the docstring of a class
                                            "basic comments"     -> an entry has any comments
                                            "multiline comments" -> an entry contains a multiline string
                                            "formatted multiline"-> an entry has a formatted docstring
                                            "documented"         -> an entries docstring contains everything necessary
    :param hash_path:       {Pathlike}      path to save/load a hash file to/from. hashing can decrease runtime by
                                            checking if a file has been changed since the creation of the hash file and
                                            only running the parser if file has changed
    :param level:           {str}           level of documentation below which an unchanged hash is ignored and parser
                                            is run anyways choice between
                                            "hashed"                -> parser is only run over files with changed hash
                                            "basic comments"        -> parser is run over files without comments
                                            "multiline comments"    -> parser is run over files without docstrings
                                            "formatted multiline"   -> parser is run over files without formatted
                                                                       docstrings
                                            "documented"            -> parser is run over files with incomplete
                                                                       docstrings
    :param file_filter:     {Pathlike,list} list containing strings following the glob format path to a file
                                            following the .gitignore format
    :param class_attribute: {bool}          if true include class attributes in the docstring of classes

    :return:                {DataFrame}     pandas dataframe identical to the generated lintworm report
    """

    # process regex
    regex = {"class": util.process_regex(classregex),
             "function": util.process_regex(functionregex),
             "method": util.process_regex(methodregex)}

    # prepare for report
    if not report_name:
        report_name = "LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"

    report_path = str(os.path.join(os.path.abspath(report_path), os.path.normpath(report_name)))
    if "basic comments" not in columns:  # basic comments column is always in the report
        columns.append("basic comments")
    if "multiline comments" not in columns:  # multiline comments column is always in the report
        columns.append("multiline comments")
    if "formatted multiline" not in columns:  # formatted multiline column is always in the report
        columns.append("formatted multiline")
    if "documented" not in columns:  # documented column is always in the report
        columns.append("documented")

    df = pd.DataFrame([], columns=columns)

    # prepare hashing if a hashpath is given
    if hash_path:
        try:
            hash_df = pd.read_csv(hash_path)
        except OSError:
            hash_df = pd.DataFrame([], columns=["path", "hashed", "basic comments", "multiline comments",
                                                "formatted multiline", "documented", "hash"])

    # prepare a PathFilter class and collect all paths
    if isinstance(file_filter, os.PathLike) or type(file_filter) == str:
        file_filter = util.PathFilter.from_file(file_filter)
    elif type(file_filter) == list or type(file_filter) == tuple:
        file_filter = util.PathFilter(file_filter)
    else:
        file_filter = util.PathFilter([])

    paths = []
    if os.path.isfile(path):
        if path[-3:] == ".py" and not file_filter.match(path):
            paths.append(pathlib.Path(path))
    else:
        paths = file_filter.walk_dir(path)

    # itterate through all files and check them if they are a .py file
    for p in paths:
        if not p.name[-3:] == ".py":
            continue
        hashed = False
        try:
            valid = True
            text = open(p, "r").read()
            if hash_path:
                hashed, in_df, text_hash = util.check_hash(text, hash_df, p, level)
        except UnicodeDecodeError:  # someone fucked up
            valid = False

        if valid and hashed:
            code = parser._Parser("", p, regex, class_attribute=class_attribute)
            code.basic_comments = hash_df["basic comments"][hash_df["path"] == str(p)].iloc[0]
            code.ml_comment = hash_df["multiline comments"][hash_df["path"] == str(p)].iloc[0]
            code.ml_formatted = hash_df["formatted multiline"][hash_df["path"] == str(p)].iloc[0]
            code.documented = hash_df["documented"][hash_df["path"] == str(p)].iloc[0]
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
                new_hash = pd.DataFrame([[p, True, code.basic_comments, code.ml_comment, code.ml_formatted,
                                          code.documented, text_hash]], columns=["path", "hashed", "basic comments",
                                                                                 "multiline comments",
                                                                                 "formatted multiline", "documented",
                                                                                 "hash"])
                hash_df = pd.concat([hash_df, new_hash], ignore_index=True)
            else:
                index = hash_df["basic comments"][hash_df["path"] == str(p)].index[0]
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

    if hash_path:
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
    test = lintworm("G:/pythonprojects/NEST/LINTWORM", hash_path="G:/pythonprojects/NEST/LINTWORM/hash.csv",
                    file_filter=["*\\.git", "*\\.idea"])
