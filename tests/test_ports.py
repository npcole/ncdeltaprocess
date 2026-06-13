"""Tests for the features ported from the ncquill-bundled ncdeltaprocess fork.

Covers:
* SoftBreakModule: ``{'insert': {'softbreak': True}}`` → ``<br>`` / ``\\\\``
* heading_base_level: offset applied to heading levels
* LaTeX longtable: tables render as longtable with p{...\\linewidth} cols
* Aligned LaTeX headings: align attr → flush envs + font-size cmd
* LaTeX hardening: pylatexenc encoder + bracket protection + diff markup
"""
import unittest

from ncdeltaprocess.delta_process import TranslatorQuillJS
from ncdeltaprocess.latex_line_render import LineRenderLaTeX


def _html(ops):
    return TranslatorQuillJS().translate_to_html(ops)


def _latex(ops):
    return TranslatorQuillJS().translate_to_latex(ops)


class TestSoftBreak(unittest.TestCase):
    """SoftBreakModule handles softbreak embeds inline."""

    def test_html_renders_br(self):
        ops = [
            {'insert': 'first'},
            {'insert': {'softbreak': True}},
            {'insert': 'second\n'},
        ]
        html = _html(ops)
        self.assertIn('first', html)
        self.assertIn('<br>', html)
        self.assertIn('second', html)
        # Single block — no second <p>
        self.assertEqual(html.count('<p>'), 1)

    def test_latex_renders_double_backslash(self):
        ops = [
            {'insert': 'first'},
            {'insert': {'softbreak': True}},
            {'insert': 'second\n'},
        ]
        latex = _latex(ops)
        self.assertIn('first', latex)
        self.assertIn('\\\\\n', latex)
        self.assertIn('second', latex)

    def test_softbreak_inside_heading(self):
        """Softbreak inside a heading block is preserved (e.g. for visually-broken titles)."""
        ops = [
            {'insert': 'TITLE LINE ONE'},
            {'insert': {'softbreak': True}},
            {'insert': 'TITLE LINE TWO'},
            {'insert': '\n', 'attributes': {'header': 1}},
        ]
        html = _html(ops)
        self.assertIn('<h1>', html)
        self.assertIn('<br>', html)
        self.assertEqual(html.count('<h1>'), 1)


class TestHeadingBaseLevel(unittest.TestCase):
    """heading_base_level offsets heading levels in both HTML and LaTeX."""

    HEADINGS_OPS = [
        {'insert': 'Top'},
        {'insert': '\n', 'attributes': {'header': 1}},
        {'insert': 'Sub'},
        {'insert': '\n', 'attributes': {'header': 2}},
    ]

    def test_html_default_no_offset(self):
        html = TranslatorQuillJS().translate_to_html(self.HEADINGS_OPS)
        self.assertIn('<h1>Top</h1>', html)
        self.assertIn('<h2>Sub</h2>', html)

    def test_html_offset_shifts_levels(self):
        html = TranslatorQuillJS().translate_to_html(
            self.HEADINGS_OPS, heading_base_level=2,
        )
        self.assertIn('<h3>Top</h3>', html)
        self.assertIn('<h4>Sub</h4>', html)

    def test_html_offset_clamps_at_h6(self):
        """Offsets that push past h6 clamp to h6."""
        html = TranslatorQuillJS().translate_to_html(
            self.HEADINGS_OPS, heading_base_level=10,
        )
        self.assertIn('<h6>Top</h6>', html)
        self.assertIn('<h6>Sub</h6>', html)

    def test_latex_offset_shifts_section_command(self):
        # offset=3 → h1 maps to \paragraph (level 4), h2 to \subparagraph (5)
        latex = TranslatorQuillJS().translate_to_latex(
            self.HEADINGS_OPS, heading_base_level=3,
        )
        self.assertIn(r'\paragraph{Top}', latex)
        self.assertIn(r'\subparagraph{Sub}', latex)

    def test_latex_default_uses_section(self):
        latex = TranslatorQuillJS().translate_to_latex(self.HEADINGS_OPS)
        self.assertIn(r'\section{Top}', latex)
        self.assertIn(r'\subsection{Sub}', latex)


