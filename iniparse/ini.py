"""Access and/or modify INI files

* Compatiable with ConfigParser
* Preserves order of sections & options
* Preserves comments/blank lines/etc
* More conveninet access to data

Example:

    >>> from StringIO import StringIO
    >>> sio = StringIO('''# configure foo-application
    ... [foo]
    ... bar1 = qualia
    ... bar2 = 1977
    ... [foo-ext]
    ... special = 1''')

    >>> cfg = INIConfig(sio)
    >>> print cfg.foo.bar1
    qualia
    >>> print cfg['foo-ext'].special
    1
    >>> cfg.foo.newopt = 'hi!'
    >>> cfg.baz.enabled = 0

    >>> print cfg
    # configure foo-application
    [foo]
    bar1 = qualia
    bar2 = 1977
    newopt = hi!
    [foo-ext]
    special = 1
    <BLANKLINE>
    [baz]
    enabled = 0

"""

# An ini parser that supports ordered sections/options
# Also supports updates, while preserving structure
# Backward-compatiable with ConfigParser


import re
import ds
DEFAULTSECT = 'global'

class ParsingError(IOError):
    """Raised when a configuration file does not follow legal syntax."""

    def __init__(self, filename):
        IOError.__init__(self, 'File contains parsing errors: %s' % filename)
        self.filename = filename
        self.errors = []

    def append(self, lineno, line):
        self.errors.append((lineno, line))
        self.message += '\n\t[line %2d]: %s' % (lineno, line)

class MissingSectionHeaderError(ParsingError):
    """Raised when a key-value pair is found before any section header."""

    def __init__(self, filename, lineno, line):
        IOError.__init__(
            self,
            'File contains no section headers.\nfile: %s, line: %d\n%r' %
            (filename, lineno, line))
        self.filename = filename
        self.lineno = lineno
        self.line = line

class LineType(object):
    line = None

    def __init__(self, line = None):
        if line is not None:
            self.line = line.strip('\n')

    # Return the original line for unmodified objects
    # Otherwise construct using the current attribute values
    def __str__(self):
        if self.line is not None:
            return self.line
        else:
            return self.to_string()

    # If an attribute is modified after initialization
    # set line to None since it is no longer accurate.
    def __setattr__(self, name, value):
        if hasattr(self, name):
            self.__dict__['line'] = None
        self.__dict__[name] = value

    def to_string(self):
        raise Exception('This method must be overridden in derived classes')


class SectionLine(LineType):
    regex = re.compile(r'^\['
                        r'(?P<name>[^]]+)'
                        r'\]\s*'
                        r'((?P<csep>;|#)(?P<comment>.*))?$')

    def __init__(self, name, comment = None, comment_separator = None,
                             comment_offset = -1, line = None):
        super(SectionLine, self).__init__(line)
        self.name = name
        self.comment = comment
        self.comment_separator = comment_separator
        self.comment_offset = comment_offset

    def to_string(self):
        out = '[' + self.name + ']'
        if self.comment is not None:
            # try to preserve indentation of comments
            out = (out + ' ').ljust(self.comment_offset)
            out = out + self.comment_separator + self.comment
        return out

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None
        return cls(m.group('name'), m.group('comment'),
                   m.group('csep'), m.start('csep'),
                   line)
    parse = classmethod(parse)

    def __str__(self):
        if self.name == DEFAULTSECT:
            return ''
        return super(SectionLine, self).__str__()


class OptionLine(LineType):
    def __init__(self, name, value, separator = ' = ', comment = None,
                 comment_separator = None, comment_offset = -1, line = None):
        super(OptionLine, self).__init__(line)
        self.name = name
        self.value = value
        self.separator = separator
        self.comment = comment
        self.comment_separator = comment_separator
        self.comment_offset = comment_offset

    def to_string(self):
        out = '%s%s%s' % (self.name, self.separator, self.value)
        if self.comment is not None:
            # try to preserve indentation of comments
            out = (out + ' ').ljust(self.comment_offset)
            out = out + self.comment_separator + self.comment
        return out

    regex = re.compile(r'^(?P<name>[^:=\s[][^:=]*)'
                       r'(?P<sep>[:=]*\s*)'
                       r'(?P<value>.*)$')

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None

        name = m.group('name').rstrip()
        value = m.group('value')
        sep = m.group('name')[len(name):] + m.group('sep')

        # comments are not detected in the regex because
        # ensuring total compatibility with ConfigParser
        # requires that:
        #     option = value    ;comment   // value=='value'
        #     option = value;1  ;comment   // value=='value;1  ;comment'
        #
        # Doing this in a regex would be complicated.  I
        # think this is a bug.  The whole issue of how to
        # include ';' in the value needs to be addressed.
        # Also, '#' doesn't mark comments in options...
        coff = value.find(';')
        if coff != -1 and value[coff - 1].isspace():
            comment = value[coff + 1:]
            csep = value[coff]
            value = value[:coff].rstrip()
            coff = m.start('value') + coff
        else:
            comment = None
            csep = None
            coff = -1
        return cls(name, value, sep, comment, csep, coff, line)
    parse = classmethod(parse)


