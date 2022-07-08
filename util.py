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
