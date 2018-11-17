# -*- coding: utf-8 -*-
"""
R Chunk Options Source for Neovim Completion Manager

by Gabriel Alcaras
"""

import vim # pylint: disable=E0401

from rsource import Rsource  # pylint: disable=E0401
import filtr  # pylint: disable=E0401
import rlang  # pylint: disable=E0401


class Source(Rsource):  # pylint: disable=too-few-public-methods
    """Completion Manager Source for R Chunk options"""

    # https://github.com/yihui/yihui.name/blob/master/content/knitr/options.md
    CHUNK_OPTIONS = [
        'aniopts="controls,loop"',
        'autodep=FALSE',
        'background="#F7F7F7"',
        'cache.comments= ',
        'cache.lazy=TRUE',
        'cache.path="cache/"',
        'cache.rebuild=FALSE',
        'cache.vars= ',
        'cache=FALSE',
        'child= ',
        'code= ',
        'comment="##"',
        'dependson=""',
        'dev.args= ',
        'dev= ',
        'dpi=72',
        'echo=TRUE',
        'engine.path=""',
        'engine="R"',
        'error=TRUE',
        'eval=TRUE',
        'ffmpeg.bitrate="1M"',
        'ffmpeg.format="webm"',
        'fig.align="default|left|right|center"',
        'fig.asp= ',
        'fig.cap=""',
        'fig.dim=c(7, 7)',
        'fig.env="figure/"',
        'fig.ext= ',
        'fig.height=7',
        'fig.keep="high|none|all|first|last"',
        'fig.lp="fig:"',
        'fig.ncol=""',
        'fig.path= ',
        'fig.pos=""',
        'fig.process= ',
        'fig.scap=""',
        'fig.sep=""',
        'fig.show="asis|hold|animate|hide"',
        'fig.showtext=FALSE',
        'fig.subcap= ',
        'fig.width=7',
        'highlight=TRUE',
        'include=TRUE',
        'interval=1',
        'message=TRUE',
        'opts.label=""',
        'out.extra= ',
        'out.height="7in"',
        'out.width="7in"',
        'prompt=FALSE',
        'purl=TRUE',
        'R.options= '
        'ref.label= ',
        'resize.height= ',
        'resize.width= ',
        'results="markup|asis|hold|hide"',
        'split=FALSE',
        'strip.white=TRUE',
        'tidy.opts= ',
        'tidy=FALSE',
        'warning=TRUE',
    ]

    CHUNK_OPTIONS_TEX = [
        'external=TRUE',
        'sanitize=FALSE',
        'size="normalsize"',
    ]

    CHUNK_OPTIONS_RMD = [
        'class.output=""',
        'class.source=""',
        'fig.retina=1',
        'collapse=FALSE',
    ]

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        self._options = list()
        options = self.CHUNK_OPTIONS

        if self._settings['filetype'] == 'rnoweb':
            options.extend(self.CHUNK_OPTIONS_TEX)

        if self._settings['filetype'] == 'rmd':
            options.extend(self.CHUNK_OPTIONS_RMD)

        options = sorted(options, key=str.lower)
        self._options = self.matches.from_chunk_options(options)

    def on_complete(self, ctx):
        """Refresh NCM list of matches"""

        matches = self._options
        option = rlang.get_option(ctx['typed'])

        self._info('hello :: typed: {}, ccol: {},'
                   ' startccol: {}'.format(ctx['typed'],
                                           ctx['ccol'],
                                           ctx['startccol']))

        if option:
            matches = filtr.arg(matches, option)

        self._info(matches)
        self.complete(ctx, ctx['scope_len'], matches)


SOURCE = Source(vim)

on_complete = SOURCE.on_complete