def change_comment_syntax(comment_chars = '%;#', allow_rem = False):
    comment_chars = re.sub(r'([\]\-\^])', r'\\\1', comment_chars)
    regex = r'^(?P<csep>[%s]' % comment_chars
    if allow_rem:
        regex += '|[rR][eE][mM]'
    regex += r')(?P<comment>.*)$'
    CommentLine.regex = re.compile(regex)

class CommentLine(LineType):
    regex = re.compile(r'^(?P<csep>[;#@]|[rR][eE][mM])'
                       r'(?P<comment>.*)$')

    def __init__(self, comment = '', separator = '#', line = None):
        super(CommentLine, self).__init__(line)
        self.comment = comment
        self.separator = separator

    def to_string(self):
        return self.separator + self.comment

    def parse(cls, line):
        m = cls.regex.match(line.rstrip())
        if m is None:
            return None
        return cls(m.group('comment'), m.group('csep'), line)
    parse = classmethod(parse)


class EmptyLine(LineType):
    # could make this a singleton
    def to_string(self):
        return ''

    value = property(lambda _: '')

    def parse(cls, line):
        if line.strip(): return None
        return cls(line)
    parse = classmethod(parse)

class LineContainer(object):
    def __init__(self, d = None):
        self.contents = []
        self.orgvalue = None
        if d:
            if isinstance(d, list): self.extend(d)
            else: self.add(d)

    def add(self, x):
        self.contents.append(x)

    def extend(self, x):
        for i in x: self.add(i)

    def get_name(self):
        return self.contents[0].name

    def set_name(self, data):
        self.contents[0].name = data

    def get_value(self):
        if self.orgvalue is not None:
            return self.orgvalue
        elif len(self.contents) == 1:
            return self.contents[0].value
        else:
            return '\n'.join([('%s' % x.value) for x in self.contents
                              if not isinstance(x, CommentLine)])

    def set_value(self, data):
        self.orgvalue = data

    name = property(get_name, set_name)
    value = property(get_value, set_value)

    def __str__(self):
        s = [x.__str__() for x in self.contents]
        return '\n'.join(s)

    def finditer(self, key):
        for x in self.contents[::-1]:
            if hasattr(x, 'name') and x.name == key:
                yield x

    def find(self, key):
        for x in self.finditer(key):
            return x
        raise KeyError(key)


def _make_xform_property(myattrname, srcattrname = None):
    private_attrname = myattrname + 'value'
    private_srcname = myattrname + 'source'
    if srcattrname is None:
        srcattrname = myattrname

    def getfn(self):
        srcobj = getattr(self, private_srcname)
        if srcobj is not None:
            return getattr(srcobj, srcattrname)
        else:
            return getattr(self, private_attrname)

    def setfn(self, value):
        srcobj = getattr(self, private_srcname)
        if srcobj is not None:
            setattr(srcobj, srcattrname, value)
        else:
            setattr(self, private_attrname, value)

    return property(getfn, setfn)


class INISection(object):
    obj = None
    _options = None

    def __init__(self, lineobj, defaults = None):
        self.obj = lineobj
        self._options = {}

    def __getitem__(self, key):
        if key == '__name__':
            return self.obj.name
        try:
            return self._options[key].value
        except KeyError:
            return None

    def __setitem__(self, key, value):
        if key not in self._options:
            # create a dummy object - value may have multiple lines
            obj = LineContainer(OptionLine(key, ''))
            self.obj.add(obj)
            self._options[key] = obj
        self._options[key].value = value

    def __delitem__(self, key):
        remaining = []
        for o in self.obj.contents:
            if not isinstance(o, LineContainer) or key != o.name:
                remaining.append(o)
        self.obj.contents = remaining
        del self._options[key]

    def __iter__(self):
        d = set()
        for x in self.obj.contents:
            if isinstance(x, LineContainer):
                ans = x.name
                if ans not in d:
                    yield ans
                    d.add(ans)

    def _new_namespace(self, name):
        raise Exception('No sub-sections allowed', name)


