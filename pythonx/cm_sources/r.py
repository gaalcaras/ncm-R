# -*- coding: utf-8 -*-
"""
R Source for Neovim Completion Manager, to be used with nvim-R

by Gabriel Alcaras
"""

from os import listdir, path
import re

import neovim
from cm import register_source, getLogger, Base  # pylint: disable=E0401

import omnils  # pylint: disable=E0401
import filtr  # pylint: disable=E0401
import rlang  # pylint: disable=E0401

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


class Source(Base):  # pylint: disable=R0902
    """Completion Manager Source for R language"""

    R_WORD = re.compile(r'[\w\$_\.]+$')

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        self._nvimr = self.nvim.eval('$NVIMR_ID')
        self._tmpdir = self.nvim.eval('g:rplugin_tmpdir')

        self._pkg_loaded = list()
        self._pkg_installed = list()

        self._all_matches = list()
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

        try:
            self.nvim.funcs.SendToNvimcom('\x08' + self._nvimr + rcmd)
        except neovim.api.nvim.NvimError:
            LOGGER.warn('ncm-R can\'t connect to nvimcom.')
            self.message('ERROR',
                         'ncm-R can\'t connect to nvimcom. '
                         'Please start R using Nvim-R '
                         '(default mapping: <localleader>rf).')

    def update_loaded_pkgs(self):
        """Update list of loaded R packages

        :returns: 1 if loaded packages have changed, 0 otherwise
        """

        loadpkg = path.join(self._tmpdir, 'loaded_pkgs_' + self._nvimr)
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
            self.message('ERROR',
                         'ncm-R can\'t find loaded R packages. '
                         'Please start R using Nvim-R '
                         '(default mapping: <localleader>rf).')

        new_loaded_pkgs = (set(old_pkgs) == set(self._pkg_loaded))
        new_pkgs = any(p not in self._pkg_installed for p in self._pkg_loaded)

        if not new_loaded_pkgs and not new_pkgs:
            return 0

        if new_pkgs:
            LOGGER.info('Some loaded packages miss an omni file. '
                        'Refreshing matches...')
            self.get_all_pkg_matches()

        return 1

    def get_all_obj_matches(self):
        """Populate candidates with all R objects in the environment"""

        self.nvim.funcs.BuildROmniList("")
        globenv_file = path.join(self._tmpdir, 'GlobalEnvList_' + self._nvimr)

        with open(globenv_file, 'r') as globenv:
            objs = [obj.strip() for obj in globenv.readlines()]

        self._obj_matches = omnils.to_matches(objs)

    def get_all_pkg_matches(self):
        """Populate matches list with candidates from every R package"""

        compdir = self.nvim.eval('g:rplugin_compldir')
        comps = [f for f in listdir(compdir) if 'omnils' in f]

        if not comps:
            LOGGER.warn('No omnils_* files in %s', compdir)
            self.message('INFO',
                         'ncm-R can\'t find the completion data. '
                         'Please load the R packages you need, '
                         'like the "base" package.')

        for filename in comps:
            pkg_name = re.search(r'_(\w+)_', filename).group(1)

            if pkg_name in self._pkg_installed:
                continue

            match = omnils.create_match(word=pkg_name, struct='package')
            self._pkg_installed.append(pkg_name)
            self._pkg_matches.append(match)

            filepath = path.join(compdir, filename)

            with open(filepath, 'r') as omnil:
                comps = [pkg.strip() for pkg in omnil.readlines()]

            self._all_matches.extend(omnils.to_matches(comps))

    def get_data_matches(self):
        """Return list of matches with datasets from R packages"""

        pkg_matches = filtr.pkg(self._all_matches, self._pkg_loaded)
        data = filtr.struct(pkg_matches, 'data.frame')
        data.extend(filtr.struct(pkg_matches, 'tbl_df'))

        return data

    def update_func_matches(self):
        """Update function matches if necessary"""

        if self.update_loaded_pkgs():
            LOGGER.info('Update Loaded R packages: %s', self._pkg_loaded)
            funcs = filtr.pkg(self._all_matches, self._pkg_loaded)
            funcs = filtr.struct(funcs, 'function')
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
            obj_m = filtr.word(obj_m, pipe + '$', rm_typed=True)
        else:
            if '$' in word:
                # If we're looking inside a data frame or tibble, only return
                # its variables
                obj_m = filtr.word(obj_m, word, rm_typed=True)
            else:
                # Otherwise, hide what's inside data.frames
                obj_m = filtr.word(obj_m, word, hide='$')

        matches = obj_m

        # Get functions from loaded R packages
        self.update_func_matches()
        func_m = filtr.pkg(self._fnc_matches, pkg)
        func_m.extend(self._pkg_matches)

        if not pkg or (pkg and word):
            func_m = filtr.word(func_m, word)

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
            return self._pkg_matches

        if func in 'data':
            return self.get_data_matches()

        args = list()
        for source in [self._fnc_matches, self._obj_matches]:
            args = filtr.arg(source, func, pipe)
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

        cur_buffer = self.nvim.current.buffer
        lnum = ctx['lnum']
        col = ctx['col']

        if re.match('^#', cur_buffer[lnum-1]):
            return

        if not self._pkg_loaded:
            self.update_loaded_pkgs()
            return

        word_match = re.search(self.R_WORD, ctx['typed'])
        word = word_match.group(0) if word_match else ''

        isinquot = re.search('["\']' + word + '$', ctx['typed'])

        function = rlang.get_function(cur_buffer, lnum, col)
        pkg = function[0]
        func = function[1]

        if isinquot and func and not re.search('(library|require|data)', func):
            return

        pipe = rlang.get_pipe(cur_buffer, lnum, col)

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
