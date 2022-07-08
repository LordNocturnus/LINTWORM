import pandas as pd
import re
import copy

import util


class Parser(object):

    def __init__(self, text, path, regex, parent=None, indent=0):
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
                                   _Property]

        self.basic_comments = False
        self.ml_comment = False
        self.ml_formatted = False
        self.ml_complete = False

        self.inputs = []
        self.returns = 0
        self.raises = []
        self.parameters = []

        self.found_inputs = []
        self.found_returns = 0
        self.found_raises = []
        self.found_parameters = []

        self.defstr = "file"

    @property
    def name(self):
        return ""

    @property
    def pure_text(self):
        text = copy.deepcopy(self.text)
        for s in self.subcontent:
            text = text.replace(s.text, "")
        return text

    def parse(self, start=0):
        self.start = start
        current_indent = self.indent

        if type(self) == Parser:
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
                return c + self.offset
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
        if all(sub_ml_comment):
            self.ml_comment = True
        if all(sub_ml_formatted):
            self.ml_formatted = True

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
            data.append(self.returns)
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

        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
        return ret


class _Bracket(Parser):

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


class _StraightBracket(Parser):

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


class _CurvedBracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"{")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(r"}")
        self.offset = 1

        self.defstr = "curved bracket"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _SingleString(Parser):

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


class _DoubleString(Parser):

    before = re.compile(r"[^\\\"f]")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

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


class _FormattingSingleString(Parser):

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


class _FormattingDoubleString(Parser):

    before = re.compile(r"f")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

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


class _SingleMultilineString(Parser):

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
            pass
        elif isinstance(self.parent, _Function):
            if self.regex["function"]["main"].match(self.text):
                self.ml_formatted = True
        elif isinstance(self.parent, _Method):
            if self.regex["method"]["main"].match(self.text):
                self.ml_formatted = True


class _DoubleMultilineString(Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"\"")
    after = re.compile(r"\"\"")

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
            pass
        elif isinstance(self.parent, _Function):
            if self.regex["function"]["main"].match(self.text):
                self.ml_formatted = True
        elif isinstance(self.parent, _Method):
            if self.regex["method"]["main"].match(self.text):
                self.ml_formatted = True


class _Comment(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"#")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'[^\\]\n')
        self.offset = 2

        self.subcontent_classes = []
        self.basic_comments = True

        self.defstr = "comment"

    def report(self, df, columns):
        for sub in self.subcontent:
            df = sub.report(df, columns)

        return df


class _Function(Parser):

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
            elif isinstance(s, _Raise):
                self.raises.append(s.name)

        for s in self.subcontent:
            if isinstance(s, _Bracket):
                inputs = s.pure_text[1:-1].split(",")

                for i in range(len(inputs)):
                    inputs[i] = inputs[i].strip().split("=")[0]
                self.inputs = inputs
                break
        return ret


class _Method(Parser):

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

    def parameter_check(self):
        ret = []
        for s in self.subcontent:
            ret += s.parameter_check()
            if isinstance(s, _Return):
                self.returns += 1
            elif isinstance(s, _Raise):
                self.raises.append(s.name)

        for s in self.subcontent:
            if isinstance(s, _Bracket):
                inputs = s.pure_text[1:-1].split(",")

                for i in range(len(inputs)):
                    inputs[i] = inputs[i].strip().split("=")[0]

                if "self" in inputs:
                    inputs.pop(inputs.index("self"))
                self.inputs = inputs
                break
        return ret


class _Class(Parser):

    before = re.compile(r"[\n ]")
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


class _Parameter(Parser):

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


class _Return(Parser):

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


class _Raise(Parser):

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


class _Property(Parser):

    before = re.compile(r"\W")
    current = re.compile(r"@")
    after = re.compile(r"property")

    def __init__(self, text, path, regex, parent=None, indent=0):
        super().__init__(text, path, regex, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# d]')
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
            if isinstance(s, (_Method, _Function)):
                return s.name

    def parameter_check(self):
        ret = [self.name]
        for s in self.subcontent:
            ret += s.parameter_check()
        return ret


class _ClassParameter(Parser):

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
