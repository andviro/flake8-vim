" Check python support
if !has('python') && !has('python3')
    echo "Error: PyFlake.vim required vim compiled with +python or +python3."
    finish
endif

let s:pycmd = has('python') && (!exists('g:PyFlakeForcePyVersion') || g:PyFlakeForcePyVersion != 3) ? ':py' : ':py3'
" This is the last sign used, so that we can remove them individually.
let s:last_sign = 1

if !exists('g:PyFlakeRangeCommand')
    let g:PyFlakeRangeCommand = 'Q'
endif

if !exists('b:PyFlake_initialized')
    let b:PyFlake_initialized = 1

    au BufWritePost <buffer> call flake8#on_write()
    au CursorHold <buffer> call flake8#get_message()
    au CursorMoved <buffer> call flake8#get_message()
    
    " Commands
    command! -buffer PyFlakeToggle :let b:PyFlake_disabled = exists('b:PyFlake_disabled') ? b:PyFlake_disabled ? 0 : 1 : 1
    command! -buffer PyFlake :call flake8#run()
    command! -buffer -range=% PyFlakeAuto :call flake8#auto(<line1>,<line2>)

    " Keymaps
    if g:PyFlakeRangeCommand != ''
        exec 'vnoremap <buffer> <silent> ' . g:PyFlakeRangeCommand . ' :PyFlakeAuto<CR>'
    endif

    let b:showing_message = 0
    
    " Signs definition
    sign define W text=WW texthl=Todo
    sign define C text=CC texthl=Comment
    sign define R text=RR texthl=Visual
    sign define E text=EE texthl=Error
endif

 "Check for flake8 plugin is loaded
if exists("g:PyFlakeDirectory")
    finish
endif

if !exists('g:PyFlakeOnWrite')
    let g:PyFlakeOnWrite = 1
endif

" Init variables
let g:PyFlakeDirectory = expand('<sfile>:p:h')

if !exists('g:PyFlakeCheckers')
    let g:PyFlakeCheckers = 'pep8,mccabe,frosted'
endif
if !exists('g:PyFlakeDefaultComplexity')
    let g:PyFlakeDefaultComplexity=10
endif
if !exists('g:PyFlakeDisabledMessages')
    let g:PyFlakeDisabledMessages = 'E501'
endif
if !exists('g:PyFlakeCWindow')
    let g:PyFlakeCWindow = 6
endif
if !exists('g:PyFlakeSigns')
    let g:PyFlakeSigns = 1
endif
if !exists('g:PyFlakeSignStart')
    " What is the first sign id that we should use. This is usefull when
    " there are multiple plugins intalled that use the sign gutter
    let g:PyFlakeSignStart = 1
endif
if !exists('g:PyFlakeAggressive')
    let g:PyFlakeAggressive = 0
endif
if !exists('g:PyFlakeMaxLineLength')
    let g:PyFlakeMaxLineLength = 100
endif
if !exists('g:PyFlakeHangClosing')
    let g:PyFlakeHangClosing = 0
endif
if !exists('g:PyFlakeLineIndentGlitch')
    let g:PyFlakeLineIndentGlitch = 1
endif

function! flake8#on_write()
    if !g:PyFlakeOnWrite || exists("b:PyFlake_disabled") && b:PyFlake_disabled
        return
    endif
    call flake8#check()
endfunction

function! flake8#run()
    if &modifiable && &modified
        write
    endif
    call flake8#check()
endfun

function! flake8#check()
    exec s:pycmd ' flake8_check()'
    let s:matchDict = {}
    for err in g:qf_list
        let s:matchDict[err.lnum] = err.text
    endfor
    call setqflist(g:qf_list, 'r')

    " Place signs
    if g:PyFlakeSigns
        call flake8#place_signs()
    endif

    " Open cwindow
    if g:PyFlakeCWindow
        cclose
        if len(g:qf_list)
            let l:winsize = len(g:qf_list) > g:PyFlakeCWindow ? g:PyFlakeCWindow : len(g:qf_list)
            exec 'botright ' . l:winsize . 'cwindow'
        endif
    endif
