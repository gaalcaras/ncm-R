# -*- coding: utf-8 -*-
"""
R Source for Neovim Completion Manager, to be used with nvim-R

by Gabriel Alcaras
"""

import re
from os import listdir

from cm import register_source, getLogger, Base  # pylint: disable=E0401

LOGGER = getLogger(__name__)

register_source(name='R',
                priority=9,
                abbreviation='R',
                word_pattern=r'[\w_\.]+',
                scoping=True,
                scopes=['r'],
                early_cache=1,
                cm_refresh_patterns=[
                    r'\$', r'::', r'"', r"'",
                    # Refresh immediately after symbol and after typing 3 chars
                    r',\s([\w_\.]{3})?',  # New argument
                    r'^\s{2,}([\w_\.]{3})?$',  # New argument on a new line
                    r'\(([\w_\.]{3})?',  # After a parenthesis
                ])


def get_pipe(buff, numline, numcol):
    """Check if completion happens inside a pipe, if so, return the piped
    data

    :buff: vim buffer
    :numline: line number
    :numcol: column number
    :returns: piped data
    """

    r_pipe = re.compile(r'([\w_\.\$]+)\s?%>%')
    r_block = re.compile(r'<-')

    no_pipe = 0
    for numl in range(numline-1, -1, -1):
        line = buff[numl]

        if numl == numline-1:
            # If line is where the cursor is currently at
            line = line[0:numcol]
            r_pipeline = re.compile(r'%>%')
        else:
            r_pipeline = re.compile(r'(%>%|\)\s?\+|,)\s*$')

        if r_pipeline.search(line):
            # If line clearly continues data pipeline
            has_pipe = r_pipe.search(line)

            if has_pipe:
                return has_pipe.group(1)
        else:
            no_pipe += 1
            begin_block = r_block.match(line)

            # The line could be the last line of a pipeline,
            # go to next iteration to check previous line...
            if begin_block or no_pipe == 2:
                # Unless the line clearly begins a block or the line below this
                # one does not match a pipeline either
                return None


def get_open_bracket_col(typed=''):
    """Find the column of the last unclosed bracket

    :typed: typed content
    :returns: position of last unclosed bracket
    """
    if not typed:
        return -1

    open_brackets = []
    inside_quotes = False
    quotes = ''

    for col, char in enumerate(typed):
        if char in ('"', "'") and typed[col-1] != "\"":
            if not inside_quotes:
                quotes = char
                inside_quotes = True
            else:
                inside_quotes = False if char == quotes else True
            continue

        if char == '(':
            open_brackets.append(col)

        if char == ')':
            try:
                open_brackets.pop()
            except IndexError:
                return -1

    try:
        result = open_brackets.pop()
    except IndexError:
        result = -1

    return result


def get_function(buff, numline, numcol):
    """Return function and package name of current line

    :buff: vim buffer
    :numline: line number
    :numcol: column number
    :returns: [package_name, function_name]
    """

    r_func = re.compile((r'((?P<pkg>[\w\._]+)::)?' +
                         r'((?P<fnc>[\w\._]+)\()?[^\(^:]*$'))
    r_param = re.compile(r',\s*$')
    r_block = re.compile(r'<-')

    no_func = 0
    for numl in range(numline-1, -1, -1):
        line = buff[numl]

        line = line[0:numcol-1] if numl == numline-1 else line

        open_bracket = get_open_bracket_col(line)

        if open_bracket == -1:
            if r_param.search(line):
                continue

            no_func += 1
            begin_block = r_block.match(line)

            # The line could be the last line of a list of arguments,
            # go to next iteration to check previous line...
            if begin_block or no_func == 2:
                # Unless the line clearly begins a block or the line below this
                # one does not match an argument either
                return ['', '']
        else:
            line = line[0:open_bracket+1]

        func_match = re.search(r_func, line)
        func = func_match.group('fnc') if func_match else ''
        pkg = func_match.group('pkg') if func_match else ''

        if (pkg and numl == numline-1) or func:
            return [pkg, func]

        if numl == 0 and not pkg and not func:
            return ['', '']


