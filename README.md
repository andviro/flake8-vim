# Flake8-vim: pyflakes, pep8 and mcabe checker for Vim

Flake8-vim is a Vim plugin that checks python sources for errors. It's based on
_pylint-mode_ plugin by Kirill Klenov.

## Installation

Copy plugin folders into your .vim directory. Alternatively use _vundle_
package manager for Vim and run command:

    BundleInstall andviro/flake8-vim

## Configuration

By default python source code is checked with pyflakes, pep8 and mccabe code
complexity utility. The following options can be configured through global
variables in .vimrc:

Auto-check file for errors on write:

    let g:PyFlakeOnWrite = 1

List of checkers used:

    let g:PyFlakeCheckers = 'pep8,mccabe,pyflakes'
    
Default maximum complexity for mccabe:

    let g:PyFlakeDefaultComplexity=10
    
List of disabled pep8 warnings and errors:

    let g:PyFlakeDisabledMessages = 'E501'

Default height of quickfix window:

    let g:PyFlakeCWindow = 6 
    
Whether to place signs or not:

    let g:PyFlakeSigns = 1 
    
## Commands

Disable/enable automatic checking of current file

    :PyFlakeToggle
    
Run checks for current file

    :PyFlake
    
Auto-fix pep8 errors for current file

    :PyFlakeAuto

## Author

Andrew Rodionoff (@andviro)
