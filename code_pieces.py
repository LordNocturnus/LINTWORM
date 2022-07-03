import pandas as pd

import parser


class MultiLineComment(object):
    """
        This class is used to save and progress any multiline comments found in the python code that is parsed.
    """

    def __init__(self, line, delimiter, regex=None, parent_type=None):
        """

        :param line:
        :param delimiter:
        :raise
        """
        self.delimiter = delimiter
        self.lines = [line]
        self.regex = regex
        self.parent_type = parent_type

    def parse(self, i, lines):
        while i < len(lines) and self.delimiter*3 not in lines[i][1]:

            self.lines.append(lines[i])
            i += 1

        self.lines.append(lines[i])
        i += 1
        return i

    def report(self, df):
        return df

    def check_function(self, parameters, returns, raises):
        print()
        print("debug")

    @property
    def text(self):
        return "".join([i[1] for i in self.lines])


class Code(object):

    def __init__(self, name, indent, path, classregex, functionregex, methodregex, line=None):
        self.path = path
        self.name = name
        self.indent = indent
        self.classregex = classregex
        self.functionregex = functionregex
        self.methodregex = methodregex
        if line:
            self.lines = [line]
        else:
            self.lines = []
        self.content = []

        self.basic_comments = False
        self.ml_comment = False
        self.ml_formatted = False
        self.ml_complete = False
        self.start = None
        self.end = None

    def parse(self, i, lines, defstr=None):
        self.start = max(1, i)
        while i < len(lines):
            if parser.comment_check(lines[i][1]):
                if '"""' in lines[i][1]:
                    delimiter = '"'
                else:
                    delimiter = "'"

                if defstr == "class":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.classregex, defstr))
                elif defstr == "function":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.functionregex, defstr))
                elif defstr == "method":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.methodregex, defstr))
                else:
                    self.content.append(MultiLineComment(lines[i], delimiter, parent_type=defstr))

                if len(parser.comment_checks[4].findall(lines[i][1])) > 1:
                    i += 1
                else:
                    i += 1
                    i = self.content[-1].parse(i, lines)
            elif lines[i][0] <= self.indent and parser.line_checks[0].match(lines[i][1]):
                break
            elif parser.class_checks[0].match(lines[i][1]):
                self.content.append(Class(lines[i][1].split(":")[0].split("class ")[1].split("(")[0], lines[i][0],
                                          self.path, self.classregex, self.functionregex, self.methodregex,
                                          lines[i][1]))
                i += 1
                i = self.content[-1].parse(i, lines, "class")
            elif parser.func_checks[0].match(lines[i][1]):
                if defstr == "class":
                    self.content.append(Method(lines[i][1].split("def ")[1].split("(")[0], lines[i][0], self.path,
                                               self.classregex, self.functionregex, self.methodregex, lines[i][1]))
                    i += 1
                    i = self.content[-1].parse(i, lines, "method")
                else:
                    self.content.append(Function(lines[i][1].split("def ")[1].split("(")[0], lines[i][0], self.path,
                                                 self.classregex, self.functionregex, self.methodregex, lines[i][1]))
                    i += 1
                    i = self.content[-1].parse(i, lines, "function")

            else:
                self.lines.append(lines[i][1])
                i += 1
        self.end = i
        return i

    def report(self, df):
        datapoint = pd.DataFrame([[self.path, self.name, "file", self.start + 1, self.end + 1, None, None, None,
                                   self.basic_comments, self.ml_comment, self.ml_formatted, self.ml_complete]],
                                 columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                          "raises", "basic comments", "multiline comments", "formatted multiline",
                                          "Documented"])
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.content:
            df = sub.report(df)

        return df

    def check(self):
        for s in self.content:
            if isinstance(s, MultiLineComment):
                self.basic_comments = True
                self.ml_comment = True
            else:
                s.check()

        for line in self.lines:
            if "#" in line:
                str_flag = False
                for c in range(len(line)):
                    if line[c] == "#" and not str_flag:
                        self.basic_comments = True
                        break
                    elif line[c] == "'" and not str_flag:
                        str_flag = "'"
                    elif line[c] == '"' and not str_flag:
                        str_flag = '"'
                    elif line[c] == str_flag and not line[max(0, c - 1)] == "\\":
                        str_flag = False
                break

    @property
    def text(self):
        return "".join(self.lines)


class Class(Code):

    def __init__(self, name, indent, path, classregex, functionregex, methodregex, line):
        super().__init__(name, indent, path, classregex, functionregex, methodregex, line)

    def report(self, df):
        datapoint = pd.DataFrame([[self.path, self.name, "class", self.start + 1, self.end + 1, None, None, None,
                                   self.basic_comments, self.ml_comment, self.ml_formatted, self.ml_complete]],
                                 columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                          "raises", "basic comments", "multiline comments", "formatted multiline",
                                          "Documented"])
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.content:
            df = sub.report(df)

        return df

    def check(self):
        for s in self.content:
            if isinstance(s, MultiLineComment):
                self.basic_comments = True
                self.ml_comment = True
            else:
                s.check()


