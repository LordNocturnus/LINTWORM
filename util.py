import re
import os
import fnmatch


class PathFilter(object):

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
                print(line)
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
        for sub_path in os.scandir(os.path.normpath(path)):
            if not self.match(sub_path):
                if sub_path.is_dir() and sub_path not in self.folders:
                    self.folders.append(sub_path)
                    self.walk_dir(sub_path)
                elif not sub_path.is_dir():
                    self.files.append(sub_path)
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


standard_classregex = {"main": r'[ ]*"""\n([ ]*[^\n]+\n)+(\n([ ]*:param [\w]+:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:return:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:yield:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:raise:[ ]+[\w.]+[ ]*\n)+)?[ ]*"""',
                       "parameter start": r"[ ]*:param ",
                       "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                       "return start": r"[ ]*:return:",
                       "return end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                       "yield start": r"[ ]*:return:",
                       "yield end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                       "raise start": r"[ ]*:raise:[ ]+",
                       "raise end": r"[\s]*\n"}

standard_functionregex = {"main": r'[ ]*"""\n([ ]*[^\n]+\n)+(\n([ ]*:param [\w]+:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:return:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:yield:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:raise:[ ]+[\w.]+[ ]*\n)+)?[ ]*"""',
                          "parameter start": r"[ ]*:param ",
                          "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                          "return start": r"[ ]*:return:",
                          "return end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                          "yield start": r"[ ]*:yield:",
                          "yield end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                          "raise start": r"[ ]*:raise:[ ]+",
                          "raise end": r"[\s]*\n"}

standard_methodregex = {"main": r'[ ]*"""\n([ ]*[^\n]+\n)+(\n([ ]*:param [\w]+:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:return:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:yield:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:raise:[ ]+[\w.]+[ ]*\n)+)?[ ]*"""',
                        "parameter start": r"[ ]*:param ",
                        "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                        "return start": r"[ ]*:return:",
                        "return end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                        "yield start": r"[ ]*:yield:",
                        "yield end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                        "raise start": r"[ ]*:raise:[ ]+",
                        "raise end": r"[ ]*\n"}

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
                    ]
