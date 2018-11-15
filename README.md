:purple_heart: for [#rstats](https://twitter.com/search?q=%23rstats), my [favorite editor](https://neovim.io/) and a nice [completion framework](https://github.com/ncm2/ncm2)

# Asynchronous R completion for Neovim and vim 8

[![R completion for Neovim and vim 8 with ncm-R](https://asciinema.org/a/lsy3CMrmrDAK0IW6ABtJD079n.png)](https://asciinema.org/a/lsy3CMrmrDAK0IW6ABtJD079n)

ncm-R provides asynchronous, as-you-type completion for the R language, as well
as R documents such as RMarkdown.

It relies on the great plugin
[nvim-R](https://github.com/jalvesaq/Nvim-R) to get the completion data and
extends 
[ncm2](https://github.com/ncm2/ncm2)
for the completion.

**Table of contents:**
<!-- vim-markdown-toc GFM -->

* [Features](#features)
  * [Completion](#completion)
  * [Snippets](#snippets)
  * [R Markdown and Rnoweb](#r-markdown-and-rnoweb)
* [Who should use this plugin?](#who-should-use-this-plugin)
* [Installation](#installation)
* [Usage](#usage)
  * [General behavior](#general-behavior)
  * [Pop-up menu configuration](#pop-up-menu-configuration)
  * [Getting the snippets to work](#getting-the-snippets-to-work)
* [Contributing to ncm-R](#contributing-to-ncm-r)
  * [Overview](#overview)
  * [Debugging](#debugging)
  * [Contributors](#contributors)

<!-- vim-markdown-toc -->

## Features

### Completion

+ **Objects** from the global R environment
+ **Functions** from loaded packages or from specific package with `package::`
+ **Packages** inside `library()` and `require()`
+ **Datasets** inside `data()`
+ **Arguments** inside functions
+ **Variables inside data transformation pipelines** (`%>%`) **and building ggplots** (`+`)

### Snippets

If [UltiSnips](https://github.com/sirver/UltiSnips) and its [ncm2
module](https://github.com/ncm2/ncm2-ultisnips) is installed, pressing
<kbd>Tab</kbd> after selecting a completion suggestion will **expand syntax
snippets**. Snippets in ncm-R are designed to help you save a few keystrokes by
writing some code for you. I find it particularly useful with function
arguments.

You can see when a snippet is available for a suggestion when a `[+]` appears
in the pop-up menu.

Here's a list of all available snippets:

+ `dataframe` -> `dataframe %>%|`
+ `function` -> `function([arg1], arg2)` (expands only arguments with no
  default value, you can then <kbd>Tab</kbd> to go to the next argument)
+ `package` -> `package::|`
+ `argument` (use <kbd>Tab</kbd> to go after the end of expanded text):
  + By default -> `argument = [DEFAULT_VALUE]`
  + If default value is inside quotes -> `argument = "[default]"`
  + If default value is a boolean, then use its negation. For instance, if
    `TRUE` by default then it will expand to `argument = [FALSE]`

`|` stands for the cursor position and `[]` shows the cursor selection after snippet
expansion.

### R Markdown and Rnoweb

+ R completion available in R code chunks
+ Completion for chunk options

## Who should use this plugin?

You'll probably enjoy ncm-R:

+ If you like how [RStudio](https://rstudio.com) does completion but won't use
any editor other than Neovim
+ If you use a lot of data pipelines (`%>%`)
+ If you want a "suggest as you type" completion behavior

It should be noted that [Nvim-R](https://github.com/jalvesaq/Nvim-R) already
comes with OmniCompletion. It's lightweight and it works well, but you need to
ask for completion (<kbd>\<C-x\>\<C-o\></kbd>) and it
doesn't support pipelines.

ncm-R is built on top of Nvim-R completion data to offer more features, while
remaining as fast and as lightweight as possible.

## Installation

Use your favorite plugin manager. For instance, with
[vim-plug](https://github.com/junegunn/vim-plug) :

```vim
Plug 'ncm2/ncm2'
Plug 'roxma/nvim-yarp'
Plug 'jalvesaq/Nvim-R'
Plug 'gaalcaras/ncm-R'

" Vim 8 only
if !has('nvim')
    Plug 'roxma/vim-hug-neovim-rpc'
endif

" Optional: for snippet support
Plug 'sirver/UltiSnips'
Plug 'ncm2/ncm2-ultisnips'

" Optional: better Rnoweb support (LaTeX completion)
Plug 'lervag/vimtex'
```

Please make sure that you fulfill all [ncm2
requirements](https://github.com/ncm2/ncm2#requirements),
especially if you use vim 8.

## Usage

### General behavior

When you open an R file, **first start an R session** with nvim-R (default
mapping is <kbd>\<localleader\>rf</kbd>, see `:help Nvim-R-use`).  That's because
completion suggestions only include objects from your global environment and
functions from loaded packages (although Nvim-R loads some packages by default,
see `:help R_start_libs`).

If you're familiar with completion in [RStudio](https://rstudio.com),
you will feel at home with ncm-R. For instance, you won't see suggestions for
your `data.frames` and their variables before you run the proper command in the
R console to load them in the global environment.  Likewise, you won't see
`dplyr` functions if you forgot to run `library(dplyr)` first.

### Pop-up menu configuration

The default pop-up menu follows a 3 column layout:

| Type      | Column 1    | Column 2                          | Column 3                   |
| ---       | ---         | ---                               | ---                        |
| Argument  | `argument`  | `= DEFAULT_VALUE`                 |                            |
| Dataset   | `{package}` | Type of dataset (e.g. `tibble`)   | Short dataset description  |
| Functions | `{package}` | `function`                        | Short function description |
| Package   | `package`   | Short package description         |                            |
| Variable  | `variable`  | Type of variable (e.g. `integer`) |                            |

The length of the two first columns can be changed in your `.vimrc`. Choosing
a value below the minimum length will remove the column altogether:

| Column    | Minimum length | Default length | Global variable          |
| ---       | ---            | ---            | ---                      |
| Column #1 | 7              | 13             | `g:ncm_r_column1_length` |
| Column #2 | 7              | 11             | `g:ncm_r_column2_length` |

Finally, if you don't want the columns to be aligned, you can disable all
column padding:

```vim
let g:ncm_r_column_layout = 0
```

### Getting the snippets to work

[ncm2-ultisnips](https://github.com/ncm2/ncm2-ultisnips) might not work out of
the box with your [UltiSnips](https://github.com/SirVer/ultisnips)
configuration. You can learn how to use <kbd>Enter</kbd> to expand snippets
[here](https://github.com/ncm2/ncm2-ultisnips#vimrc-example) or
[there](thttps://github.com/ncm2/ncm2-ultisnips) to use <kbd>Tab</kbd>.

## Contributing to ncm-R

### Overview

Nvim-R is in charge of generating and updating the completion data:

| Completion data | Stored in |
| --- | --- |
| objects in the Global Environment | `GlobalEnvList_*` file in the `g:rplugin_tmpdir` directory |
| loaded packages | `g:rplugin_loaded_libs` |
| objects from packages | `pack_descriptions` and `omnils_*` files in `g:rplugin_compldir` |

ncm-R then retrieves the completion data, parses the buffer and feeds candidate
matches to ncm2's API.  For more information, please check out [this section of
Nvim-R's
README](https://github.com/jalvesaq/Nvim-R#the-communication-between-r-and-either-vim-or-neovim)
and `:help ncm2-API`.

### Debugging

You can run `NVIM_PYTHON_LOG_FILE=/tmp/log NVIM_PYTHON_LOG_LEVEL=INFO nvim`
then look at `nvim.log_py3_ncm_r`. You can also `tail -f nvim.log_py3_*
| grep ncmR` to get only ncm-R messages.

### Contributors

Special thanks to [@jalvesaq](https://github.com/jalvesaq) for making several
improvements to Nvim-R's API.
