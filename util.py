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
    new_lines = []
    for line in string.split("\n"):
        new_str = line.split("\t")
        for i in range(0, len(new_str) - 1):
            new_str[i] += " " * (4 - len(new_str[i]) % 4)
        new_lines.append("".join(new_str))
    return "\n".join(new_lines)


def process_regex(regex):
    ret = dict()

    try:
        ret["main"] = re.compile(regex["main"])
    except TypeError:
        ret["main"] = None

    try:
        ret["parameter main"] = re.compile(regex["parameter start"] + r"[\w]+" + regex["parameter end"])
        ret["parameter start"] = re.compile(regex["parameter start"])
        ret["parameter end"] = re.compile(regex["parameter end"])
    except TypeError:
        ret["parameter main"] = None
        ret["parameter start"] = None
        ret["parameter end"] = None

    try:
        ret["return main"] = re.compile(regex["return start"] + regex["return end"])
        ret["return start"] = re.compile(regex["return start"])
        ret["return end"] = re.compile(regex["return end"])
    except TypeError:
        ret["return main"] = None
        ret["return start"] = None
        ret["return end"] = None

    try:
        ret["raise main"] = re.compile(regex["raise start"] + r"[\w.]+" + regex["raise end"])
        ret["raise start"] = re.compile(regex["raise start"])
        ret["raise end"] = re.compile(regex["raise end"])
    except TypeError:
        ret["raise main"] = None
        ret["raise start"] = None
        ret["raise end"] = None

    return ret


standard_classregex = {"main": None,
                       "parameter start": r"[ ]*:param ",
                       "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                       "return start": None,
                       "return end": None,
                       "raise start": None,
                       "raise end": None}

standard_functionregex = {"main": r'[ ]*"""\n([ ]*[^\n]+\n)+(\n([ ]*:param [\w]+:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:return:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:raise:[ ]+[\w.]+[ ]*\n)+)?[ ]*"""',
                          "parameter start": r"[ ]*:param ",
                          "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                          "return start": r"[ ]*:return:",
                          "return end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                          "raise start": r"[ ]*:raise:[ ]+",
                          "raise end": r"[\s]*\n"}

standard_methodregex = {"main": r'[ ]*"""\n([ ]*[^\n]+\n)+(\n([ ]*:param [\w]+:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:return:[ ]+{[\w.]+}([ ]+[^:\n]+\n)+)+)?(\n([ ]*:raise:[ ]+[\w.]+[ ]*\n)+)?[ ]*"""',
                        "parameter start": r"[ ]*:param ",
                        "parameter end": r":[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                        "return start": r"[ ]*:return:",
                        "return end": r"[ ]+{[\w.]+}([ ]+[^:\n]+\n)+",
                        "raise start": r"[ ]*:raise:[ ]+",
                        "raise end": r"[ ]*\n"}