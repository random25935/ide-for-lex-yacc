import sys
from PySide2.QtCore import QRegExp
from PySide2.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
def format(color, style=''):
    '''Return a QTextCharFormat with the given attributes.
    '''
    _color = QColor()
    _color.setNamedColor(color)
    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)
    if 'italicbold' in style:
        _format.setFontItalic(True)
        _format.setFontWeight(QFont.Bold)
    return _format
mybrawn = ("#7E5916")
# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('#c87832', 'bold'),
    'operator': format('#969696'),
    'brace': format('darkGray'),
    'defclass': format('#dcdcff', 'bold'),
    'classes': format('#cc0000', 'bold'),
    'Qtclass': format('black', 'bold'),
    'string': format('#42b883'),
    'string2': format('#347474'),
    'comment': format('#808080'),
    'self': format('#96558c', 'italicbold'),
    'selfnext': format('#2e3436', 'bold'),
    'Qnext': format('#2e3436', 'bold'),
    'numbers': format('#6496be'),
}
class Highlighter(QSyntaxHighlighter):
    '''Syntax highlighter for the Python language.
    '''
    # Python keywords
    keywords = [
        'auto', 'break', 'case', 'char', 'const', 'continue',
        'default', 'do', 'double', 'else', 'enum', 'extern',
        'float', 'for', 'goto', 'if', 'int', 'long', 'register',
        'return', 'short', 'signed', 'sizeof', 'static', 'struct',
        'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile',
        'while'
    ]
    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]
    # braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        tri = ("'''")
        trid = ('"""')
        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp(tri), 1, STYLES['string2'])
        self.tri_double = (QRegExp(trid), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in Highlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in Highlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in Highlighter.braces]

        # All other rules
        rules += [
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences ### "\"([^\"]*)\"" ### "\"(\\w)*\""
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an word
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']), ### (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),

            # 'self.' followed by an word
            (r'\bself\b)', 1, STYLES['selfnext']), ### (r'\bself.\b\s*(\w+)', 1, STYLES['selfnext']),

            # 'Q' followed by an word
            (r'\b[Q.]\b\s*(\w+)', 1, STYLES['Qnext']),

            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['classes']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # 'Q'  word
            #(r'\\bQ[A-Za-z]+\\b', 1, STYLES['Qtclass']), #(QRegExp("\\bQ[A-Za-z]+\\b")
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):

#        Apply syntax highlighting to the given block of text.

        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        '''Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        '''
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False