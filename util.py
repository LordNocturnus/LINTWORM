import numpy as np
import re
import hashlib
import os
import fnmatch
import pathlib


class PathFilter(object):
    """
        Class used for filterd recursive walks through directories to collect and return all files that have a path that
        does not match any of the patterns given to the class instance

    :param patterns:    {list}  contains the file patterns that are to be used for filtering paths
    :param folders:     {list}  contains the absolute paths of all folders visited by the recursive walk_dir method to
                                prevent infinite recursion in case of circular symlinks
    :param files:       {list}  all files that do not match any patterns given to the PathFilter instance
    """

    def __init__(self, patterns):
        """
            initialize teh PathFileter class

        :param patterns:    {List}  List containing glob compatible patterns that are used for path filtering
        """
        self.patterns = patterns
        self.folders = []
        self.files = []

    @classmethod
    def from_file(cls, path):
        """
            load all patterns from a file that follows the glob formatting for filters and uses "#" for comments

        :param path:    {PathLike}      path to the file to load

        :return:        {PathFilter}    new instance of the PathFilter class using all patterns found path
        """
        f = open(path, "r").readlines()
        patterns = []
        for line in f:
            line = line[:-1]
            line = line.split("#")[0]
            if re.search(r"\W", line):
                patterns.append(line)
        return cls(patterns)

    def match(self, path):
        """
            checks if the given path matches any of the patterns of the filter

        :param path:    {PathLike}  path to check for matches with filters

        :return:        {bool}      path matches a pattern of this filter
        :return:        {bool}      path does not match any of the patterns
        """
        for p in self.patterns:
            if fnmatch.fnmatch(path, p):
                return True
        return False

    def walk_dir(self, path):
        """
            recursively walks through the dir and all sub dirs that do not match any of the patterns of this filter
            adding all folders to the folder parameter is done to prevent infinite depth recursion on circular symlinks

        :param path:    {PathLike}  path to walk through

        :return:        {list}      list of paths to all files that do not match any patterns
        """
        path = os.path.realpath(path)
        self.folders.append(path)
        with os.scandir(os.path.normpath(path)) as it:
            for sub_path in it:
                if not self.match(sub_path) and os.path.realpath(sub_path.path) not in self.folders:
                    if sub_path.is_dir():
                        self.walk_dir(sub_path)
                    elif not sub_path.is_dir():
                        self.files.append(pathlib.Path(sub_path))
        return self.files


def replace_tabs(string):
    """
        This function replaces all tabs in a string with the number of spaces that result in a string with the same
        indentation and length

    :param string:  {str}   string potentially containing tabs to be replaced with spaces

    :return:        {str}   string with all tabs replaced by spaces
    """
    new_lines = []
    for line in string.split("\n"):
        new_str = line.split("\t")
        for i in range(0, len(new_str) - 1):
            new_str[i] += " " * (4 - len(new_str[i]) % 4)
        new_lines.append("".join(new_str))
    return "\n".join(new_lines)


def process_regex(regex):
    """
        compiles the strings in the regex dict into regex instances and adds the parameter main, return main, yield main
        and raise main

    :param regex:   {dict}  dictionary containing regex compatible strings which are to be compiled into regex
                            instances.
                            Should contain,
                                main,               string to match a complete multiline string to the given format
                                parameter start,    beginning of a parameter definition should stop right before the
                                                    parameter name
                                parameter end,      end of a parameter definition should start right after the parameter
                                                    name and not overlap into the next parameter/return/yield/raise
                                return start,       beginning of a return definition should stop somewhere in the return
                                                    definition
                                return end,         end of a return definition should start right after the return start
                                                    and not overlap into the next parameter/return/yield/raise
                                yield start,        beginning of a yield definition should stop somewhere in the yield
                                                    definition
                                yield end,          end of a yield definition should start right after the yield start
                                                    and not overlap into the next parameter/return/yield/raise
                                raise start,        beginning of a raise definition should stop right before the
                                                    raise type
                                raise end,          end of a raise definition should start right after the raise
                                                    type and not overlap into the next parameter/return/yield/raise

    :return:        {dict}  dictionary with all necessary regex instances for a single type of multiline comment that is
                            to be matched in LINTWORM
    """
    ret = dict()

    ret["main"] = re.compile(regex["main"])

    ret["parameter main"] = re.compile(regex["parameter start"] + r"[\w]+" + regex["parameter end"])
    ret["parameter start"] = re.compile(regex["parameter start"])
    ret["parameter end"] = re.compile(regex["parameter end"])

    ret["return main"] = re.compile(regex["return start"] + regex["return end"])
    ret["return start"] = re.compile(regex["return start"])
    ret["return end"] = re.compile(regex["return end"])

    ret["yield main"] = re.compile(regex["yield start"] + regex["yield end"])
    ret["yield start"] = re.compile(regex["yield start"])
    ret["yield end"] = re.compile(regex["yield end"])

    ret["raise main"] = re.compile(regex["raise start"] + r"[\w.]+" + regex["raise end"])
    ret["raise start"] = re.compile(regex["raise start"])
    ret["raise end"] = re.compile(regex["raise end"])

    return ret


