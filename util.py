import re
import fnmatch


class PathFilter(object):

    def __init__(self, wants, ignores):
        self.wants = wants
        self.ignores = ignores
        self.files = []
        self.folders = []


def replace_tabs(string):
    """
        This function replaces all tabs in a string with the number of spaces that result in a string with the same
        indentation and length

        :param
            string {str}    -- string potentially containing tabs to be replaced with spaces
        :return
            {str}           -- string with all tabs replaced by spaces
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
