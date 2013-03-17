# coding: utf-8

from mccabe.mccabe import get_module_complexity
from pyflakes import checker, messages
import _ast
from pep8 import pep8 as p8
from pep8.autopep8 import fix_file as pep8_fix, fix_lines as pep8_fix_lines
import os


class Pep8Options():
    verbose = 0
    diff = False
    in_place = True
    recursive = False
    pep8_passes = 100
    max_line_length = 79
    ignore = ''
    select = ''
    aggressive = False


class MccabeOptions():
    complexity = 10

flake_code_mapping = {
    'W402': (messages.UnusedImport,),
    'W403': (messages.ImportShadowedByLoopVar,),
    'W404': (messages.ImportStarUsed,),
    'W405': (messages.LateFutureImport,),
    'W801': (messages.RedefinedWhileUnused,
             messages.RedefinedInListComp,),
    'W802': (messages.UndefinedName,),
    'W803': (messages.UndefinedExport,),
    'W804': (messages.UndefinedLocal,
             messages.UnusedVariable,),
    'W805': (messages.DuplicateArgument,),
    'W806': (messages.Redefined,),
}

flake_class_mapping = dict(
    (k, c) for (c, v) in flake_code_mapping.items() for k in v)


def fix_file(filename):
    pep8_fix(filename, Pep8Options)


def fix_lines(lines):
    return pep8_fix_lines(lines, Pep8Options)


def run_checkers(filename, checkers, ignore):

    result = []

    for c in checkers:

        checker_fun = globals().get(c)
        if not checker:
            continue

        try:
            for e in checker_fun(filename):
                e.update(
                    col=e.get('col') or 0,
                    text="{0} [{1}]".format(
                        e.get('text', '').strip(
                        ).replace("'", "\"").splitlines()[0],
                        c),
                    filename=os.path.normpath(filename),
                    type=e.get('type') or 'W',
                    bufnr=0,
                )
                result.append(e)
        except:
            pass

    result = filter(lambda e: _ignore_error(e, ignore), result)
    return sorted(result, key=lambda x: x['lnum'])


def mccabe(filename):
    return get_module_complexity(filename, min=MccabeOptions.complexity)


def pep8(filename):
    style = PEP8 or _init_pep8()
    return style.input_file(filename)


def pyflakes(filename):
    codeString = file(filename, 'U').read() + '\n'
    errors = []
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError as e:
        errors.append(dict(
            lnum=e.lineno or 0,
            col=e.offset or 0,
            text=getattr(e, 'msg', None) or str(e),
            type='E'
        ))
    else:
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        for w in w.messages:
            errors.append(dict(
                lnum=w.lineno,
                col=0,
                text=u'{0} {1}'.format(
                    flake_class_mapping.get(w.__class__, ''),
                    w.message % w.message_args),
                type='E'
            ))
    return errors


PEP8 = None


def _init_pep8():
    global PEP8

    class _PEP8Report(p8.BaseReport):

        def init_file(self, filename, lines, expected, line_offset):
            super(_PEP8Report, self).init_file(
                filename, lines, expected, line_offset)
            self.errors = []

        def error(self, line_number, offset, text, check):
            code = super(_PEP8Report, self).error(
                line_number, offset, text, check)

            self.errors.append(dict(
                text=text,
                type=code,
                col=offset + 1,
                lnum=line_number,
            ))

        def get_file_results(self):
            return self.errors

    PEP8 = p8.StyleGuide(reporter=_PEP8Report)
    return PEP8


def _ignore_error(e, ignore):
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True

if __name__ == '__main__':
    for r in run_checkers(
        '/home/andrew/devel/vim/bundle/flake8-vim/ftplugin/python/flake8.py',
            checkers=['mccabe', 'pyflakes', 'pep8'], ignore=[]):
        print r
