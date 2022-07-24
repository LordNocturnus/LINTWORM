import pandas as pd
import re

import util


class _Parser(object):

    def __init__(self, text, path, regex, parent=None, indent=0):
        """
            initializes the _Parser class by adding all necessary parameters

        :param text:    {str}       the code which is to be analysed for documentation
        :param path:    {Pathlike}  abspath to file from which the text is taken
        :param regex:   {dict}      dictionary containing dictionaries for each code peace which should be checked
                                    for multiline comment formatting. Currently implemented are functions, methods and
                                    classes.
        :param parent:  {_Parser}   pointer to a _Parser or subclass of _Parser which contains the new instance
        :param indent:  {int}       number of spaces between start of line and first significant char
        """
        self.text = text
        self.path = path
        self.regex = regex
        self.parent = parent
        self.indent = indent

        self.start = None
        self.end = None
        self.endchar = re.compile("[^\w\W]")
        self.offset = 0

        self.subcontent = []

        self.subcontent_classes = [_Bracket,
                                   _StraightBracket,
                                   _CurvedBracket,
                                   _SingleString,
                                   _DoubleString,
                                   _FormattingSingleString,
                                   _FormattingDoubleString,
                                   _SingleMultilineString,
                                   _DoubleMultilineString,
                                   _Comment,
                                   _Function,
                                   _Class,
                                   _Parameter,
                                   _Return,
                                   _Raise,
                                   _Property,
                                   _Argument,
                                   _Yield,
                                   _ClassMethodArgument]

        self.basic_comments = False
        self.ml_comment = False
        self.ml_formatted = False
        self.documented = False

        self.inputs = []
        self.returns = 0
        self.yields = 0
        self.raises = []
        self.parameters = []

        self.found_inputs = []
        self.found_returns = 0
        self.found_yields = 0
        self.found_raises = []
        self.found_parameters = []

        self.defstr = "file"

    @property
    def name(self):
        return ""

    @property
    def ret_offset(self):
        return self.offset

    @property
    def pure_text(self):
        text = self.text
        for s in self.subcontent:
            text = text.replace(s.text, "")
        return text

    def parse(self, start=0):
        self.start = start
        current_indent = self.indent

        if type(self) == _Parser:
            c = 0
        else:
            c = 1

        while c < len(self.text):
            new_sub = None
            for sub in self.subcontent_classes:
                if sub.before.match(self.text[c-1]) and sub.current.match(self.text[c]) and \
                        sub.after.match(self.text[c+1:]):
                    new_sub = sub(self.text[c:], self.path, self.regex, self, current_indent)
                    break
            if new_sub:
                delta = new_sub.parse(start=self.start+c)

                self.subcontent.append(new_sub)
                c += delta
            elif self.endchar.match(self.text[c:]):
                self.text = self.text[:c+self.offset]
                self.end = self.start + len(self.text)
                return c + self.ret_offset
            elif self.text[c] == "\n":
                c += 1
                current_indent = 0
                while c < len(self.text):
                    if self.text[c] == " ":
                        c += 1
                        current_indent += 1
                    else:
                        break
                if current_indent > 0:
                    c -= 1
            else:
                c += 1
        self.end = self.start + len(self.text)
        return c + self.offset

    def check(self):
        sub_ml_comment = []
        sub_ml_formatted = []
        documented = []
        for s in self.subcontent:
            s.check()
            if isinstance(s, _Comment) or s.basic_comments:
                self.basic_comments = True
            if isinstance(s, (_SingleMultilineString, _DoubleMultilineString)):
                self.basic_comments = True
                self.ml_comment = True
                if s.ml_formatted:
                    self.ml_formatted = True
            elif isinstance(s, (_Class, _Function, _Method)):
                sub_ml_comment.append(s.ml_comment)
                sub_ml_formatted.append(s.ml_formatted)
                documented.append(s.documented)
        if all(sub_ml_comment) and not len(sub_ml_comment) == 0 and not isinstance(self, (_Class, _Function, _Method)):
            self.ml_comment = True
        if all(sub_ml_formatted) and not len(sub_ml_formatted) == 0 and not isinstance(self, (_Class, _Function,
                                                                                              _Method)):
            self.ml_formatted = True
        if all(documented) and not len(documented) == 0 and not isinstance(self, (_Class, _Function, _Method)):
            self.documented = True
        if type(self) == _Parser and len(sub_ml_comment) == 0 and len(sub_ml_formatted) == 0 and len(documented) == 0:
            self.basic_comments = True
            self.ml_comment = True
            self.ml_formatted = True
            self.documented = True

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

        if "start char" in columns:
            data.append(self.start + 1)
            col.append("start char")
        if "end char" in columns:
            data.append(self.end + 1)
            col.append("end char")

        if "inputs" in columns:
            data.append(":".join(sorted(self.inputs)))
            col.append("inputs")
        if "found inputs" in columns:
            data.append(":".join(sorted(self.found_inputs)))
            col.append("found inputs")
        if "missing inputs" in columns:
            data.append(":".join(sorted([i for i in self.inputs if i not in self.found_inputs])))
            col.append("missing inputs")

        if "returns" in columns:
            data.append(self.returns)
            col.append("returns")
        if "found returns" in columns:
            data.append(self.found_returns)
            col.append("found returns")

        if "yields" in columns:
            data.append(self.yields)
            col.append("yields")
        if "found yields" in columns:
            data.append(self.found_yields)
            col.append("found yields")

        if "raises" in columns:
            data.append(":".join(sorted(self.raises)))
            col.append("raises")
        if "found raises" in columns:
            data.append(":".join(sorted(self.found_raises)))
            col.append("found raises")
        if "missing raises" in columns:
            data.append(":".join(sorted([i for i in self.raises if i not in self.found_raises])))
            col.append("missing raises")

        if "parameters" in columns:
            data.append(":".join(sorted(self.parameters)))
            col.append("parameters")
        if "found parameters" in columns:
            data.append(":".join(sorted(self.found_parameters)))
            col.append("found parameters")
        if "missing parameters" in columns:
            data.append(":".join(sorted([i for i in self.parameters if i not in self.found_parameters])))
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
        if "documented" in columns:
            data.append(self.documented)
            col.append("documented")
        datapoint = pd.DataFrame([data], columns=col)
        df = pd.concat([df, datapoint], ignore_index=True)

        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
        return ret


