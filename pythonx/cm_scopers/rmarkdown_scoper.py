# -*- coding: utf-8 -*-
"""
Rmarkdown Scoper for Neovim Completion Manager

by Gabriel Alcaras
"""

import re
import copy
from cm import Base, getLogger  # pylint: disable=E0401

LOGGER = getLogger(__name__)


class Scoper(Base):  # pylint: disable=too-few-public-methods

    """Scoper for RMarkdown"""

    scopes = ['rmd']

    def sub_context(self, ctx, src):
        """Return context data about R chunks inside RMarkdown document"""

        scope = None
        pos = self.get_pos(ctx['lnum'], ctx['col'], src)

        pat = re.compile(
            r'^`{3} \s* \{r([^\}^\n]*)\} \s* \n'
            r'(.+?)'
            r'^`{3} \s* $', re.M | re.X | re.S)

        for chunk in pat.finditer(src):
            if chunk.start() > pos:
                break

            if chunk.group(2) and chunk.start(2) <= pos and chunk.end(2) > pos:
                scope = dict(src=chunk.group(2),
                             pos=pos-chunk.start(2),
                             scope_offset=chunk.start(2),
                             scope='r')
                break

        if not scope:
            return None

        new_pos = scope['pos']
        new_src = scope['src']
        pos = 0

        for numline, line in enumerate(new_src.split("\n")):
            if (pos <= new_pos) and (pos + len(line) + 1 > new_pos):
                new_ctx = copy.deepcopy(ctx)
                new_ctx['scope'] = scope['scope']
                new_ctx['lnum'] = numline + 1
                new_ctx['col'] = new_pos - pos + 1
                new_ctx['scope_offset'] = scope['scope_offset']
                new_ctx['scope_len'] = len(new_src)

                lnum_col = self.get_lnum_col(scope['scope_offset'], src)
                new_ctx['scope_lnum'] = lnum_col[0]
                new_ctx['scope_col'] = lnum_col[1]
                return new_ctx
            else:
                pos += len(line) + 1

        return None
