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


comment_checks = [re.compile("[^#]*\"{3}|\'{3}"),
                  re.compile("[^\"]*\"[^\"]*\'{3}"),
                  re.compile("[^\']*\'[^\']*\"{3}"),
                  re.compile("[^\"\'#]*(([^\"\'#]*\"[^\"\'#]*#?[^\"\'#]*\")|([^\"\'#]*\'[^\"\'#]*#?[^\"\'#]*\'))*[^\"\'#]*#"),
                  re.compile("\"{3}")]
func_checks = [re.compile(r"[ ]*def [a-zA-Z0-9_]+\(")]
class_checks = [re.compile(r"[ ]*class [a-zA-Z0-9_]+(\([a-zA-Z0-9_\.]*\))?:")]
line_checks = [re.compile(r"[ ]*[a-zA-Z0-9_]+")]

format_checks = [re.compile(r'[\t ]*"""\n([\t ]*[\w., ]+\n)+([\t ]*\n([\t ]*:param \w+:[\t ]+{[\w.]+}([\t ]+[\w., ]+\n)+)+)?([\t ]*\n([\t ]*:return: {[\w.]+}\n)+)?([\t ]*\n([\t ]*:raise [\w.]+:\n)+)?[\t ]*"""\n')]