class TestAlignedLatexHeadings(unittest.TestCase):
    """Headings with align use flush envs + font-size, not \\section."""

    def test_centered_heading_uses_center_env(self):
        ops = [
            {'insert': 'Title'},
            {'insert': '\n', 'attributes': {'header': 1, 'align': 'center'}},
        ]
        latex = _latex(ops)
        self.assertIn(r'\begin{center}', latex)
        self.assertIn(r'\end{center}', latex)
        # Aligned headings get font-size + bfseries, not \section
        self.assertIn(r'\Large\bfseries', latex)
        self.assertNotIn(r'\section{Title', latex)
        self.assertIn('Title', latex)

    def test_right_aligned_uses_flushright(self):
        ops = [
            {'insert': 'X'},
            {'insert': '\n', 'attributes': {'header': 2, 'align': 'right'}},
        ]
        latex = _latex(ops)
        self.assertIn(r'\begin{flushright}', latex)
        self.assertIn(r'\end{flushright}', latex)
        self.assertIn(r'\large\bfseries', latex)

    def test_left_aligned_uses_flushleft(self):
        ops = [
            {'insert': 'X'},
            {'insert': '\n', 'attributes': {'header': 3, 'align': 'left'}},
        ]
        latex = _latex(ops)
        self.assertIn(r'\begin{flushleft}', latex)
        self.assertIn(r'\end{flushleft}', latex)

    def test_unaligned_heading_still_uses_section(self):
        ops = [
            {'insert': 'X'},
            {'insert': '\n', 'attributes': {'header': 1}},
        ]
        latex = _latex(ops)
        self.assertIn(r'\section{X}', latex)
        self.assertNotIn(r'\begin{center}', latex)


class TestLatexLongtable(unittest.TestCase):
    """Better tables render as longtable with p{...\\linewidth} columns."""

    BASIC_TABLE_OPS = [
        {'insert': '\n', 'attributes': {'table-temporary': True}},
        {'insert': 'A'},
        {'insert': '\n', 'attributes': {
            'table-cell-block': 'cell-a',
            'table-cell': {'data-row': 'row-1'},
        }},
        {'insert': 'B'},
        {'insert': '\n', 'attributes': {
            'table-cell-block': 'cell-b',
            'table-cell': {'data-row': 'row-1'},
        }},
    ]

    def test_uses_longtable_not_tabular(self):
        latex = _latex(self.BASIC_TABLE_OPS)
        self.assertIn(r'\begin{longtable}', latex)
        self.assertIn(r'\end{longtable}', latex)
        self.assertNotIn(r'\begin{tabular}', latex)

    def test_columns_use_linewidth(self):
        latex = _latex(self.BASIC_TABLE_OPS)
        self.assertIn(r'\linewidth', latex)
        # p-column spec: p{0.NN\linewidth}
        self.assertIn(r'p{0.', latex)

    def test_ampersand_separates_cells(self):
        """Cell separator must appear between cells, not after the last."""
        latex = _latex(self.BASIC_TABLE_OPS)
        # Exactly one & between A and B (two cells, one separator)
        a_pos = latex.find('A')
        b_pos = latex.find('B')
        amp_pos = latex.find('&', a_pos)
        self.assertGreater(amp_pos, a_pos)
        self.assertLess(amp_pos, b_pos)

    def test_no_trailing_ampersand_before_row_end(self):
        """The cell after the last one should NOT have a trailing & before \\\\."""
        latex = _latex(self.BASIC_TABLE_OPS)
        # The row terminator is `\\` on its own line; nothing useful between
        # B's text and the row terminator should be '&'.
        between = latex.split('B', 1)[1].split('\\\\', 1)[0]
        self.assertNotIn('&', between)


