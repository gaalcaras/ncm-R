:purple_heart: for [#rstats](https://twitter.com/search?q=%23rstats), my [favorite editor](https://neovim.io/) and a nice [completion framework](https://github.com/roxma/nvim-completion-manager)

# Asynchronous R completion for Neovim and vim 8

![fullscreen screencast](https://user-images.githubusercontent.com/6551953/33690893-e896c35e-dae5-11e7-973d-cc1bffed1fcf.gif)

ncm-R extends the
[nvim-completion-manager](https://github.com/roxma/nvim-completion-manager)
(NCM) framework to provide asynchronous completion for the R language. It relies on the great plugin
[nvim-R](https://github.com/jalvesaq/Nvim-R) to get the completion data.

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
* [Contributing to ncm-R](#contributing-to-ncm-r)
  * [Overview](#overview)
  * [Debugging](#debugging)

<!-- vim-markdown-toc -->

## Features

### Completion

**Objects** from the global R environment :

![variables](https://user-images.githubusercontent.com/6551953/33718172-ce45f746-db5c-11e7-878f-818f5a7059b3.gif)

**Functions** from loaded packages or from specific package with `package::`:

![functions](https://user-images.githubusercontent.com/6551953/33718180-d4510ff4-db5c-11e7-9536-8e8b52f9630f.gif)

**Packages** inside `library()` and `require()`:

![library](https://user-images.githubusercontent.com/6551953/33718181-d47e22dc-db5c-11e7-9768-385b1c1558fe.gif)

**Datasets** inside `data()`:

![data](https://user-images.githubusercontent.com/6551953/33718183-d49b9f06-db5c-11e7-8c97-a5a1793907a3.gif)

**Arguments** inside functions:

![arguments](https://user-images.githubusercontent.com/6551953/33718185-d4b86816-db5c-11e7-8db8-28df7a95d456.gif)

**Variables inside data transformation pipelines** (`%>%`) **and building ggplots** (`+`):

![pipeline](https://user-images.githubusercontent.com/6551953/33718382-76ee990c-db5d-11e7-9a84-89e790c9e577.gif)

### Snippets

If [UltiSnips](https://github.com/sirver/UltiSnips) is installed, pressing
<kbd>Tab</kbd> after selecting a completion suggestion will **expand syntax
snippets**:

+ `dataframe` -> `dataframe %>%`
+ `function` -> `function(arg1, arg2, ...)` (expands only arguments with no
  default value)
+ `package` -> `package::`
+ `argument` -> `argument = DEFAULT_VALUE`

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
Plug 'roxma/nvim-completion-manager'
Plug 'jalvesaq/Nvim-R'
Plug 'gaalcaras/ncm-R'

" Vim 8 only
if !has('nvim')
    Plug 'roxma/vim-hug-neovim-rpc'
endif

" Optional: for snippet support
Plug 'sirver/UltiSnips'

" Optional: better Rnoweb support (LaTeX completion)
Plug 'lervag/vimtex'
```

Please make sure that you fulfill all [NCM
requirements](https://github.com/roxma/nvim-completion-manager#requirements),
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

## Contributing to ncm-R

### Overview

Nvim-R is in charge of generating and updating the completion data:

| Completion data | Stored in |
| --- | --- |
| objects in the Global Environment | `GlobalEnvList_*` file in the `g:rplugin_tmpdir` directory |
| loaded packages | `g:rplugin_loaded_libs` |
| objects from packages | `pack_descriptions` and `omnils_*` files in `g:rplugin_compldir` |

ncm-R then retrieves the completion data, parses the buffer and feeds candidate
matches to NCM's API.  For more information, please check out [this section of
Nvim-R's
README](https://github.com/jalvesaq/Nvim-R#the-communication-between-r-and-either-vim-or-neovim)
and `:help NCM-API`.

Special thanks to @jalvesaq for making several improvements to Nvim-R's API.

### Debugging

You can run `NVIM_PYTHON_LOG_FILE=nvim.log NVIM_PYTHON_LOG_LEVEL=INFO nvim`
then look at `nvim.log_py3_cm_core`. You can also `tail -f nvim.log_py3_cm_core
| grep ncm-R` to get only ncm-R messages.
