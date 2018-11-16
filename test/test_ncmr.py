# -*- coding: utf-8 -*-
"""
Testing ncm-R

by Gabriel Alcaras
"""

import sys

from neovim import attach

LISTEN = '/tmp/nvim-ncmr2'
try:
    NVIM = attach('socket', path=LISTEN)
except FileNotFoundError:
    print('Could not find NVIM process. Did you start a NVIM instance at {}'
          '?'.format(LISTEN))
    sys.exit()

# SPECIAL KEYS
DOWN = NVIM.replace_termcodes('<down>')
RETURN = NVIM.replace_termcodes('<return>')
CTRL_E = NVIM.replace_termcodes('<C-e>')

def send_rcmd(cmd):
    """Send cmd to R"""
    NVIM.command('call g:SendCmdToR("{}")'.format(cmd))

class TestCase: # pylint: disable=too-few-public-methods

    """Setup ncm-R test case"""

    def __init__(self, question='', buf=None):
        # RESET NVIM
        NVIM.feedkeys(CTRL_E) # Close popup menu if still open
        NVIM.command('stopinsert')
        NVIM.command('silent bwipeout!')
        NVIM.command('e! /tmp/test.R')

        # PREP BUFFER
        buf = [] if buf is None else buf
        buf = ['# {}'.format(question), *buf]
        nvim_buf = NVIM.current.buffer
        nvim_buf[:] = buf
        NVIM.feedkeys(DOWN)

        self._question = question

    def ask(self):
        """Prompt user to answer test question"""

        yes_opt = set(['yes', 'y', 'ye', ''])
        no_opt = set(['no', 'n'])

        while True:
            choice = input('{} [y/n] '.format(self._question)).lower()
            if choice in yes_opt:
                return True

            if choice in no_opt:
                sys.exit(0)

            print("Please respond with 'yes' or 'no'\n")


# ==== ERRORS ==== #
TEST = TestCase('Has ncm-R thrown an error?', ['li'])
NVIM.feedkeys('A')
TEST.ask()

NVIM.command("call StartR('R')")
send_rcmd("library('stringr')")

# ==== FUNCTION COMPLETION ==== #
TEST = TestCase('Is ncm-R suggesting mean?', ['mea'])
NVIM.feedkeys('A')
TEST.ask()

TEST3 = TestCase('Is ncm-R suggesting base::mean?', ['base::mea'])
NVIM.feedkeys('A')
TEST3.ask()

TEST = TestCase('Is ncm-R suggesting ONLY stringr functions?', ['stringr::'])
NVIM.feedkeys('A')
TEST.ask()

# ==== ARGUMENT COMPLETION ==== #
TEST = TestCase('Is ncm-R suggesting ONLY mean arguments?', ['mean('])
NVIM.feedkeys('A')
TEST.ask()

TEST = TestCase('Is ncm-R suggesting ONLY str_extract arguments?',
                ['stringr::str_extract('])
NVIM.feedkeys('A')
TEST.ask()

# ==== PACKAGE COMPLETION ==== #
TEST = TestCase('Is ncm-R suggesting packages?', ['library('])
NVIM.feedkeys('A')
TEST.ask()

# ==== DATASET COMPLETION ==== #
TEST = TestCase('Is ncm-R suggesting datasets?', ['data('])
NVIM.feedkeys('A')
TEST.ask()

# ==== OBJECT COMPLETION ==== #
TEST = TestCase('Is ncm-R suggesting sleep object?', ['sl'])
send_rcmd("data('sleep')")
NVIM.feedkeys('A')
TEST.ask()

TEST = TestCase('Is ncm-R suggesting sleep variables?', ['sleep$'])
NVIM.feedkeys('A')
TEST.ask()

# ==== PIPELINES ==== #
TEST = TestCase('Is ncm-R suggesting sleep variables and mean arguments?',
                ['sleep %>%', '  mean('])
NVIM.feedkeys(DOWN + 'A')
TEST.ask()

TEST = TestCase('Is ncm-R suggesting sleep variables and geom_point arguments?',
                ['sleep %>%', '  ggplot() +', '  geom_point('])
send_rcmd("library('ggplot2')")
NVIM.feedkeys('2' + DOWN + 'A')
TEST.ask()

# ==== IT'S  OVER ==== #
TEST = TestCase(r'Testing is over \o/')
TEST.ask()
