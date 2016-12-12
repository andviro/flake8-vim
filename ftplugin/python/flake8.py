# coding: utf-8

SUBMODULES = ['mccabe', 'pycodestyle', 'autopep8', 'frosted', 'pies']

import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for module in SUBMODULES:
    module_dir = os.path.join(BASE_DIR, module)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)


from mccabe import McCabeChecker
from frosted.api import checker, _noqa_lines
from frosted import messages
import _ast
import pycodestyle as p8
from autopep8 import fix_file as pep8_fix, fix_lines as pep8_fix_lines, DEFAULT_INDENT_SIZE, continued_indentation as autopep8_c_i
from contextlib import contextmanager
from operator import attrgetter


@contextmanager
def patch_pep8():
    if autopep8_c_i in p8._checks['logical_line']:
        del p8._checks['logical_line'][autopep8_c_i]
        p8.register_check(p8.continued_indentation)
    try:
        yield
    finally:
        del p8._checks['logical_line'][p8.continued_indentation]
        p8.register_check(autopep8_c_i)


class Pep8Options():
    verbose = 0
    diff = False
    in_place = True
    recursive = False
    pep8_passes = 100
    max_line_length = 79
    line_range = None
    indent_size = DEFAULT_INDENT_SIZE
    ignore = ''
    select = ''
    aggressive = 0
    experimental = False
    hang_closing = False


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
        if not checker_fun:
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
        except Exception:
            pass

    result = filter(lambda e: _ignore_error(e, ignore), result)
    return sorted(result, key=lambda x: x['lnum'])


def mccabe(filename):
    with open(filename, "rU") as mod:
        code = mod.read()
        try:
            tree = compile(code, filename, "exec", _ast.PyCF_ONLY_AST)
        except Exception:
            return []

    complx = []
    McCabeChecker.max_complexity = MccabeOptions.complexity
    for lineno, offset, text, check in McCabeChecker(tree, filename).run():
        complx.append(dict(col=offset, lnum=lineno, text=text))

    return complx


def pep8(filename):
    with patch_pep8():
        style = PEP8 or _init_pep8()
        return style.input_file(filename)


def frosted(filename):
    codeString = open(filename, 'U').read() + '\n'
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
        w = checker.Checker(tree, filename, ignore_lines=_noqa_lines(codeString))
        for w in sorted(w.messages, key=attrgetter('lineno')):
            errors.append(dict(
                lnum=w.lineno,
                col=0,
                text=u'{0} {1}'.format(
                    flake_class_mapping.get(w.__class__, ''),
                    w.message.split(':', 2)[-1].strip()),
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

    PEP8 = p8.StyleGuide(reporter=_PEP8Report,
                         ignore=Pep8Options.ignore,
                         select=Pep8Options.select,
                         max_line_length=Pep8Options.max_line_length,
                         hang_closing=Pep8Options.hang_closing)
    return PEP8


def _ignore_error(e, ignore):
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True


if __name__ == '__main__':
    for r in run_checkers(__file__, checkers=['mccabe', 'frosted', 'pep8'], ignore=[]):
        print(r)
