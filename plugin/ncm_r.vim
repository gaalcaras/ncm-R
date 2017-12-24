" """""""""""""""""""""""""""""""""""""""""""""""
" ncm-R: asynchronous R autocompletion for Neovim
"
" by Gabriel Alcaras
" """""""""""""""""""""""""""""""""""""""""""""""

" Tell Nvim-R ncm-R is loaded
let $NCM_R = 'TRUE'

let g:ncm_r_column1_length = get(g:, 'ncm_r_column1_length', 13)
let g:ncm_r_column2_length = get(g:, 'ncm_r_column2_length', 11)