class _Bracket(_Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\(")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"\)")
        self.offset = 1

        self.defstr = "bracket"

    def report(self, df, columns):

        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _StraightBracket(_Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\[")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"]")
        self.offset = 1

        self.defstr = "straight bracket"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _CurvedBracket(_Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"{")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"}")
        self.offset = 1

        self.defstr = "curved bracket"

    @property
    def ret_offset(self):
        return 0

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _SingleString(_Parser):

    before = re.compile(r"[^\\'f]")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = []

        self.defstr = "single string"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _DoubleString(_Parser):

    before = re.compile(r'[^\\"f]')
    current = re.compile(r'"')
    after = re.compile(r'[^"]|([^"]{2})')

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = []

        self.defstr = "double string"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _FormattingSingleString(_Parser):

    before = re.compile(r"f")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]

        self.defstr = "formatted single string"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _FormattingDoubleString(_Parser):

    before = re.compile(r"f")
    current = re.compile(r'"')
    after = re.compile(r'[^"]|([^"]{2})')

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]

        self.defstr = "formatted double string"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _SingleMultilineString(_Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"'")
    after = re.compile(r"''")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"[^\\]'''")
        self.offset = 4

        self.subcontent_classes = []
        self.basic_comments = True
        self.ml_comment = True

        self.defstr = "single multiline string"

    def check(self):
        if isinstance(self.parent, _Class):
            regex = self.regex["class"]
        elif isinstance(self.parent, _Function):
            regex = self.regex["function"]
        elif isinstance(self.parent, _Method):
            regex = self.regex["method"]
        else:
            regex = None

        if regex:
            if regex["main"].match(self.text):
                self.ml_formatted = True
                param = util.get_regex_instances(self.text, regex["parameter main"])
                for p in param:
                    p = regex["parameter start"].sub("", p)
                    p = regex["parameter end"].sub("", p)
                    if isinstance(self.parent, _Class):
                        self.parent.found_parameters.append(p)
                    else:
                        self.parent.found_inputs.append(p)
                self.parent.missing_parameters = list(set(self.parent.parameters) - set(self.parent.found_parameters))
                self.parent.missing_inputs = list(set(self.parent.inputs) - set(self.parent.found_inputs))

                ret = util.get_regex_instances(self.text, regex["return main"])
                for r in ret:
                    r = regex["return start"].sub("", r)
                    r = regex["return end"].sub("", r)
                    if r == "":
                        self.parent.found_returns += 1

                yie = util.get_regex_instances(self.text, regex["yield main"])
                for y in yie:
                    y = regex["yield start"].sub("", y)
                    y = regex["yield end"].sub("", y)
                    if y == "":
                        self.parent.found_yields += 1

                rai = util.get_regex_instances(self.text, regex["raise main"])
                for r in rai:
                    r = regex["raise start"].sub("", r)
                    r = regex["raise end"].sub("", r)
                    self.parent.found_raises.append(r)
                self.parent.missing_raises = list(set(self.parent.raises) - set(self.parent.found_raises))

                if len(self.parent.missing_parameters) == 0 and len(self.parent.missing_inputs) == 0 and \
                        len(self.parent.missing_raises) == 0 and self.parent.found_returns - self.parent.returns == 0 \
                        and self.parent.found_yields - self.parent.yields == 0:
                    self.parent.documented = True

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _DoubleMultilineString(_Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r'"')
    after = re.compile(r'""')

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[^\\]"""')
        self.offset = 4

        self.subcontent_classes = []
        self.basic_comments = True
        self.ml_comment = True

        self.defstr = "double multiline string"

    def check(self):
        if isinstance(self.parent, _Class):
            regex = self.regex["class"]
        elif isinstance(self.parent, _Function):
            regex = self.regex["function"]
        elif isinstance(self.parent, _Method):
            regex = self.regex["method"]
        else:
            regex = None

        if regex:
            if regex["main"].match(self.text):
                self.ml_formatted = True
                param = util.get_regex_instances(self.text, regex["parameter main"])
                for p in param:
                    p = regex["parameter start"].sub("", p)
                    p = regex["parameter end"].sub("", p)
                    if isinstance(self.parent, _Class):
                        self.parent.found_parameters.append(p)
                    else:
                        self.parent.found_inputs.append(p)
                self.parent.missing_parameters = list(set(self.parent.parameters) - set(self.parent.found_parameters))
                self.parent.missing_inputs = list(set(self.parent.inputs) - set(self.parent.found_inputs))

                ret = util.get_regex_instances(self.text, regex["return main"])
                for r in ret:
                    r = regex["return start"].sub("", r)
                    r = regex["return end"].sub("", r)
                    if r == "":
                        self.parent.found_returns += 1

                yie = util.get_regex_instances(self.text, regex["yield main"])
                for y in yie:
                    y = regex["yield start"].sub("", y)
                    y = regex["yield end"].sub("", y)
                    if y == "":
                        self.parent.found_yields += 1

                rai = util.get_regex_instances(self.text, regex["raise main"])
                for r in rai:
                    r = regex["raise start"].sub("", r)
                    r = regex["raise end"].sub("", r)
                    self.parent.found_raises.append(r)
                self.parent.missing_raises = list(set(self.parent.raises) - set(self.parent.found_raises))

                if len(self.parent.missing_parameters) == 0 and len(self.parent.missing_inputs) == 0 and \
                        len(self.parent.missing_raises) == 0 and self.parent.found_returns - self.parent.returns == 0 \
                        and self.parent.found_yields - self.parent.yields == 0:
                    self.parent.documented = True

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _Comment(_Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"#")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[^\\]\n')
        self.offset = 2

        self.subcontent_classes = []
        self.basic_comments = True

        self.defstr = "comment"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _Function(_Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"d")
    after = re.compile(r"ef ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0

        self.defstr = "function"

    @property
    def name(self):
        return self.text.split("\n")[0].split("(")[0][4:]

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
            if isinstance(s, _Return):
                self.returns += 1
            elif isinstance(s, _Yield):
                self.yields += 1
            elif isinstance(s, _Raise):
                self.raises.append(s.name)

        for s in self.subcontent:
            if isinstance(s, _Bracket):
                args = []
                self.inputs = s.pure_text[1:-1].split(",")

                for i in range(len(self.inputs)):
                    self.inputs[i] = self.inputs[i].strip().split("=")[0].split(":")[0]
                    if "*" in self.inputs[i]:
                        args.append(self.inputs[i])

                for r in args:
                    print(r)
                    self.inputs.pop(self.inputs.index(r))
                break
        return ret


class _Method(_Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"d")
    after = re.compile(r"ef ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0

        self.defstr = "method"

    @property
    def name(self):
        return self.text.split("\n")[0].split("(")[0][4:]

    @property
    def ret_offset(self):
        return self.offset - 1

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
            if isinstance(s, _Return):
                self.returns += 1
            elif isinstance(s, _Yield):
                self.yields += 1
            elif isinstance(s, _Raise):
                self.raises.append(s.name)

        for s in self.subcontent:
            if isinstance(s, _Bracket):
                args = []
                self.inputs = s.pure_text[1:-1].split(",")

                for i in range(len(self.inputs)):
                    self.inputs[i] = self.inputs[i].strip().split("=")[0].split(":")[0]
                    if "*" in self.inputs[i]:
                        args.append(self.inputs[i])

                for r in args:
                    print(r)
                    self.inputs.pop(self.inputs.index(r))

                if "self" in self.inputs:
                    self.inputs.pop(self.inputs.index("self"))
                break
        return ret


class _ClassMethod(_Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"d")
    after = re.compile(r"ef ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0

        self.defstr = "classmethod"

    @property
    def name(self):
        return self.text.split("\n")[0].split("(")[0][4:]

    @property
    def ret_offset(self):
        return self.offset - 1

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
            if isinstance(s, _Return):
                self.returns += 1
            elif isinstance(s, _Yield):
                self.yields += 1
            elif isinstance(s, _Raise):
                self.raises.append(s.name)

        for s in self.subcontent:
            if isinstance(s, _Bracket):
                args = []
                self.inputs = s.pure_text[1:-1].split(",")

                for i in range(len(self.inputs)):
                    self.inputs[i] = self.inputs[i].strip().split("=")[0].split(":")[0]
                    if "*" in self.inputs[i]:
                        args.append(self.inputs[i])

                for r in args:
                    print(r)
                    self.inputs.pop(self.inputs.index(r))

                if "cls" in self.inputs:
                    self.inputs.pop(self.inputs.index("cls"))
                break
        return ret


class _Class(_Parser):

    before = re.compile(r"\s")
    current = re.compile(r"c")
    after = re.compile(r"lass ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0

        self.subcontent_classes.pop(self.subcontent_classes.index(_Function))
        self.subcontent_classes.append(_Method)
        self.subcontent_classes.append(_ClassParameter)

        self.defstr = "class"

    @property
    def name(self):
        return self.text.split("\n")[0].split(":")[0].split("(")[0][6:]

    def parameter_check(self):
        for s in self.subcontent:
            self.parameters += s.parameter_check()
        self.parameters = list(set(self.parameters))
        return []


class _Parameter(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"s")
    after = re.compile(r"elf\.")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[^\.\w]')
        self.offset = 0

        self.subcontent_classes = []

        self.defstr = "parameter"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    @property
    def name(self):
        return self.text.split(".")[1]

    def parameter_check(self):
        return [self.name]


class _Return(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"r")
    after = re.compile(r"eturn ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[\n#]')
        self.offset = 0

        self.defstr = "return"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _Raise(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"r")
    after = re.compile(r"aise ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[\n#]')
        self.offset = 0

        self.defstr = "raise"

    @property
    def name(self):
        return self.pure_text[6:]

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _Property(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"@")
    after = re.compile(r"property")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^# d]')
        self.offset = 0

        self.subcontent_classes.pop(self.subcontent_classes.index(_Function))
        self.subcontent_classes.append(_Method)

        self.defstr = "property"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    @property
    def name(self):
        for s in self.subcontent:
            if isinstance(s, _Method):
                return s.name

    def parameter_check(self):
        ret = [self.name]
        for s in self.subcontent:
            ret += s.parameter_check()
        return ret


class _ClassMethodArgument(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"@")
    after = re.compile(r"classmethod")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^# d]')
        self.offset = 0

        self.subcontent_classes.pop(self.subcontent_classes.index(_Function))
        self.subcontent_classes.append(_ClassMethod)

        self.defstr = "classmethodargument"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
        return ret


class _ClassParameter(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"\w")
    after = re.compile(r"[\w]*[ ]+=")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'\W')
        self.offset = 0

        self.subcontent_classes = []

        self.defstr = "class parameter"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    @property
    def name(self):
        return self.text

    def parameter_check(self):
        return [self.name]


class _Argument(_Parser):

    before = re.compile(r"[\W\w]")
    current = re.compile(r"\n")
    after = re.compile(r"[ ]*@[^\Wpc]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\n')
        self.offset = 0

        self.defstr = "argument"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    @property
    def name(self):
        return self.text[1:]


class _Yield(_Parser):

    before = re.compile(r"\W")
    current = re.compile(r"y")
    after = re.compile(r"ield ")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r'[\n#]')
        self.offset = 0

        self.defstr = "yield"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df
