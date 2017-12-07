# -*- coding: utf-8 -*-
"""
ncm-R: tools to filter matches

by Gabriel Alcaras
"""

import re


def arg(ncm_matches, func="", pipe=None):
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
            return [a for a in args[0] if '.data' not in a['word']]

        return args[0]

    return ['']


def struct(ncm_matches, strct=""):
    """Filter list of ncm matches based on their types (str() in R)

    :ncm_matches: list of matches (dictionaries)
    :strct: only show matches of given type
    :returns: filtered list of ncm matches
    """

    if not strct:
        return ncm_matches

    ncm_matches = [d for d in ncm_matches if d['struct'] == strct]

    return ncm_matches


def pkg(ncm_matches, pkgs=None):
    """Filter list of ncm matches with R packages

    :ncm_matches: list of matches
    :pkgs: only show matches from given R packages
    :returns: filtered list of ncm matches
    """

    if not pkgs:
        return ncm_matches

    res_matches = []
    packages = [pkgs] if isinstance(pkgs, str) else pkgs
    for pack in packages:
        pkg_matches = [d for d in ncm_matches if d['pkg'] == pack]
        res_matches.extend(pkg_matches)

    return res_matches


def word(ncm_matches, typed="", hide="", rm_typed=False):
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
