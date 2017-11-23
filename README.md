:purple_heart: for [#rstats](https://twitter.com/search?q=%23rstats), my [favorite editor](https://neovim.io/) and [completion framework](https://github.com/roxma/nvim-completion-manager)

# R completion for Neovim Completion Manager

This vim plugin extends NCM with R completion. It relies on the excellent
[nvim-R](https://github.com/jalvesaq/Nvim-R) plugin to provide accurate
completion to your R code.

For now, ncm-R provides really basic features of completion:
+ objects from the global R environment
+ functions from currently loaded packages
+ packages inside `library()` and `require()`
+ arguments inside functions
+ expand syntax snippets when pressing Tab (if [UltiSnips](https://github.com/sirver/UltiSnips)
    is installed):
    + `dataframe` -> `dataframe$`
    + `function` -> `function(arg1, arg2, ...)` (only shows mandatory arguments)
    + `package` -> `package::`
    + `argument` -> `argument = DEFAULT_VALUE`

## Installation

Use your favorite plugin manager. For instance, with
[vim-plug](https://github.com/junegunn/vim-plug) :

```vim
Plug 'roxma/nvim-completion-manager'
Plug 'jalvesaq/Nvim-R', { 'for' : 'r' }
Plug 'gaalcaras/ncm-R', { 'for' : 'r' }

" Optional: for snippet support
Plug 'sirver/UltiSnips'
```
