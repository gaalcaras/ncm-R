if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm_r#proc = yarp#py3({
    \ 'module': 'ncm_r',
    \ 'on_load': { -> ncm2#set_ready(g:ncm_r#source)}
\ })

let g:ncm_r#source = extend(get(g:, 'ncm_r', {}), {
            \ 'name': 'ncmR',
            \ 'ready': 0,
            \ 'priority': 9,
            \ 'mark': 'R',
            \ 'scope': ['r'],
            \ 'subscope_enable': 1,
            \ 'word_pattern': '[\w_\.]+',
            \ 'complete_pattern': [
            \       '\$', '::', '"', "'",
            \       ',\s', '^\s', '\('
            \ ],
            \ 'on_complete': 'ncm_r#on_complete',
            \ 'on_warmup': 'ncm_r#on_warmup',
            \ }, 'keep')

function! ncm_r#init()
  call ncm2#register_source(g:ncm_r#source)
endfunction

function! ncm_r#on_warmup(ctx)
    call g:ncm_r#proc.jobstart()
endfunction

function! ncm_r#on_complete(ctx)
    call g:ncm_r#proc.try_notify('on_complete', a:ctx)
endfunction
