if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm_rchunk#proc = yarp#py3({
    \ 'module': 'ncm_rchunk',
\ })

let g:ncm_rchunk#source = extend(get(g:, 'ncm_rchunk', {}), {
            \ 'name': 'Rchunk',
            \ 'priority': 9,
            \ 'mark': 'Rchunk',
            \ 'scope': ['rchunk'],
            \ 'subscope_enable': 1,
            \ 'word_pattern': '[\w_\.]*',
            \ 'complete_pattern': [',\s', '=\s"'],
            \ 'on_complete': 'ncm_rchunk#on_complete',
            \ }, 'keep')

function! ncm_rchunk#init()
  call ncm2#register_source(g:ncm_rchunk#source)
endfunction

function! ncm_rchunk#on_complete(ctx)
  call g:ncm_rchunk#proc.try_notify('on_complete', a:ctx)
endfunction