endfunction

function! flake8#auto(l1, l2) "{{{
    cclose
    while s:last_sign >= g:PyFlakeSignStart
        execute "sign unplace" s:last_sign
        let s:last_sign -= 1
    endwhile
    let s:matchDict = {}
    call setqflist([])

exec s:pycmd . ' << EOF'
start, end = int(vim.eval('a:l1'))-1, int(vim.eval('a:l2'))
enc = vim.eval('&enc')
lines = fix_lines(list(unicode(x, enc, 'replace') for x in vim.current.buffer[start:end])).splitlines()
res = [ln.encode(enc, 'replace') for ln in lines]
vim.current.buffer[start:end] = res
EOF
endfunction "}}}

function! flake8#place_signs()
    " first remove previous inserted signs. Removing them by id instead of
    " unplace *, so that this can live in peace with other plugins.
    while s:last_sign >= g:PyFlakeSignStart
        execute "sign unplace" s:last_sign
        let s:last_sign -= 1
    endwhile

    "now we place one sign for every quickfix line
    let s:last_sign = g:PyFlakeSignStart - 1
    for item in getqflist()
        let s:last_sign += 1
        execute(':sign place '.s:last_sign.' name='.l:item.type.' line='.l:item.lnum.' buffer='.l:item.bufnr)
    endfor
endfunction

" keep track of whether or not we are showing a message
" WideMsg() prints [long] message up to (&columns-1) length
" guaranteed without "Press Enter" prompt.
function! flake8#wide_msg(msg)
    let x=&ruler | let y=&showcmd
    set noruler noshowcmd
    redraw
    echo strpart(a:msg, 0, &columns-1)
    let &ruler=x | let &showcmd=y
endfun


function! flake8#get_message()
    let s:cursorPos = getpos(".")

    " Bail if RunPyflakes hasn't been called yet.
    if !exists('s:matchDict')
        return
    endif

    " if there's a message for the line the cursor is currently on, echo
    " it to the console
    if has_key(s:matchDict, s:cursorPos[1])
        let s:pyflakesMatch = get(s:matchDict, s:cursorPos[1])
        call flake8#wide_msg(s:pyflakesMatch)
        let b:showing_message = 1
        return
    endif

    " otherwise, if we're showing a message, clear it
    if b:showing_message == 1
        echo
        let b:showing_message = 0
    endif
endfunction

function! flake8#force_py_version(version)
    let ver = a:version == 3 ? '3' : ''
    let s:pycmd = ':py' . ver
    if !py{ver}eval('"flake8_check" in dir()')
      call s:init_py_modules()
    endif
endfunction "}}}

function! s:init_py_modules()
exec s:pycmd . ' << EOF'

import sys
import json
import vim

if sys.version_info >= (3,):
    def unicode(str, *args):
        return str

sys.path.insert(0, vim.eval("g:PyFlakeDirectory"))
from flake8 import run_checkers, fix_lines, Pep8Options, MccabeOptions

def flake8_check():
    checkers=vim.eval('g:PyFlakeCheckers').split(',')
    ignore=vim.eval('g:PyFlakeDisabledMessages').split(',')
    MccabeOptions.complexity=int(vim.eval('g:PyFlakeDefaultComplexity'))
    Pep8Options.max_line_length=int(vim.eval('g:PyFlakeMaxLineLength'))
    Pep8Options.aggressive=int(vim.eval('g:PyFlakeAggressive'))
    Pep8Options.hang_closing=int(vim.eval('g:PyFlakeHangClosing'))
    filename=vim.current.buffer.name
    parse_result(run_checkers(filename, checkers, ignore))

def parse_result(result):
    vim.command('let g:qf_list = {0}'.format(json.dumps(result, ensure_ascii=False)))

EOF
endfunction

call s:init_py_modules()