def create_match(word='', struct='', pkg='', info=''):
    """Create ncm match dictionnary

    :word: word (appears in menu)
    :struct: type (str() in R)
    :pkg: pkg
    :info: additional information about the object (args, doc, etc.)
    :returns: ncm match
    """

    if not word and not struct:
        return None

    match = dict(word=word,
                 menu='{:10}'.format(struct[0:10]),
                 struct=struct)

    match['pkg'] = pkg if pkg else ''

    if struct == 'function':

        if info:
            args = get_func_args(info)
            pkg_name = '{' + pkg[0:8] + '}'
            menu = '{:10}'.format(pkg_name)
            menu += ' ' + match['word'] + '('
            menu += ', '.join(args) + ')'

            match['menu'] = menu
            match['snippet'] = make_func_snippet(word, args)

            margs = list()
            for arg in args:
                if arg in ('NO_ARGS', '...'):
                    continue

                margs.append(create_match(word=arg, struct='argument'))

            match['args'] = margs

        else:
            match['snippet'] = word + '($1)'

    if struct in ('data.frame', 'tbl_df'):
        match['snippet'] = word + ' %>%$1'
        pkg_name = '{' + pkg[0:8] + '}'
        match['menu'] = '{:10}'.format(pkg)
        match['menu'] += ' ' + struct

    if struct == 'package':
        match['snippet'] = word + '::$1'

    if struct == 'argument':
        word_parts = [w.strip() for w in word.split('=')]
        lhs = word_parts[0]
        rhs = word_parts[1] if len(word_parts) == 2 else ''

        match['word'] = lhs
        match['menu'] = '{:10}'.format('param')
        match['menu'] += ' = ' + rhs if rhs else ''

        if rhs:
            match['snippet'] = lhs + ' = ${1:' + rhs + '}'
        else:
            match['snippet'] = lhs + ' = $1'

    return match


def make_func_snippet(func='', args=None):
    """Create function snippet with its arguments

    :func: the function name
    :args: function arguments
    :returns: snippet
    """
    snippet = func + '('

    if args[0] == 'NO_ARGS':
        return snippet + ')'

    # Fill snippet with mandatory arguments
    mand_args = [a for a in args if '=' not in a]

    for numarg, arg in enumerate(mand_args):
        if arg in ('...') and numarg > 0:
            continue

        snippet += '${' + str(numarg+1) + ':' + arg + '}, '

    if len(mand_args) >= 1:
        snippet = snippet[:-2]
    else:
        snippet += '$1'

    snippet = snippet + ')'

    return snippet


def get_func_args(info=''):
    """Return function arguments based on omniline info

    :info: information from omni files
    :returns: ncm match with info entry
    """
    if not info:
        return list()

    splits = re.split('\x08', info)
    args = splits[0]
    args = re.split('\t', args)
    args = [arg.replace('\x07', ' = ') for arg in args]

    return args