def get_regex_instances(text, regex):
    """
        a function to get a list of all matches of the given regex in text

    :param text:    {str}           text to be checked for occurrences of the regex pattern
    :param regex:   {re.Pattern}    regex pattern to search for in text

    :return:        {list}          list of all occurrences of the regex pattern in text
    """
    ret = []

    while True:
        new_match = regex.search(text)
        if not new_match:
            break
        ret.append(new_match.group(0))
        text = text.split(ret[-1])[1]
    return ret


def check_hash(text, df, path, level="documented"):
    """
        checks if path is in df, if the sha256 has of text in df is identical and if the text passed LINTWORM above
        level for the given hash.

    :param text:    {str}               text (meaning python code) obtained from file path
    :param df:      {pandas.Dataframe}  a Dataframe obtained from a LINTWORM generated hash file. Can be an empty
                                        Dataframe when running LINTWORM for the first time over a new hash file
    :param path:    {Pathlike}          path to the python file which is being checked for hash
    :param level:   {str}               documentation level text should at least have for the hash. valid are
                                        "basic comments", "multiline comments", "multiline formatted" and "documented"
                                        in increasing order of level

    :return:        {bool, bool, str}   hashes are identical and path is documented to at least level,
                                        path is in df aka the file has been hashed in the past,
                                        sha256 hash of text
    :return:        {bool, bool, str}   hashes are not identical or path is not documented to at least level,
                                        path is in df aka the file has been hashed in the past,
                                        sha256 hash of text
    :return:        {bool, bool, str}   not checked,
                                        path is not in df aka the file is new,
                                        sha256 hash of text
    """
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    if str(path) in np.asarray(df["path"]):
        if np.asarray(df["hash"][df["path"] == str(path)])[0] == text_hash:
            if np.asarray(df[level][df["path"] == str(path)])[0]:
                return True, True, text_hash
        return False, True, text_hash
    return False, False, text_hash


standard_classregex = {"main": r'[ ]*"""\n([ ]*[^\n:]+\n)+([ ]*\n([ ]*:param [\w\d_]+:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:return:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:yield:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:raise:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?[ ]*"""',
                       "parameter start": r"[ ]*:param ",
                       "parameter end": r":[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                       "return start": r"[ ]*:return:",
                       "return end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                       "yield start": r"[ ]*:return:",
                       "yield end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                       "raise start": r"[ ]*:raise:[ ]+",
                       "raise end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+"}

standard_functionregex = {"main": r'[ ]*"""\n([ ]*[^\n:]+\n)+([ ]*\n([ ]*:param [\w\d_]+:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:return:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:yield:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:raise:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?[ ]*"""',
                          "parameter start": r"[ ]*:param ",
                          "parameter end": r":[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                          "return start": r"[ ]*:return:",
                          "return end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                          "yield start": r"[ ]*:yield:",
                          "yield end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                          "raise start": r"[ ]*:raise:[ ]+",
                          "raise end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+"}

standard_methodregex = {"main": r'[ ]*"""\n([ ]*[^\n:]+\n)+([ ]*\n([ ]*:param [\w\d_]+:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:return:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:yield:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?([ ]*\n([ ]*:raise:[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+)+)?[ ]*"""',
                        "parameter start": r"[ ]*:param ",
                        "parameter end": r":[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                        "return start": r"[ ]*:return:",
                        "return end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                        "yield start": r"[ ]*:yield:",
                        "yield end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+",
                        "raise start": r"[ ]*:raise:[ ]+",
                        "raise end": r"[ ]+{[^\n:]+}([ ]+[^\n:]+\n)+"}

standard_columns = ["path",
                    "name",
                    "type",
                    # "start char",
                    # "end char",
                    # "inputs",
                    # "found inputs",
                    "missing inputs",
                    "returns",
                    "found returns",
                    "yields",
                    "found yields",
                    # "raises",
                    # "found raises",
                    "missing raises",
                    # "parameters",
                    # "found parameters",
                    "missing parameters",
                    "basic comments",
                    "multiline comments",
                    "formatted multiline",
                    "documented",
                    ]
