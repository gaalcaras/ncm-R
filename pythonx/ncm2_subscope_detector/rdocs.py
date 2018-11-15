# -*- coding: utf-8 -*-
"""
Rmarkdown and Rnoweb Scoper for ncm2

by Gabriel Alcaras
"""

import re
import copy
from ncm2 import Ncm2Base, getLogger # pylint: disable=E0401

LOGGER = getLogger(__name__)


class SubscopeDetector(Ncm2Base):  # pylint: disable=too-few-public-methods

    """Scoper for RMarkdown and Rnoweb"""

    scope = ['rmd', 'rnoweb']

    def get_scope(self, lnum, ccol, src):
        """Identify scope"""

        scope = None
        cur_pos = self.lccol2pos(lnum, ccol, src)

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

    def detect(self, lnum, ccol, src):
        """Return context data about R chunks inside RMarkdown document"""

        LOGGER.info('[ncmR] subscope :: lnum: %s, ccol: %s, src: %s',
                    lnum, ccol, src)
        scope = self.get_scope(lnum, ccol, src)

        if not scope:
            return None

        new_pos = scope['pos']
        new_src = scope['src']
        pos = 0

        for numline, line in enumerate(new_src.split("\n")):
            if pos < new_pos <= pos + len(line) + 1:
                subctx = {}
                subctx['scope'] = scope['scope']
                subctx['scope_offset'] = scope['scope_offset']
                subctx['scope_len'] = len(new_src)

                subctx['lnum'] = numline+1
                subctx['col'] = new_pos - pos + 1

                lnum_col = self.pos2lccol(scope['scope_offset'], src)
                subctx['scope_lnum'] = lnum_col[0]
                subctx['scope_ccol'] = lnum_col[1]
                LOGGER.info('[ncmR] subscope :: subctx2: %s', subctx)
                return subctx

            pos += len(line) + 1

        return None
