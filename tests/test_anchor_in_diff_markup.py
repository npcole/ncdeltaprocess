r"""An anchor inside a diff command does not typeset.

``\hypertarget`` is a zero-width position marker, and the renderer used
to prepend it to a run's content BEFORE the diff wrapper went on, so it
ended up inside the wrapper: ``\added{\hypertarget{a}{} text}``.
hyperref's anchor machinery does not survive the argument of the
``changes`` package's commands -- ``\added`` gives "Undefined control
sequence" inside ``\@hyper@@anchor`` and ``\deleted`` "Bad space factor
(0)" -- whatever the anchor is named and whether or not its text is
empty.

That combination is not exotic: an anchored run inside a redline is what
every "jump to this change" link in a diff report is made of. One such
run made a whole document unbuildable.

Prepending the anchor AFTER the wrapper puts it at the same point in the
text stream, outside the fragile command, and incidentally puts the two
renderers in agreement -- the HTML side has always emitted the anchor
outside the diff span, because ``add_links`` is post-processing.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

from ncdeltaprocess import TranslatorQuillJS

ANCHOR = 'jump_id_1'

#: label -> the diff attribute value a run carries.
DIFF_VALUES = {'insertion': 'new', 'deletion': 'removed', 'edit': 'edited'}


def _ops(diff_value):
    return [{'insert': 'kept '},
            {'insert': 'changed run',
             'attributes': {'anchor': ANCHOR, 'quill_diff': diff_value}},
            {'insert': '.\n'}]


def _latex(ops):
    return TranslatorQuillJS(diff_mode=True).translate_to_latex(ops)


class TestTheAnchorIsOutsideTheDiffCommand(unittest.TestCase):

    def test_the_anchor_precedes_the_diff_command(self):
        for label, value in DIFF_VALUES.items():
            with self.subTest(change=label):
                latex = _latex(_ops(value))
                target = r'\hypertarget{' + ANCHOR + '}{}'
                self.assertIn(target, latex)
                command = re.search(r'\\(added|deleted|highlight|replaced)\{',
                                    latex)
                self.assertIsNotNone(command, latex)
                self.assertLess(
                    latex.index(target), command.start(),
                    f'the anchor is inside {command.group(1)!r}, which does '
                    f'not typeset:\n{latex}')

    def test_the_anchor_is_not_dropped(self):
        """Non-vacuity: moving it out must not mean losing it."""
        for label, value in DIFF_VALUES.items():
            with self.subTest(change=label):
                self.assertEqual(_latex(_ops(value)).count(r'\hypertarget'), 1)

    def test_an_anchor_without_diff_markup_still_prepends(self):
        ops = [{'insert': 'run', 'attributes': {'anchor': ANCHOR}},
               {'insert': '\n'}]
        self.assertTrue(_latex(ops).startswith(r'\hypertarget{' + ANCHOR + '}{}'))

    def test_the_renderers_agree_on_where_the_anchor_goes(self):
        """HTML has always put it outside the diff span."""
        ops = _ops('new')
        html = TranslatorQuillJS(diff_mode=True).translate_to_html(ops)
        self.assertLess(html.index(f'id="{ANCHOR}"'), html.index('<span'))


@unittest.skipIf(shutil.which('pdflatex') is None, 'pdflatex is not installed')
class TestItActuallyCompiles(unittest.TestCase):
    """The rule was derived from pdflatex; this is pdflatex saying so."""

    PREAMBLE = ('\\documentclass{article}\n'
                '\\usepackage[T1]{fontenc}\n'
                '\\usepackage{hyperref}\n'
                '\\usepackage{changes}\n'
                '\\begin{document}\n%s\n\\end{document}\n')

    def _compiles(self, body):
        with tempfile.TemporaryDirectory() as work:
            tex = os.path.join(work, 'doc.tex')
            with open(tex, 'w', encoding='utf-8') as handle:
                handle.write(self.PREAMBLE % body)
            proc = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                 f'-output-directory={work}', tex],
                capture_output=True, text=True, errors='replace', timeout=300)
            return proc.returncode == 0, proc.stdout

    def test_every_kind_of_change_compiles(self):
        for label, value in DIFF_VALUES.items():
            with self.subTest(change=label):
                body = _latex(_ops(value))
                ok, output = self._compiles(body)
                self.assertTrue(ok, f'{body}\n{output[-900:]}')

    def test_a_link_to_the_anchor_still_resolves(self):
        body = (_latex(_ops('new'))
                + '\n\n' + r'\hyperlink{' + ANCHOR + '}{jump}')
        ok, output = self._compiles(body)
        self.assertTrue(ok, f'{body}\n{output[-900:]}')

    def test_the_old_placement_really_did_not_compile(self):
        """Non-vacuity, against pdflatex itself."""
        for command in ('added', 'deleted'):
            with self.subTest(command=command):
                broken = ('\\%s{\\hypertarget{%s}{} text}'
                          % (command, ANCHOR))
                self.assertFalse(self._compiles(broken)[0],
                                 f'expected pdflatex to reject {broken}')


if __name__ == '__main__':
    unittest.main()
