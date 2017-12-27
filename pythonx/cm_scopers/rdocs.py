# -*- coding: utf-8 -*-
"""
Rmarkdown Scoper for Neovim Completion Manager

by Gabriel Alcaras
"""

import re
import copy
from cm import Base  # pylint: disable=E0401


class Scoper(Base):  # pylint: disable=too-few-public-methods

    """Scoper for RMarkdown"""

    scopes = ['rmd', 'rnoweb']

    def get_scope(self, ctx, src):
        """Identify scope"""

        scope = None
        cur_pos = self.get_pos(ctx['lnum'], ctx['col'], src)

        pat = re.compile(
            r'^((`{3})|(<<)) \s* (?(2)\{r)([^\n]*) \s* \n'
            r'(.*?)'
            r'^(?(3)@|\2) \s* (?:\n+|$)', re.M | re.X | re.S)

        groups = {4: 'rchunk', 5: 'r'}

        for chunk in pat.finditer(src):
            if chunk.start() > cur_pos:
                break

            for grp_nb, grp_scope in groups.items():
                group = chunk.group(grp_nb)
                start = chunk.start(grp_nb)

                if group and start <= cur_pos <= chunk.end(grp_nb):
                    scope = dict(src=group, pos=cur_pos-start,
                                 scope_offset=start, scope=grp_scope)

                    break

        return scope

    def sub_context(self, ctx, src):
        """Return context data about R chunks inside RMarkdown document"""

        scope = self.get_scope(ctx, src)

        if not scope:
            return None

        new_pos = scope['pos']
        new_src = scope['src']
        pos = 0

        for numline, line in enumerate(new_src.split("\n")):
            if pos < new_pos <= pos + len(line) + 1:
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