def make_comment(line):
    return CommentLine(line.rstrip('\n'))


def readline_iterator(f):
    """iterate over a file by only using the file object's readline method"""
    yield "[global]"
    have_newline = False
    while True:
        line = f.readline()

        if not line:
            if have_newline:
                yield ""
            return

        if line.endswith('\n'):
            have_newline = True
        else:
            have_newline = False

        yield line


def lower(x):
    return x.lower()

class INIConfig(object):
    _data = None
    _sections = None
    _parse_exc = None
    _bom = False
    def __init__(self, fp = None, parse_exc = True):
        self._data = LineContainer()
        self._parse_exc = parse_exc

        self._sections = ds.SectionDict()
        if fp is not None:
            self._readfp(fp)

    def __getitem__(self, key):
        return self._sections[key]

    def __setitem__(self, key, value):
        raise Exception('Values must be inside sections', key, value)

    def __delitem__(self, key):
        for line in self._sections.getlist(key):
            self._data.contents.remove(line)
        del self._sections[key]

    def __iter__(self):
        d = set()
        d.add(DEFAULTSECT)
        for x in self._data.contents:
            if isinstance(x, LineContainer):
                if x.name not in d:
                    yield x.name
                    d.add(x.name)

    def _new_namespace(self, name):
        if self._data.contents:
            self._data.add(EmptyLine())
        obj = LineContainer(SectionLine(name))
        obj = INISection(obj)
        self._data.add(obj)
        self._sections.appendlist(name, obj)
        return obj


    def __str__(self):
        if self._bom:
            fmt = u'\ufeff%s'
        else:
            fmt = '%s'
        return fmt % self._data.__str__()

    __unicode__ = __str__

    _line_types = [EmptyLine, CommentLine,
                   SectionLine, OptionLine]

    def _parse(self, line):
        for linetype in self._line_types:
            lineobj = linetype.parse(line)
            if lineobj:
                return lineobj
        else:
            # can't parse line
            return None

    def _readfp(self, fp):
        cur_section = None
        cur_option = None
        cur_section_name = None
        cur_option_name = None
        pending_lines = []
        pending_empty_lines = False
        try:
            fname = fp.name
        except AttributeError:
            fname = '<???>'
        linecount = 0
        exc = None
        line = None

        for line in readline_iterator(fp):
            # Check for BOM on first line
            if linecount == 0 and isinstance(line, unicode):
                if line[0] == u'\ufeff':
                    line = line[1:]
                    self._bom = True

            lineobj = self._parse(line)
            linecount += 1

            if not cur_section and not isinstance(lineobj,
                                (CommentLine, EmptyLine, SectionLine)):
                if self._parse_exc:
                    raise MissingSectionHeaderError(fname, linecount, line)
                else:
                    lineobj = make_comment(line)

            if lineobj is None:
                if self._parse_exc:
                    if exc is None: exc = ParsingError(fname)
                    exc.append(linecount, line)
                lineobj = make_comment(line)


            if isinstance(lineobj, OptionLine):
                if pending_lines:
                    cur_section.extend(pending_lines)
                    pending_lines = []
                    pending_empty_lines = False
                cur_option = LineContainer(lineobj)
                cur_section.add(cur_option)
                cur_option_name = cur_option.name
                optobj = self._sections[cur_section_name]
                optobj._options[cur_option_name] = cur_option

            if isinstance(lineobj, SectionLine):
                if pending_lines:
                    self._data.extend(pending_lines)
                    pending_lines = []
                    pending_empty_lines = False
                cur_section = LineContainer(lineobj)
                self._data.add(cur_section)
                cur_option = None
                cur_option_name = None
                cur_section_name = cur_section.name
                if cur_section_name not in self._sections:
                    self._sections[cur_section_name] = \
                            INISection(cur_section)
                else:
                    self._sections.appendlist(cur_section_name, INISection(cur_section))

            if isinstance(lineobj, (CommentLine, EmptyLine)):
                pending_lines.append(lineobj)
                if isinstance(lineobj, EmptyLine):
                    pending_empty_lines = True

        self._data.extend(pending_lines)
        if line and line[-1] == '\n':
            self._data.add(EmptyLine())

        if exc:
            raise exc


    def f(self, *args, **kwargs):
        return self._sections.f(*args, **kwargs)

    def g(self, *args, **kwargs):
        return self._sections.f(*args, **kwargs)
