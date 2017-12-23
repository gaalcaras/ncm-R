# -*- coding: utf-8 -*-
"""
ncm-R: tools to convert omnils to NCM matches

by Gabriel Alcaras
"""

import re


class Function(object):

    """Function object to generate snippet and arguments."""

    def __init__(self, word='', info=''):
        """Initialize function object with match data"""

        self._word = word
        self._info = info

        self._snippet = ''
        self._args = list()

        self._get_args()
        self._make_snippet()

    def _get_args(self):
        """Get function arguments based on omniline info"""

        if not self._info:
            return list()

        if re.search('\x08', self._info):
            splits = re.split('\x08', self._info)
            args = splits[0]
        else:
            args = self._info

        args = re.split('\t', args)
        args = [arg.replace('\x07', ' = ') for arg in args]

        self._args = args

    def _make_snippet(self):
        """Create function snippet with its arguments"""

        self._snippet = self._word + '('

        if self._args[0] == 'NO_ARGS':
            self._snippet += ')'
            return

        # Get arguments without no default value (usually mandatory arguments)
        mand_args = [a for a in self._args if '=' not in a]

        for numarg, arg in enumerate(mand_args):
            if arg in ('...') and numarg > 0:
                continue

            self._snippet += '${' + str(numarg+1) + ':' + arg + '}, '

        if len(mand_args) >= 1:
            self._snippet = self._snippet[:-2]
        else:
            self._snippet += '$1'

        self._snippet += ')'

    def args(self):
        """Return list of arguments as NCM matches"""

        margs = list()
        for arg in self._args:
            if arg in ('NO_ARGS', '...'):
                continue

            marg = Match(word=arg, struct='argument')
            margs.append(marg.get())

        return margs

    def snippet(self):
        """Return function snippet"""

        return self._snippet


class Match(object):  # pylint: disable=too-few-public-methods

    """NCM match"""

    def __init__(self, word='', struct='', pkg='', info=''):
        """Initialize match object

        :word: word (appears in menu)
        :struct: type (str() in R)
        :pkg: pkg
        :info: additional information about the object (args, doc, etc.)
        """

        if not word and not struct:
            return None

        self.word = word
        self.struct = struct
        self.pkg = pkg if pkg else ''
        self.info = info if info else ''

        self.args = list()
        self.snippet = ''
        self.menu = '{:10}'.format(struct[0:10])

        if struct == 'function':
            self._process_function()
        elif struct in ('data.frame', 'tbl_df'):
            self._process_df()
        elif struct == 'package':
            self._process_package()
        elif struct == 'argument':
            self._process_argument()
        else:
            pass

    def _get_obj_title(self):
        """Get object title, e.g. function or dataset description"""

        if not self.info:
            return list()

        obj_title = re.search(r'\x08(.*)\x05', self.info)

        if obj_title:
            return obj_title.group(1).strip()

        return ''

    def _process_function(self):
        """Process match when it's a function."""

        title = self._get_obj_title()
        title = title if title else 'function'

        function = Function(word=self.word, info=self.info)

        pkg_name = '{' + self.pkg[0:8] + '}'
        menu = '{:10}'.format(pkg_name)
        menu += ' ' + title

        self.menu = menu
        self.snippet = function.snippet()
        self.args = function.args()

    def _process_df(self):
        """Process match when it's a data.frame or a tibble."""

        title = self._get_obj_title()

        self.snippet = self.word + ' %>%$1'
        pkg_name = '{' + self.pkg[0:8] + '}'
        self.menu = '{:10}'.format(pkg_name)
        self.menu += ' {:10}'.format(self.struct[0:10])
        self.menu += ' ' + title

    def _process_package(self):
        """Process match when it's an R package."""

        self.snippet = self.word + '::$1'
        self.menu = 'package ' + self.info

    def _process_argument(self):
        """Process match when it's a function argument."""

        word_parts = [w.strip() for w in self.word.split('=')]
        lhs = word_parts[0]
        rhs = word_parts[1] if len(word_parts) == 2 else ''

        self.word = lhs
        self.menu = '{:10}'.format('param')
        self.menu += ' = ' + rhs if rhs else ''

        if rhs:
            quotes = re.search(r'^"(.*)"$', rhs)

            if quotes:
                self.snippet = lhs + ' = "${1:' + quotes.group(1) + '}"'
            else:
                self.snippet = lhs + ' = ${1:' + rhs + '}'
        else:
            self.snippet = lhs + ' = $1'

    def get(self):
        """Return NCM match as a dictionary."""

        match = dict(word=self.word, menu=self.menu, pkg=self.pkg,
                     struct=self.struct, snippet=self.snippet)

        if self.args:
            match['args'] = self.args

        return match


def to_pkg_matches(lines):
    """Transform package description lines from Nvim-R into list of NCM matches

    :lines: list of lines from a pack_descriptions file
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\t', line)

        if len(parts) >= 2:
            match = Match(word=parts[0], info=parts[1], struct='package')

            if match:
                cm_list.append(match.get())

    return cm_list


def to_matches(lines):
    """Transform omni lists from Nvim-R into list of NCM matches

    :lines: list of lines from an omni list
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\x06', line)

        if len(parts) >= 5:
            match = Match(word=parts[0], struct=parts[1], pkg=parts[3],
                          info=parts[4])

            if match:
                cm_list.append(match.get())

    return cm_list
