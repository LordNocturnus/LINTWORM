import re

import util


class Parser(object):

    def __init__(self, text, parent=None, indent=0):
        self.text = text
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
                                   _Parameter]


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
                    new_sub = sub(self.text[c:], self, current_indent)
                    break
            if new_sub:
                delta = new_sub.parse(start=c)

                self.subcontent.append(new_sub)
                c += delta
            elif self.endchar.match(self.text[c:]):
                self.text = self.text[:c+self.offset]
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
        return c + self.offset

    def check(self):



class _Bracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\(")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"\)")
        self.offset = 1


class _StraightBracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\[")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"]")
        self.offset = 1


class _CurvedBracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"{")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"}")
        self.offset = 1


class _SingleString(Parser):

    before = re.compile(r"[^\\'f]")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = []


class _DoubleString(Parser):

    before = re.compile(r"[^\\\"f]")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = []


class _FormattingSingleString(Parser):

    before = re.compile(r"f")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]


class _FormattingDoubleString(Parser):

    before = re.compile(r"f")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]


class _SingleMultilineString(Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"'")
    after = re.compile(r"''")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r"[^\\]'''")
        self.offset = 4

        self.subcontent_classes = []


class _DoubleMultilineString(Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"\"")
    after = re.compile(r"\"\"")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'[^\\]"""')
        self.offset = 4

        self.subcontent_classes = []


class _Comment(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"#")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'[^\\]\n')
        self.offset = 2

        self.subcontent_classes = []


class _Function(Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"d")
    after = re.compile(r"ef ")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0


class _Method(Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"d")
    after = re.compile(r"ef ")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0


class _Class(Parser):

    before = re.compile(r"[\n ]")
    current = re.compile(r"c")
    after = re.compile(r"lass ")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(f'\\n[ ]{"{0," + str(self.indent) + "}"}[^\n# ]')
        self.offset = 0

        self.subcontent_classes.pop(self.subcontent_classes.index(_Function))
        self.subcontent_classes.append(_Method)


class _Parameter(Parser):

    before = re.compile(r"\W")
    current = re.compile(r"s")
    after = re.compile(r"elf.")

    def __init__(self, text, parent=None, indent=0):
        super().__init__(text, parent, indent)

        self.endchar = re.compile(r'\W')
        self.offset = 0

        self.subcontent_classes = []
