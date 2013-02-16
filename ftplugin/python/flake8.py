import locale
locale.setlocale(locale.LC_CTYPE, "C")

from mccabe.mccabe import get_module_complexity
from pyflakes import checker
import _ast
from pep8 import pep8 as p8
from pep8.autopep8 import fix_file as pep8_fix
import vim


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


def fix_file(filename):
    pep8_fix(filename, Pep8Options)


def run_checkers(filename, checkers, ignore, select):

    result = []

    for c in checkers:

        checker_fun = globals().get(c)
        if not checker:
            continue

        try:
            for e in checker_fun(filename):
                e.update(
                    col=e.get('col') or 0,
                    text="%s [%s]" % (e.get('text', '')
                                      .strip(
                                      ).replace(
                                      "'", "\"").split('\n')[0], c),
                    filename=filename,
                    bufnr=0,
                )
                result.append(e)

        except SyntaxError, e:
            result.append(dict(
                lnum=e.lineno,
                col=e.offset or 0,
                text=e.args[0],
                filename=filename,
            ))
            break

        except Exception, e:
            print e, '!!!'
            assert True

    result = filter(lambda e: _ignore_error(e, select, ignore), result)
    return sorted(result, key=lambda x: x['lnum'])


def mccabe(filename):
    complexity = vim.eval('g:PyFlakeDefaultComplexity')
    return get_module_complexity(filename, min=complexity)


def pep8(filename):
    PEP8 or _init_pep8()
    style = PEP8['style']
    return style.input_file(filename)


def pyflakes(filename):
    codeString = file(filename, 'U').read() + '\n'
    errors = []
    tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    w = checker.Checker(tree, filename)
    w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
    for w in w.messages:
        errors.append(dict(
            lnum=w.lineno,
            col=0,
            text=w.message % w.message_args,
            type='E'
        ))
    return errors


PEP8 = dict()


def _init_pep8():

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

    PEP8['style'] = p8.StyleGuide(reporter=_PEP8Report)


def _ignore_error(e, select, ignore):
    for s in select:
        if e['text'].startswith(s):
            return True
    for i in ignore:
        if e['text'].startswith(i):
            return False
    return True

if __name__ == '__main__':
    for r in run_checkers(
        '/home/andrew/devel/vim/bundle/flake8-vim/ftplugin/python/flake8.py',
        checkers=['mccabe', 'pyflakes', 'pep8'], select=[],
            ignore=[]):
        print r