class TestLatexBracketProtection(unittest.TestCase):
    """Square brackets in body text are wrapped to avoid LaTeX optional-arg confusion."""

    def test_brackets_escaped_in_text(self):
        ops = [
            {'insert': 'See [Figure 1] for details.\n'},
        ]
        latex = _latex(ops)
        self.assertIn('{[}Figure 1{]}', latex)
        self.assertNotIn(' [Figure 1] ', latex)

    def test_brackets_in_link_text_escaped(self):
        ops = [
            {'insert': '[click]', 'attributes': {'link': 'https://x.example/'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn('{[}click{]}', latex)


class TestLatexDiffMarkup(unittest.TestCase):
    """ncquill_diff / quill_diff attributes map to \\added / \\deleted / \\highlight."""

    def test_new_insert_uses_added(self):
        ops = [
            {'insert': 'added text', 'attributes': {'ncquill_diff': 'new'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn(r'\added{added text}', latex)

    def test_insert_alias_uses_added(self):
        ops = [
            {'insert': 'X', 'attributes': {'quill_diff': 'insert'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn(r'\added{X}', latex)

    def test_removed_uses_deleted(self):
        ops = [
            {'insert': 'gone', 'attributes': {'ncquill_diff': 'removed'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn(r'\deleted{gone}', latex)

    def test_delete_alias_uses_deleted(self):
        ops = [
            {'insert': 'X', 'attributes': {'quill_diff': 'delete'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn(r'\deleted{X}', latex)

    def test_edited_uses_highlight(self):
        ops = [
            {'insert': 'edited', 'attributes': {'ncquill_diff': 'edited'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertIn(r'\highlight{edited}', latex)

    def test_unknown_diff_value_ignored(self):
        ops = [
            {'insert': 'plain', 'attributes': {'ncquill_diff': 'something-else'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertNotIn(r'\added', latex)
        self.assertNotIn(r'\deleted', latex)
        self.assertNotIn(r'\highlight', latex)
        self.assertIn('plain', latex)

    def test_diff_wraps_inline_formatting(self):
        ops = [
            {'insert': 'bold add', 'attributes': {
                'bold': True, 'ncquill_diff': 'new',
            }},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        # \added wraps \textbf
        added_pos = latex.find(r'\added{')
        bold_pos = latex.find(r'\textbf{')
        self.assertGreater(added_pos, -1)
        self.assertGreater(bold_pos, -1)
        self.assertLess(added_pos, bold_pos)


class TestLatexEncoderExtras(unittest.TestCase):
    """Smart quotes / dashes / NBSP get LaTeX-encoded when pylatexenc is available."""

    @classmethod
    def setUpClass(cls):
        try:
            import pylatexenc  # noqa: F401
            cls.has_pylatexenc = True
        except ImportError:
            cls.has_pylatexenc = False

    def test_emdash(self):
        if not self.has_pylatexenc:
            self.skipTest('pylatexenc not installed')
        ops = [{'insert': 'a — b\n'}]
        latex = _latex(ops)
        self.assertIn(r'\textemdash', latex)
        self.assertNotIn('—', latex)

    def test_smart_quotes(self):
        if not self.has_pylatexenc:
            self.skipTest('pylatexenc not installed')
        ops = [{'insert': 'a “b” ‘c’\n'}]
        latex = _latex(ops)
        self.assertIn(r'\textquotedblleft', latex)
        self.assertIn(r'\textquotedblright', latex)
        self.assertIn(r'\textquoteleft', latex)
        self.assertIn(r'\textquoteright', latex)

    def test_nbsp_becomes_tilde(self):
        if not self.has_pylatexenc:
            self.skipTest('pylatexenc not installed')
        ops = [{'insert': 'a b\n'}]
        latex = _latex(ops)
        self.assertIn('~', latex)

    def test_bullet(self):
        if not self.has_pylatexenc:
            self.skipTest('pylatexenc not installed')
        ops = [{'insert': '• item\n'}]
        latex = _latex(ops)
        self.assertIn(r'\textbullet', latex)


class TestPortedFeaturesXss(unittest.TestCase):
    """Attack surface introduced by the ported features stays narrow."""

    def test_align_attribute_only_matches_allowlist(self):
        """An attacker-controlled align value can't inject LaTeX envs."""
        ops = [
            {'insert': 'X'},
            {'insert': '\n', 'attributes': {
                'header': 1,
                'align': 'center"} \\evil{',
            }},
        ]
        latex = _latex(ops)
        # The match statement falls through; no flush/center env emitted.
        self.assertNotIn(r'\begin{center', latex)
        self.assertNotIn(r'\evil', latex)
        # Falls back to a normal \section command.
        self.assertIn(r'\section{', latex)

    def test_align_attribute_html_allowlist(self):
        """An attacker-controlled align value can't inject CSS."""
        ops = [
            {'insert': 'X'},
            {'insert': '\n', 'attributes': {
                'header': 1,
                'align': '"><script>alert(1)</script>',
            }},
        ]
        html = _html(ops)
        self.assertNotIn('<script>', html)
        self.assertNotIn('text-align: "', html)

    def test_diff_attribute_only_matches_allowlist(self):
        """An attacker-controlled ncquill_diff value can't inject a LaTeX cmd."""
        ops = [
            {'insert': 'X', 'attributes': {'ncquill_diff': '} \\evil{'}},
            {'insert': '\n'},
        ]
        latex = _latex(ops)
        self.assertNotIn(r'\evil', latex)
        # Plain text only — no \added / \deleted / \highlight
        self.assertNotIn(r'\added', latex)
        self.assertNotIn(r'\deleted', latex)
        self.assertNotIn(r'\highlight', latex)

    def test_softbreak_does_not_interpolate_attributes(self):
        """Softbreak rendering ignores attributes, can't be tricked."""
        ops = [
            {'insert': 'a'},
            {'insert': {'softbreak': True},
             'attributes': {'evil': '"><script>alert(1)</script>'}},
            {'insert': 'b\n'},
        ]
        html = _html(ops)
        self.assertNotIn('<script>', html)
        self.assertEqual(html.count('<br>'), 1)


class TestLatexProcessorComposition(unittest.TestCase):
    """LaTeX text-run post-processors compose like HTML ones (smoke test)."""

    def test_extra_latex_processor_runs(self):
        ops = [{'insert': 'hi\n'}]
        t = TranslatorQuillJS()

        # Inject a one-shot LaTeX post-processor directly on the pipeline
        def wrap(node, text):
            return r'\WRAP{' + text + r'}'

        t._latex_text_post_processors.append(wrap)
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\WRAP{hi}', latex)


if __name__ == '__main__':
    unittest.main()