def to_matches(lines):
    """Transform omni lists from Nvim-R into list of NCM matches

    :lines: list of lines from an omni list
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\x06', line)
        match = create_match(word=parts[0], struct=parts[1], pkg=parts[3],
                             info=parts[4])

        if match:
            cm_list.append(match)

    return cm_list


def filter_matches_arg(ncm_matches, func="", pipe=None):
    """Filter list of ncm matches of arguments for func

    :ncm_matches: list of matches
    :func: function name
    :pipe: piped data
    :returns: filtered list of ncm matches
    """

    if not func:
        return ncm_matches

    args = [m['args'] for m in ncm_matches if m['word'] == func]

    if args:
        if pipe:
            # In data pipelines, hide arguments like ".data = "
            return [a for a in args[0] if '.' not in a['word']]

        return args[0]

    return ['']


def filter_matches_struct(ncm_matches, struct=""):
    """Filter list of ncm matches based on their types (str() in R)

    :ncm_matches: list of matches (dictionaries)
    :struct: only show matches of given type
    :returns: filtered list of ncm matches
    """

    if not struct:
        return ncm_matches

    ncm_matches = [d for d in ncm_matches if d['struct'] == struct]

    return ncm_matches


def filter_matches_pkgs(ncm_matches, pkgs=None):
    """Filter list of ncm matches with R packages

    :ncm_matches: list of matches
    :pkgs: only show matches from given R packages
    :returns: filtered list of ncm matches
    """

    if not pkgs:
        return ncm_matches

    res_matches = []
    packages = [pkgs] if isinstance(pkgs, str) else pkgs
    for pkg in packages:
        pkg_matches = [d for d in ncm_matches if d['pkg'] == pkg]
        res_matches.extend(pkg_matches)

    return res_matches


def filter_matches(ncm_matches, typed="", hide="", rm_typed=False):
    """Filter list of ncm matches

    :ncm_matches: list of matches (dictionaries)
    :typed: filter matches with this string
    :hide: filter out matches containing this string
    :rm_typed: remove typed string from the filtered matches
    :returns: filtered list of cm dictionaries
    """

    filtered_list = list()

    for match in ncm_matches:
        if typed and re.match(re.escape(typed), match['word']):
            if hide and hide in match['word']:
                continue

            if rm_typed:
                match['word'] = match['word'].replace(typed, '')

            filtered_list.append(match)

    return filtered_list


class Source(Base):
    """Completion Manager Source for R language"""

    R_WORD = re.compile(r'[\w\$_\.]+$')

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        self._nvimr = self.nvim.eval('$NVIMR_ID')
        self._tmpdir = self.nvim.eval('g:rplugin_tmpdir')

        self._pkg_loaded = list()
        self._pkg_installed = list()
        self._pkg_matches = list()
        self._fnc_matches = list()
        self._obj_matches = list()

        self.get_all_pkg_matches()

    def _r_output_to_file(self, rcmd='', filepath=''):
        """Write output of R command to file

        :rcmd: R command to run
        :filepath: filepath to write output to
        """
        if not rcmd and not filepath:
            return

        rcmd = 'writeLines(text = paste(' + rcmd + ', collapse="\\n"), '
        rcmd += 'con = "' + filepath + '")'
        self.nvim.funcs.SendToNvimcom('\x08' + self._nvimr + rcmd)

    def update_loaded_pkgs(self):
        """Update list of loaded R packages

        :returns: 1 if loaded packages have changed, 0 otherwise
        """

        loadpkg = self._tmpdir + '/loaded_pkgs_' + self._nvimr
        self.nvim.funcs.AddForDeletion(loadpkg)

        self._r_output_to_file('.packages()', loadpkg)
        old_pkgs = self._pkg_loaded

        try:
            loaded_pkgs = open(loadpkg, 'r')
            pkgs = [pkg.strip() for pkg in loaded_pkgs.readlines()]
            self._pkg_loaded = pkgs

            loaded_pkgs.close()
        except FileNotFoundError:
            LOGGER.warn('Cannot find loaded R packages. Please start nvim-R')

        if set(old_pkgs) == set(self._pkg_loaded):
            return 0

        return 1

    def get_all_obj_matches(self):
        """Populate candidates with all R objects in the environment"""

        self.nvim.funcs.BuildROmniList("")
        globenv_file = self._tmpdir + '/GlobalEnvList_' + self._nvimr

        with open(globenv_file, 'r') as globenv:
            objs = [obj.strip() for obj in globenv.readlines()]

        self._obj_matches = to_matches(objs)

    def get_all_pkg_matches(self):
        """Populate matches list with candidates from every R package"""

        compdir = self.nvim.eval('g:rplugin_compldir')
        comps = [f for f in listdir(compdir) if 'omnils' in f]

        for filename in comps:
            match = create_match(word=re.search(r'_(\w+)_', filename)[1],
                                 struct='package')

            if match:
                self._pkg_installed.append(match)

        compfiles = [compdir + '/' + comp for comp in comps]

        for pkg in compfiles:
            with open(pkg, 'r') as omnil:
                comps = [pkg.strip() for pkg in omnil.readlines()]

            self._pkg_matches.extend(to_matches(comps))

    def get_data_matches(self):
        """Return list of matches with datasets from R packages"""
        pkg_matches = filter_matches_pkgs(self._pkg_matches, self._pkg_loaded)
        data = filter_matches_struct(pkg_matches, 'data.frame')
        data.extend(filter_matches_struct(pkg_matches, 'tbl_df'))

        return data

    def update_func_matches(self):
        """Update function matches if necessary"""

        if self.update_loaded_pkgs():
            LOGGER.info('Update Loaded R packages: %s', self._pkg_loaded)
            funcs = filter_matches_pkgs(self._pkg_matches, self._pkg_loaded)
            funcs = filter_matches_struct(funcs, 'function')
            self._fnc_matches = funcs

    def get_matches(self, word, pkg=None, pipe=None):
        """Return function and object matches based on given word

        :word: string to filter matches with
        :pkg: only show functions from R package
        :pipe: piped data
        :returns: list of ncm matches
        """

        self.get_all_obj_matches()
        obj_m = self._obj_matches

        if pipe:
            # Inside data pipeline, keep variables from piped data
            obj_m = filter_matches(obj_m, pipe + '$', rm_typed=True)
        else:
            if '$' in word:
                # If we're looking inside a data frame or tibble, only return
                # its variables
                obj_m = filter_matches(obj_m, word, rm_typed=True)
            else:
                # Otherwise, hide what's inside data.frames
                obj_m = filter_matches(obj_m, word, hide='$')

        matches = obj_m

        # Get functions from loaded R packages
        self.update_func_matches()
        func_m = filter_matches_pkgs(self._fnc_matches, pkg)
        func_m.extend(self._pkg_installed)

        if not pkg or (pkg and word):
            func_m = filter_matches(func_m, word)

        matches.extend(func_m)

        return matches

    def get_func_matches(self, func, word, pipe=None):
        """Return matches when completion happens inside function

        :func: the name of function
        :word: word typed
        :pipe: piped data
        :returns: list of ncm matches
        """

        if func in ('library', 'require'):
            return self._pkg_installed

        if func in 'data':
            return self.get_data_matches()

        args = list()
        for source in [self._fnc_matches, self._obj_matches]:
            args = filter_matches_arg(source, func, pipe)
            args.extend(args)

            if len(args) > 1:
                break

        objs = self.get_matches(word, pipe=pipe)

        matches = list()
        if pipe:
            matches.extend(objs+args)
        else:
            matches.extend(args+objs)

        return matches

    def cm_refresh(self, info, ctx,):
        """Refresh NCM list of matches"""

        if not self._pkg_loaded:
            self.update_loaded_pkgs()

        cur_buffer = self.nvim.current.buffer
        lnum = ctx['lnum']
        col = ctx['col']

        word_match = re.search(self.R_WORD, ctx['typed'])
        word = word_match[0] if word_match else ''

        isinquot = re.search('["\']' + word + '$', ctx['typed'])

        function = get_function(cur_buffer, lnum, col)
        pkg = function[0]
        func = function[1]

        if isinquot and func and not re.search('(library|require|data)', func):
            return

        pipe = get_pipe(cur_buffer, lnum, col)

        LOGGER.info('word: "%s", func: "%s", pkg: %s, pipe: %s',
                    word, func, pkg, pipe)

        if func:
            matches = self.get_func_matches(func, word, pipe)
        else:
            if not word and not pkg:
                return

            matches = self.get_matches(word, pkg=pkg)

        LOGGER.debug("matches: %s", matches)
        self.complete(info, ctx, ctx['startcol'], matches)