class Function(Code):

    def __init__(self, name, indent, path, classregex, functionregex, methodregex, line):
        super().__init__(name, indent, path, classregex, functionregex, methodregex, line)
        self.inputs = []
        self.returns = []
        self.raises = []

    def parse(self, i, lines, defstr=None):
        i = super().parse(i, lines, defstr)
        self.check_inputs()
        for line in range(len(self.lines)):
            if " return " in self.lines[line]:
                return_line = self.lines[line].split(" return ")
                in_str = False
                for c in range(len(return_line[0])):
                    if in_str:
                        if return_line[0][c] == in_str and not return_line[0][c - 1] == "\\":
                            in_str = False
                    elif return_line[0][c] == '"' and not return_line[0][c - 1] == "\\":
                        in_str = '"'
                    elif return_line[0][c] == "'" and not return_line[0][c - 1] == "\\":
                        in_str = "'"
                if not in_str:
                    self.returns.append(str(line))
            if " raise " in self.lines[line]:
                return_line = self.lines[line].split(" raise ")
                in_str = False
                for c in range(len(return_line[0])):
                    if in_str:
                        if return_line[0][c] == in_str and not return_line[0][c - 1] == "\\":
                            in_str = False
                    elif return_line[0][c] == '"' and not return_line[0][c - 1] == "\\":
                        in_str = '"'
                    elif return_line[0][c] == "'" and not return_line[0][c - 1] == "\\":
                        in_str = "'"
                if not in_str:
                    self.raises.append(str(line))
        return i

    def report(self, df):
        datapoint = pd.DataFrame([[self.path, self.name, "function", self.start + 1, self.end + 1,
                                   ":".join(self.inputs), len(self.returns), len(self.raises), self.basic_comments,
                                   self.ml_comment, self.ml_formatted, self.ml_complete]],
                                 columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                          "raises", "basic comments", "multiline comments", "formatted multiline",
                                          "Documented"])
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.content:
            df = sub.report(df)

        return df

    def check(self):
        for s in self.content:
            if isinstance(s, MultiLineComment):
                self.basic_comments = True
                self.ml_comment = True
                if self.functionregex["main"].fullmatch(s.text):
                    self.ml_formatted = True
                    s.check_function(self.inputs, self.returns, self.raises)
            else:
                s.check()

    def check_inputs(self):
        for c in range(len(self.lines[0])):
            if self.lines[0][c] == "(":
                input_str = self.lines[0][c+1:-1].split("#")[0]
                break

        c = 0
        lines = 1
        normal_brackets = 1
        dict_brackets = 0
        list_brackets = 0
        in_str = False
        cut = False

        while c < len(input_str):
            if in_str:
                if input_str[c] == in_str and not input_str[c-1] == "\\":
                    in_str = False
            elif input_str[c] == '"' and not input_str[c-1] == "\\":
                in_str = '"'
            elif input_str[c] == "'" and not input_str[c-1] == "\\":
                in_str = "'"
            elif cut and input_str[c] == "," and normal_brackets == 1 and dict_brackets == 0 and list_brackets == 0:
                input_str = input_str[:cut] + input_str[c:]
                c = cut - 1
                cut = False
            elif input_str[c] == "=" and not input_str[c - 1] == "\\":
                cut = c
            elif input_str[c] == "(":
                normal_brackets += 1
            elif input_str[c] == "[":
                dict_brackets += 1
            elif input_str[c] == "{":
                list_brackets += 1
            elif input_str[c] == ")":
                normal_brackets -= 1
            elif input_str[c] == "]":
                dict_brackets -= 1
            elif input_str[c] == "}":
                list_brackets -= 1
            if normal_brackets == 0:
                if cut:
                    input_str = input_str[:cut]
                else:
                    input_str = input_str[:c]
                break
            c += 1
            if c == len(input_str) and normal_brackets >= 1:
                input_str = input_str.rstrip() + " " + self.lines[lines][:-1].lstrip().split("#")[0]
                lines += 1

        self.inputs = input_str.split(", ")


class Method(Function):

    def __init__(self, name, indent, path, classregex, functionregex, methodregex, line):
        super().__init__(name, indent, path, classregex, functionregex, methodregex, line)

    def report(self, df):
        datapoint = pd.DataFrame([[self.path, self.name, "method", self.start + 1, self.end + 1, ":".join(self.inputs),
                                   len(self.returns), len(self.raises),  self.basic_comments, self.ml_comment,
                                   self.ml_formatted, self.ml_complete]],
                                 columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                          "raises", "basic comments", "multiline comments", "formatted multiline",
                                          "Documented"])
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.content:
            df = sub.report(df)

        return df
