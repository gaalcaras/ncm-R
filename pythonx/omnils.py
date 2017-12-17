# -*- coding: utf-8 -*-
"""
ncm-R: tools to convert omnils to NCM matches

by Gabriel Alcaras
"""

import re


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
            title = get_obj_title(info)
            pkg_name = '{' + pkg[0:8] + '}'
            menu = '{:10}'.format(pkg_name)
            menu += ' ' + title

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
        title = get_obj_title(info)
        match['menu'] = '{:10}'.format(pkg_name)
        match['menu'] += ' {:10}'.format(struct[0:10])
        match['menu'] += ' ' + title

    if struct == 'package':
        match['snippet'] = word + '::$1'
        match['menu'] = 'package ' + info

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
    :returns: list of arguments
    """
    if not info:
        return list()

    splits = re.split('\x08', info)
    args = splits[0]
    args = re.split('\t', args)
    args = [arg.replace('\x07', ' = ') for arg in args]

    return args


def get_obj_title(info=''):
    """Return object title based on omniline info

    :info: information from omni files
    :returns: function title
    """
    if not info:
        return list()

    obj_title = re.search(r'\x08(.*)\x05', info)

    if obj_title:
        return obj_title.group(1).strip()

    return ''


def to_pkg_matches(lines):
    """Transform package description lines from Nvim-R into list of NCM matches

    :lines: list of lines from a pack_descriptions file
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\t', line)

        if len(parts) >= 2:
            match = create_match(word=parts[0], info=parts[1],
                                 struct='package')

            if match:
                cm_list.append(match)

    return cm_list


def to_matches(lines):
    """Transform omni lists from Nvim-R into list of NCM matches

    :lines: list of lines from an omni list
    :returns: list of ncm matches
    """

    cm_list = list()

    for line in lines:
        parts = re.split('\x06', line)

        if len(parts) >= 5:
            match = create_match(word=parts[0], struct=parts[1], pkg=parts[3],
                                 info=parts[4])

            if match:
                cm_list.append(match)

    return cm_list
