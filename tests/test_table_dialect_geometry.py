r"""Every table dialect emits a ``longtable`` its rows actually fit.

A ``longtable`` preamble fixes the row width for the whole table. A row
that emits more ``&``-separated slots than the preamble declares does
not render badly -- pdflatex refuses it outright with "Extra alignment
tab has been changed to \cr", one error per surplus slot, and writes no
PDF. A whole report is therefore the blast radius of one table.

Three dialects reach this renderer and a stored delta may carry any of
them, or several, because a document outlives the editor that wrote it:

* **Quill 2.x** (``modules/table_quill2.py``) -- ``{'table': <row-id>}``;
  no column definitions, no spans. Its ``TableBlock`` used to emit no
  alignment environment AT ALL, while its rows and cells still emitted
  ``&``, ``\\`` and ``\hline`` -- alignment material in open text, which
  cannot compile ("Misplaced alignment tab character &").
* **quill-better-table** (``modules/table_better_table.py``) --
  ``table-col`` definitions plus ``table-cell-line``.
* **quill-table-better** (``modules/table_better.py``) -- no column
  group at all; its columns come from the first row's cells, so a wider
  later row overran its own specification.
All three had each written ``len(self._columns) or 1`` as their column
count, independently, and all three were wrong the same way. They now
share ``block.plan_latex_table_columns``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

from ncdeltaprocess import TranslatorQuillJS

PDFLATEX = shutil.which('pdflatex')


def _quill2(row_id):
    ops = []
    for text in ('a', 'b'):
        ops += [{'insert': f'{text} ({row_id})'},
                {'insert': '\n', 'attributes': {'table': row_id}}]
    return ops


def _better_table():
    def cell(row, cid, text, cs=1, rs=1):
        line = {'rowspan': str(rs), 'colspan': str(cs), 'row': row, 'cell': cid}
        return [{'insert': text},
                {'insert': '\n', 'attributes': {
                    'table-cell-line': line, 'row': row,
                    'rowspan': str(rs), 'colspan': str(cs)}}]
    return ([{'insert': '\n\n', 'attributes': {'table-col': {'width': '100'}}}]
            + cell('1', '1', 'spanning header', cs=2)
            + cell('2', '1', 'tall', rs=2) + cell('2', '2', 'x')
            + cell('3', '1', 'y'))


def _table_better():
    def cell(row, cid, text, cs=1, rs=1):
        table_cell = {'data-row': row}
        if cs != 1:
            table_cell['colspan'] = str(cs)
        if rs != 1:
            table_cell['rowspan'] = str(rs)
        return [{'insert': text},
                {'insert': '\n', 'attributes': {'table-cell': table_cell,
                                                'table-cell-block': cid}}]
    return (cell('r1', 'c1', 'spanning header', cs=2)
            + cell('r2', 'c2', 'tall', rs=2) + cell('r2', 'c3', 'p')
            + cell('r3', 'c4', 'q'))



DIALECTS = {
    'quill2': _quill2('row-a') + _quill2('row-b'),
    'quill-better-table': _better_table(),
    'quill-table-better': _table_better(),
}

#: One delta holding all four, with prose between: a document may carry
#: more than one dialect, and the renderers must not run together.
MIXED = [{'insert': 'Prose before.\n'}]
for _name, _ops in DIALECTS.items():
    MIXED += _ops + [{'insert': f'After the {_name} table.\n'}]

#: Shapes where the declared width and the rows disagree unless the
#: table is measured on an occupancy grid.
GEOMETRY = {
    # Cells that outlived their column group: nothing declares a width.
    'no column group at all': (
        [{'insert': 'x'},
         {'insert': '\n', 'attributes': {'table-cell-line': {
             'rowspan': '1', 'colspan': '1', 'row': '1', 'cell': '1'},
             'row': '1', 'rowspan': '1', 'colspan': '1'}},
         {'insert': 'y'},
         {'insert': '\n', 'attributes': {'table-cell-line': {
             'rowspan': '1', 'colspan': '1', 'row': '1', 'cell': '2'},
             'row': '1', 'rowspan': '1', 'colspan': '1'}}], 2),
    # One declared column beneath two-cell rows.
    'column group narrower than the rows': (
        [{'insert': '\n', 'attributes': {'table-col': {'width': '100'}}}]
        + [{'insert': 'x'},
           {'insert': '\n', 'attributes': {'table-cell-line': {
               'rowspan': '1', 'colspan': '1', 'row': '1', 'cell': '1'},
               'row': '1', 'rowspan': '1', 'colspan': '1'}},
           {'insert': 'y'},
           {'insert': '\n', 'attributes': {'table-cell-line': {
               'rowspan': '1', 'colspan': '1', 'row': '1', 'cell': '2'},
               'row': '1', 'rowspan': '1', 'colspan': '1'}}], 2),
}


def _latex(ops):
    return TranslatorQuillJS(diff_mode=False).translate_to_latex(
        ops, heading_base_level=3)


def _declared_columns(latex):
    spec = latex.split(r'\begin{longtable}{', 1)[1].split('}\n', 1)[0]
    return spec.count('p{') + spec.count('}l') or spec.count('l')


def _widest_row(latex):
    """The most ``&``-separated slots any emitted row uses."""
    body = latex.split(r'\begin{longtable}', 1)[1]
    body = body.split(r'\end{longtable}', 1)[0]
    widest = 1
    for row in body.split('\\\\'):
        depth = slots = 0
        index = 0
        while index < len(row):
            char = row[index]
            if char == '\\':
                index += 2
                continue
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            elif char == '&' and depth == 0:
                slots += 1
            index += 1
        widest = max(widest, slots + 1)
    return widest


class TestNoRowOutrunsItsPreamble(unittest.TestCase):
    """The invariant itself, for every dialect."""

    def test_every_dialect(self):
        for name, ops in DIALECTS.items():
            with self.subTest(dialect=name):
                latex = _latex(ops)
                self.assertGreaterEqual(
                    _declared_columns(latex), _widest_row(latex),
                    f'{name}: a row emits more slots than the preamble '
                    f'declares, which pdflatex refuses:\n{latex}')

    def test_geometry_shapes(self):
        for name, (ops, expected) in GEOMETRY.items():
            with self.subTest(shape=name):
                self.assertEqual(_declared_columns(_latex(ops)), expected)


class TestAlignmentMaterialStaysInsideATable(unittest.TestCase):
    """``TableBlock`` used to emit ``&`` and ``\\hline`` into open text."""

    def test_every_dialect(self):
        for name, ops in DIALECTS.items():
            with self.subTest(dialect=name):
                latex = _latex(ops)
                self.assertIn(r'\begin{longtable}', latex)
                outside = (latex.split(r'\begin{longtable}')[0]
                           + latex.rsplit(r'\end{longtable}', 1)[1])
                self.assertNotIn('&', outside)
                self.assertNotIn(r'\hline', outside)


class TestSpansAreRendered(unittest.TestCase):
    """``colspan``/``rowspan`` reached the HTML and not the LaTeX."""

    def test_colspan_becomes_multicolumn(self):
        for name in ('quill-better-table', 'quill-table-better'):
            with self.subTest(dialect=name):
                self.assertIn(r'\multicolumn{2}', _latex(DIALECTS[name]))

    def test_rowspan_becomes_multirow(self):
        for name in ('quill-better-table', 'quill-table-better'):
            with self.subTest(dialect=name):
                self.assertIn(r'\multirow{2}{*}{', _latex(DIALECTS[name]))

    def test_a_covered_row_is_padded_into_its_column(self):
        """A covered position carries no cell of its own in the wire data,
        so without a filler slot the next row slides left under the span."""
        for name, tail in (('quill-better-table', 'y'),
                           ('quill-table-better', 'q')):
            with self.subTest(dialect=name):
                self.assertIn(f' & {tail}', _latex(DIALECTS[name]))


class TestOneDeltaMayHoldEveryDialect(unittest.TestCase):

    def test_each_table_is_opened_and_closed(self):
        latex = _latex(MIXED)
        self.assertEqual(latex.count(r'\begin{longtable}'), len(DIALECTS))
        self.assertEqual(latex.count(r'\end{longtable}'), len(DIALECTS))

    def test_the_prose_between_them_survives(self):
        """Non-vacuity: four empty tables would satisfy the count above."""
        latex = _latex(MIXED)
        self.assertIn('Prose before.', latex)
        self.assertIn('After the quill2 table.', latex)


@unittest.skipIf(PDFLATEX is None, 'pdflatex is not installed')
class TestEveryDialectCompiles(unittest.TestCase):
    """Rendering is not the standard; compiling is."""

    PREAMBLE = ('\\documentclass{article}\n'
                '\\usepackage[T1]{fontenc}\n'
                '\\usepackage{longtable}\n'
                # A rowspanning cell is wrapped in \\multirow.
                '\\usepackage{multirow}\n'
                '\\begin{document}\n%s\n\\end{document}\n')

    def compile_latex_body(self, body, label='document'):
        with tempfile.TemporaryDirectory() as work:
            tex = os.path.join(work, 'doc.tex')
            with open(tex, 'w', encoding='utf-8') as handle:
                handle.write(self.PREAMBLE % body)
            proc = subprocess.run(
                [PDFLATEX, '-interaction=nonstopmode', '-halt-on-error',
                 f'-output-directory={work}', tex],
                capture_output=True, text=True, errors='replace', timeout=300)
            if proc.returncode != 0:
                first = next((line for line in proc.stdout.splitlines()
                              if line.startswith('!')), '(no ! line)')
                self.fail(f'pdflatex rejected {label}: {first}\n{body}')

    def test_each_dialect(self):
        for name, ops in DIALECTS.items():
            with self.subTest(dialect=name):
                self.compile_latex_body(_latex(ops), label=name)

    def test_all_of_them_in_one_document(self):
        self.compile_latex_body(_latex(MIXED), label='every dialect')

    def test_the_geometry_shapes(self):
        for name, (ops, _expected) in GEOMETRY.items():
            with self.subTest(shape=name):
                self.compile_latex_body(_latex(ops), label=name)


if __name__ == '__main__':
    unittest.main()
