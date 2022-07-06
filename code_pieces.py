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

    def report(self, df, columns):
        return df

    def check_function(self, parameters, returns, raises):
        found_parameters = []
        count_parameters = 0
        found_returns = []
        count_returns = 0
        found_raises = []
        count_raises = 0

        documented = True

        parameter_lines = parser.get_regex_instances(self.text, self.regex["parameter_line"])
        for param in parameter_lines:
            param = self.regex["parameter_start"].sub("", param)
            found_parameters.append(self.regex["parameter_end"].sub("", param))
            count_parameters += 1
            if param in parameters:
                parameters.pop(parameters.index(param))

        documented = documented and len(parameters) == 0

        return_lines = parser.get_regex_instances(self.text, self.regex["return_line"])
        for ret in return_lines:
            ret = self.regex["return_start"].sub("", ret)
            found_returns.append(self.regex["return_end"].sub("", ret))
            count_returns += 1
            if ret in returns:
                returns.pop(returns.index(ret))

        documented = documented and count_returns == len(returns)

        raise_lines = parser.get_regex_instances(self.text, self.regex["raise_line"])
        for r in raise_lines:
            r = self.regex["raise_start"].sub("", r)
            found_raises.append(self.regex["raise_end"].sub("", r))
            count_raises += 1
            if r in raises:
                raises.pop(raises.index(r))

        documented = documented and len(raises) == 0

        return found_parameters, count_returns, found_raises, documented

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

        self.inputs = []
        self.returns = []
        self.raises = []
        self.parameters = []

        self.found_inputs = []
        self.found_returns = 0
        self.found_raises = []
        self.found_parameters = []

        self.defstr = "file"

    def parse(self, i, lines):
        self.start = max(1, i)
        while i < len(lines):
            if parser.comment_check(lines[i][1]):
                if '"""' in lines[i][1]:
                    delimiter = '"'
                else:
                    delimiter = "'"

                if self.defstr == "class":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.classregex, self.defstr))
                elif self.defstr == "function":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.functionregex, self.defstr))
                elif self.defstr == "method":
                    self.content.append(MultiLineComment(lines[i], delimiter, self.methodregex, self.defstr))
                else:
                    self.content.append(MultiLineComment(lines[i], delimiter, parent_type=self.defstr))

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
                i = self.content[-1].parse(i, lines)
            elif parser.func_checks[0].match(lines[i][1]):
                if self.defstr == "class":
                    self.content.append(Method(lines[i][1].split("def ")[1].split("(")[0], lines[i][0], self.path,
                                               self.classregex, self.functionregex, self.methodregex, lines[i][1]))
                    i += 1
                    i = self.content[-1].parse(i, lines)
                else:
                    self.content.append(Function(lines[i][1].split("def ")[1].split("(")[0], lines[i][0], self.path,
                                                 self.classregex, self.functionregex, self.methodregex, lines[i][1]))
                    i += 1
                    i = self.content[-1].parse(i, lines)

            else:
                self.lines.append(lines[i][1])
                i += 1

                if " return " in self.lines[-1]:
                    return_line = self.lines[-1].split(" return ")
                    if not parser.check_in_str(return_line):
                        self.returns.append(str(len(self.lines)))

                if " raise " in self.lines[-1]:
                    raise_line = self.lines[-1].split(" raise ")
                    if not parser.check_in_str(raise_line):
                        self.raises.append(self.lines[-1].split(" raise ")[1].split("(")[0])

                if "self." in self.lines[-1]:
                    param_line = self.lines[-1].split("self.")
                    print(param_line)
        self.end = i
        return i

    def report(self, df, columns):
        data = []
        col = []
        if "path" in columns:
            data.append(self.path)
            col.append("path")
        if "name" in columns:
            data.append(self.name)
            col.append("name")
        if "type" in columns:
            data.append(self.defstr)
            col.append("type")

        if "start line" in columns:
            data.append(self.start + 1)
            col.append("start line")
        if "end line" in columns:
            data.append(self.end + 1)
            col.append("end line")

        if "inputs" in columns:
            data.append(":".join(self.inputs))
            col.append("inputs")
        if "found inputs" in columns:
            data.append(":".join(self.found_inputs))
            col.append("found inputs")
        if "missing inputs" in columns:
            data.append(":".join([i for i in self.inputs if i not in self.found_inputs]))
            col.append("missing inputs")

        if "returns" in columns:
            data.append(len(self.returns))
            col.append("returns")
        if "found returns" in columns:
            data.append(self.found_returns)
            col.append("found returns")

        if "raises" in columns:
            data.append(":".join(self.raises))
            col.append("raises")
        if "found raises" in columns:
            data.append(":".join(self.found_raises))
            col.append("found raises")
        if "missing raises" in columns:
            data.append(":".join([i for i in self.raises if i not in self.found_raises]))
            col.append("missing raises")

        if "parameters" in columns:
            data.append(":".join(self.parameters))
            col.append("parameters")
        if "found parameters" in columns:
            data.append(":".join(self.found_parameters))
            col.append("found parameters")
        if "missing parameters" in columns:
            data.append(":".join([i for i in self.parameters if i not in self.found_parameters]))
            col.append("missing parameters")

        if "basic comments" in columns:
            data.append(self.basic_comments)
            col.append("basic comments")
        if "multiline comments" in columns:
            data.append(self.ml_comment)
            col.append("multiline comments")
        if "formatted multiline" in columns:
            data.append(self.ml_formatted)
            col.append("formatted multiline")
        if "Documented" in columns:
            data.append(self.ml_complete)
            col.append("Documented")
        datapoint = pd.DataFrame([data], columns=col)
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.content:
            df = sub.report(df, columns)

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
        self.defstr = "class"

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

        self.defstr = "function"

    def parse(self, i, lines):
        i = super().parse(i, lines)
        self.check_inputs()
        return i

    def check(self):
        for s in self.content:
            if isinstance(s, MultiLineComment):
                self.basic_comments = True
                self.ml_comment = True
                if self.functionregex["main"].match(s.text):
                    self.ml_formatted = True
                    self.found_inputs, self.found_returns, self.found_raises, self.ml_complete = s.check_function(
                        self.inputs, self.returns, self.raises)
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

        self.defstr = "method"

    def check_inputs(self):
        super().check_inputs()
        if "self" in self.inputs:
            self.inputs.pop(self.inputs.index("self"))
