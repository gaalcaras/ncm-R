# -*- coding: utf-8 -*-
"""
R Source for Neovim Completion Manager

by Gabriel Alcaras
"""

from neovim.api.nvim import NvimError
from cm import getLogger, Base  # pylint: disable=E0401

from omnils import Matches  # pylint: disable=E0401

LOGGER = getLogger(__name__)


class Rsource(Base):  # pylint: disable=too-few-public-methods

    """Base for R Source completion"""

    def __init__(self, nvim):
        super(Rsource, self).__init__(nvim)

        self.matches = Matches()
        self._settings = dict()

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

    def _error(self, msg, error=''):
        """Output error in logs and in nvim"""

        msg_format = '[ncm-R] {}'
        msg_format += ': {}' if error else '{}'
        msg = msg_format.format(msg, error)

        LOGGER.error(msg)
        self.message('ERROR', msg)

    def _info(self, msg, error=''):  # pylint: disable=no-self-use
        """Output information in log only"""

        msg_format = '[ncm-R] {}'
        msg_format += ': {}' if error else '{}'
        msg = msg_format.format(msg, error)

        LOGGER.info(msg)
