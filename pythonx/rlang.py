# -*- coding: utf-8 -*-
"""
ncm-R: tools to parse code

by Gabriel Alcaras
"""

import re


def get_pipe(buff, numline, numcol):
    """Check if completion happens inside a pipe, if so, return the piped
    data

    :buff: vim buffer
    :numline: line number
    :numcol: column number
    :returns: piped data
    """

    pipe = None
    r_pipe = re.compile(r'([\w_\.\$]+)\s?%>%')
    r_block = re.compile(r'<-')

    no_pipe = 0
    for numl in range(numline - 1, -1, -1):
        line = buff[numl]

        if numl == numline - 1:
            # If line is where the cursor is currently at
            line = line[0:numcol]
            r_pipeline = re.compile(r'%>%')
        else:
            r_pipeline = re.compile(r'(%>%|\)\s?\+|,)\s*$')

        if r_pipeline.search(line):
            # If line clearly continues data pipeline
            has_pipe = r_pipe.search(line)

            if has_pipe:
                pipe = has_pipe.group(1)
                break
        else:
            no_pipe += 1
            begin_block = r_block.match(line)

            # The line could be the last line of a pipeline,
            # go to next iteration to check previous line...
            if begin_block or no_pipe == 2:
                # Unless the line clearly begins a block or the line below this
                # one does not match a pipeline either
                break

    return pipe


def get_open_bracket_col(typed=''):
    """Find the column of the last unclosed bracket

    :typed: typed content
    :returns: position of last unclosed bracket
    """
    if not typed:
        return -1

    open_brackets = []
    inside_quotes = False
    quotes = ''

    for col, char in enumerate(typed):
        if char in ('"', "'") and typed[col - 1] != "\"":
            if not inside_quotes:
                quotes = char
                inside_quotes = True
            else:
                inside_quotes = False if char == quotes else True
            continue

        if char == '(':
            open_brackets.append(col)

        if char == ')':
            try:
                open_brackets.pop()
            except IndexError:
                return -1

    try:
        result = open_brackets.pop()
    except IndexError:
        result = -1

    return result


def get_function(buff, numline, numcol):
    """Return function and package name of current line

    :buff: vim buffer
    :numline: line number
    :numcol: column number
    :returns: [package_name, function_name]
    """

    result = list()
    r_func = re.compile((r'((?P<pkg>[\w\._]+)::)?' +
                         r'((?P<fnc>[\w\._]+)\()?[^\(^:]*$'))
    r_param = re.compile(r',\s*$')
    r_block = re.compile(r'<-')

    no_func = 0
    for numl in range(numline - 1, -1, -1):
        line = buff[numl]

        line = line[0:numcol - 1] if numl == numline - 1 else line

        open_bracket = get_open_bracket_col(line)

        if open_bracket == -1:
            if r_param.search(line):
                continue

            no_func += 1
            begin_block = r_block.match(line)

            # The line could be the last line of a list of arguments,
            # go to next iteration to check previous line...
            if begin_block or no_func == 2:
                # Unless the line clearly begins a block or the line below this
                # one does not match an argument either
                result = ['', '']
                break
        else:
            line = line[0:open_bracket + 1]

        func_match = re.search(r_func, line)
        func = func_match.group('fnc') if func_match else ''
        pkg = func_match.group('pkg') if func_match else ''

        if (pkg and numl == numline - 1) or func:
            result = [pkg, func]
            break

        if numl == 0 and not pkg and not func:
            result = ['', '']
            break

    return result


def get_option(typed=''):
    """Return option name when assigning its value"""

    pattern = re.search(r',\s?([\w\.]+)\s?=\s?"$', typed)

    if pattern:
        return pattern.group(1)

    return None
