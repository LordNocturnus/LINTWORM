import re

import code_pieces


class Parser(object):

    def __init__(self, text, parent=None):
        self.text = text
        self.parent = parent

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
                                   _Comment]

    def parse(self, start=0):
        self.start = start
        if type(self) == Parser:
            c = 0
        else:
            c = 1
        while c < len(self.text):
            new_sub = None
            for sub in self.subcontent_classes:
                if sub.before.match(self.text[c-1]) and sub.current.match(self.text[c]) and \
                        sub.after.match(self.text[c+1:]):
                    new_sub = sub(self.text[c:], self)
                    break
            if new_sub:
                delta = new_sub.parse(start=c)
                self.subcontent.append(new_sub)
                c += delta
            elif self.endchar.match(self.text[c:]):
                self.text = self.text[:c+self.offset]
                return c + self.offset
            else:
                c += 1


class _Bracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\(")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"\)")
        self.offset = 1


class _StraightBracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"\[")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"]")
        self.offset = 1


class _CurvedBracket(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"{")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"}")
        self.offset = 1


class _SingleString(Parser):

    before = re.compile(r"[^\\'f]")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = []


class _DoubleString(Parser):

    before = re.compile(r"[^\\\"f]")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = []


class _FormattingSingleString(Parser):

    before = re.compile(r"f")
    current = re.compile(r"'")
    after = re.compile(r"[^']|([^']{2})")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"[^\\]'")
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]


class _FormattingDoubleString(Parser):

    before = re.compile(r"f")
    current = re.compile(r"\"")
    after = re.compile(r"[^\"]|([^\"]{2})")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r'[^\\]"')
        self.offset = 2

        self.subcontent_classes = [_CurvedBracket]


class _SingleMultilineString(Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"'")
    after = re.compile(r"''")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r"[^\\]'''")
        self.offset = 4

        self.subcontent_classes = []


class _DoubleMultilineString(Parser):

    before = re.compile(r"[^\\]")
    current = re.compile(r"\"")
    after = re.compile(r"\"\"")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r'[^\\]"""')
        self.offset = 4

        self.subcontent_classes = []


class _Comment(Parser):

    before = re.compile(r"[\w\W]")
    current = re.compile(r"#")
    after = re.compile(r"[\w\W]")

    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.endchar = re.compile(r'[^\\]\n')
        self.offset = 2

        self.subcontent_classes = []