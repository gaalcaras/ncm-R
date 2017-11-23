# -*- coding: utf-8 -*-
"""
R Source for Neovim Completion Manager, to be used with nvim-R

by Gabriel Alcaras
"""

import re
from os import listdir

import neovim
from cm import register_source, getLogger, Base  # pylint: disable=E0401

LOGGER = getLogger(__name__)

register_source(name='R',
                priority=9,
                abbreviation='R',
                word_pattern=r'[\w_\.]+',
                scoping=True,
                scopes=['r'],
                early_cache=1,
                cm_refresh_patterns=[r'\$', r'\(', r'"', r"'"],)


def create_match(word='', struct='', pkg=''):
    """Create ncm match dictionnary

    :word: word (appears in menu)
    :struct: type (str() in R)
    :pkg: pkg
    :returns: ncm match

    """

    if not word and not struct:
        return None

    match = dict(word=word, menu=struct, struct=struct)

    if pkg:
        match['pkg'] = pkg
        match['menu'] += ' [' + pkg + ']'

    if struct == 'function':
        match['snippet'] = word + '($1)'

    if struct in ('data.frame', 'tbl_df'):
        match['snippet'] = word + '$$1'

    if struct == 'package':
        match['snippet'] = word + '::$1'

    return match


def to_matches(lines):
    """Transform omni lists from Nvim-R into list of NCM matches

    :lines: list of lines from an omni list
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\x06', line)
        match = create_match(word=parts[0], struct=parts[1], pkg=parts[3])

        if match:
            cm_list.append(match)

    return cm_list


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


def filter_matches_pkgs(ncm_matches, pkg=None):
    """Filter list of ncm matches with R packages

    :ncm_matches: list of matches (dictionaries)
    :pkg: only show matches from given R packages
    :returns: filtered list of ncm matches
    """

    if not pkg:
        return ncm_matches

    ncm_matches = [d for d in ncm_matches if any(p in d['pkg'] for p in pkg)]

    return ncm_matches


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
        if typed and typed in match['word']:
            if hide and hide in match['word']:
                continue

            if rm_typed:
                match['word'] = match['word'].replace(typed, '')

            filtered_list.append(match)

    return filtered_list


class Source(Base):
    """Completion Manager Source for R language"""

    R_WORD = re.compile(r'[\w\$_\.]+$')
    R_FUNC = re.compile(r'([^\(]+)\([^\(]*')

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        self._nvimr = self.nvim.eval('$NVIMR_ID')
        self._tmpdir = self.nvim.eval('g:rplugin_tmpdir')

        self._pkg_loaded = list()
        self._pkg_installed = list()
        self._pkg_matches = list()
        self._fnc_matches = list()
        self._obj_matches = list()

        self._start_nvimr()
        self.get_all_pkg_matches()

    def _start_nvimr(self):
        """Start nvim-R"""

        try:
            if self.nvim.eval('g:SendCmdToR') == "function('SendCmdToR_fake')":
                self.nvim.funcs.StartR('R')
        except neovim.api.nvim.NvimError as ex:
            self.message('error', 'Could not start nvim-R :(')
            LOGGER.exception(ex)

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

    def update_func_matches(self):
        """Update function matches if necessary"""
        if self.update_loaded_pkgs():
            LOGGER.info('Update Loaded R packages: %s', self._pkg_loaded)
            funcs = filter_matches_pkgs(self._pkg_matches, self._pkg_loaded)
            funcs = filter_matches_struct(funcs, 'function')
            self._fnc_matches = funcs

    def get_matches(self, word):
        """Return function and object matches based on given word

        :word: string to filter matches with
        :returns: list of ncm matches
        """

        self.get_all_obj_matches()
        matches = self._obj_matches

        if '$' in word:
            # If we're looking inside a data frame or tibble, only return
            # its variables
            matches = filter_matches(matches, word, rm_typed=True)
        else:
            # Otherwise, return objects (hiding data frame variables) and
            # functions from loaded R packages
            self.update_func_matches()
            matches.extend(self._fnc_matches)
            matches.extend(self._pkg_installed)

            matches = filter_matches(matches, word, hide='$')

        return matches

    def get_func_matches(self, funcname, word):
        """Return matches when completion happens inside function

        :funcname: the name of function
        :word: word typed
        :returns: list of ncm matches
        """

        matches = list()

        if funcname in ('library', 'require'):
            return self._pkg_installed

        matches.extend(self.get_matches(word))

        return matches

    def cm_refresh(self, info, ctx,):
        """Refresh NCM list of matches"""

        word_match = re.search(self.R_WORD, ctx['typed'])
        func_match = re.search(self.R_FUNC, ctx['typed'])
        word, func = ['', '']

        if word_match:
            word = word_match[0]
            LOGGER.info('word: %s', word)

        if func_match:
            func = func_match.group(1)
            LOGGER.info('func: %s', func)

        if func:
            matches = self.get_func_matches(func, word)
        else:
            matches = self.get_matches(word)

        LOGGER.debug("matches: [%s]", matches)
        self.complete(info, ctx, ctx['startcol'], matches)
