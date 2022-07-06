import re


def replace_tabs(string):
    """
        This function replaces all tabs in a string with the number of spaces that result in a string with the same
        indentation and length

        :param
            string {str}    -- string potentially containing tabs to be replaced with spaces
        :return
            {str}           -- string with all tabs replaced by spaces
    """
    new_str = string.split("\t")
    for i in range(0, len(new_str) - 1):
        new_str[i] += " " * (4 - len(new_str[i]) % 4)
    new_str = "".join(new_str)
    return new_str


def comment_check(line):
    """
    Checks if the line is the start of a Multiline comment

    :param
        line {str}  -- line to be checked for Multiline comment start
    :return
        {bool}      -- True if line contains the start of a Multiline comment
    """
    if '"""' in line or "'''" in line:
        if comment_checks[0].match(line):
            if not comment_checks[1].match(line) and not comment_checks[2].match(line):
                return True
    return False


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
        text = regex.sub("", text, 1)
    return ret


def check_in_str(line):
    in_str = False
    for c in range(len(line[0])):
        if in_str:
            if line[0][c] == in_str and not line[0][c - 1] == "\\":
                in_str = False
        elif line[0][c] == '"' and not line[0][c - 1] == "\\":
            in_str = '"'
        elif line[0][c] == "'" and not line[0][c - 1] == "\\":
            in_str = "'"
        elif line[0][c] == "#":
            in_str = True
            break

    if not in_str:
        return False
    return True


def get_parameters(line):
    pass


comment_checks = [re.compile("[^#]*\"{3}|\'{3}"),
                  re.compile("[^\"]*\"[^\"]*\'{3}"),
                  re.compile("[^\']*\'[^\']*\"{3}"),
                  re.compile("[^\"\'#]*(([^\"\'#]*\"[^\"\'#]*#?[^\"\'#]*\")|([^\"\'#]*\'[^\"\'#]*#?[^\"\'#]*\'))*[^\"\'#]*#"),
                  re.compile("\"{3}")]
func_checks = [re.compile(r"[ ]*def [a-zA-Z0-9_]+\(")]
class_checks = [re.compile(r"[ ]*class [a-zA-Z0-9_]+(\([a-zA-Z0-9_\.]*\))?:")]
line_checks = [re.compile(r"[ ]*[a-zA-Z0-9_]+")]

standard_classregex = {"main": None,
                       "parameter_start": r"[\s]*:param ",
                       "parameter_end": r":[\s]+{[\w.]+}([\s]+[^:\n]+\n)*[\s]+[^:\n]+",
                       "return_start": None,
                       "return_end": None,
                       "raise_start": None,
                       "raise_end": None}

standard_functionregex = {"main": re.compile(r'[\s]*"""\n([\s]+[^{}]+\n)+(([\s]*:param [\w]+:[\s]+{[\w.]+}([\s]+[^:\n]+\n)+)+\n)?(([\s]*:return:[\s]+{[\w.]+}([\s]+[^:\n]+\n)+)+\n)?([\s]*:raise:[\s]+[\w.]+[\s]*\n)*[\s]*"""\n'),
                          "parameter_start": r"[\s]*:param ",
                          "parameter_end": r":[\s]+{[\w.]+}([\s]+[^:\n]+\n)*[\s]+[^:\n]+",
                          "return_start": r"[\s]*:return:",
                          "return_end": r"[\s]+{[\w.]+}([\s]+[^:\n]+\n)+",
                          "raise_start": r"[\s]*:raise:[\s]+",
                          "raise_end": r"[\s]*\n"}

standard_methodregex = {"main": re.compile(r'[\s]*"""\n([\s]+[^{}]+\n)+(([\s]*:param [\w]+:[\s]+{[\w.]+}([\s]+[^:\n]+\n)+)+\n)?(([\s]*:return:[\s]+{[\w.]+}([\s]+[^:\n]+\n)+)+\n)?([\s]*:raise:[\s]+[\w.]+[\s]*\n)*[\s]*"""\n'),
                        "parameter_start": r"[\s]*:param ",
                        "parameter_end": r":[\s]+{[\w.]+}([\s]+[^:\n]+\n)*[\s]+[^:\n]+",
                        "return_start": r"[\s]*:return:",
                        "return_end": r"[\s]+{[\w.]+}([\s]+[^:\n]+\n)+",
                        "raise_start": r"[\s]*:raise:[\s]+",
                          "raise_end": r"[\s]*\n"}

