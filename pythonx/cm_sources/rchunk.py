# -*- coding: utf-8 -*-
"""
R Chunk Options Source for Neovim Completion Manager,
to be used with nvim-R

by Gabriel Alcaras
"""

from neovim.api.nvim import NvimError
from cm import register_source, getLogger, Base  # pylint: disable=E0401

from omnils import Matches  # pylint: disable=E0401
import filtr  # pylint: disable=E0401
import rlang  # pylint: disable=E0401

LOGGER = getLogger(__name__)

register_source(name='RChunk',
                priority=9,
                abbreviation='RChunk',
                word_pattern=r'[\w_\.]+',
                scoping=True,
                scopes=['rchunk'],
                early_cache=1,
                cm_refresh_patterns=[
                    r',\s?',  # New option
                    r'=\s?"',  # Option value
                ])


class Source(Base):  # pylint: disable=R0902
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

        self.matches = Matches()
        self._settings = dict()

        self._options = list()

        try:
            settings = dict()
            settings['col1_len'] = self.nvim.eval('g:ncm_r_column1_length')
            settings['col2_len'] = self.nvim.eval('g:ncm_r_column2_length')
            settings['col_layout'] = self.nvim.eval('g:ncm_r_column_layout')
            settings['filetype'] = self.nvim.eval('&filetype')
        except NvimError as error:
            self._error('Can\'t load ncm-R options', error)
            raise

        self._settings = settings
        self.matches.setup(settings)

        options = self.CHUNK_OPTIONS

        if settings['filetype'] == 'rnoweb':
            options.extend(self.CHUNK_OPTIONS_TEX)

        if settings['filetype'] == 'rmd':
            options.extend(self.CHUNK_OPTIONS_RMD)

        options = sorted(options, key=str.lower)
        self._options = self.matches.from_chunk_options(options)

    def _error(self, msg, error=''):
        """Output error in logs and in nvim"""

        msg_format = '[ncm-R] R Chunk options: {}'
        msg_format += ': {}' if error else '{}'
        msg = msg_format.format(msg, error)

        LOGGER.error(msg)
        self.message('ERROR', msg)

    def cm_refresh(self, info, ctx,):
        """Refresh NCM list of matches"""

        matches = self._options

        option = rlang.get_option(ctx['typed'])

        if option:
            matches = filtr.arg(matches, option)

        LOGGER.debug('[ncm-R] matches: %s', matches)
        self.complete(info, ctx, ctx['startcol'], matches)
