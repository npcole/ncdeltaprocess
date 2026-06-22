"""Tests for run-fragmented inline-style merging in LaTeX output.

A Quill delta often splits a styled phrase across several ops (e.g.
"ex post facto" as three underlined runs with plain spaces between). Rendered
naively that gives ``\\uline{ex} \\uline{post} \\uline{facto}`` — choppy
per-word underlining with the inter-word spaces left outside the rule.
``translate_to_latex`` folds such neighbours back into one continuous run via
``merge_adjacent_inline_styles``.

Also pins that underline now uses ``\\uline`` (ulem — fixed depth, line-break
friendly) rather than ``\\underline`` (per-word height, margin overflow).
"""
import unittest

from ncdeltaprocess import TranslatorQuillJS
from ncdeltaprocess.latex_line_render import merge_adjacent_inline_styles as merge


class TestMergeFunction(unittest.TestCase):
    def test_merges_run_fragmented_underline(self):
        self.assertEqual(merge(r'a \uline{ex} \uline{post} \uline{facto} law'),
                         r'a \uline{ex post facto} law')

    def test_preserves_nonbreaking_tie(self):
        self.assertEqual(merge(r'\uline{ex}~\uline{post}~\uline{facto}'),
                         r'\uline{ex~post~facto}')

    def test_other_styles(self):
        self.assertEqual(merge(r'\textbf{Mr} \textbf{Smith}'), r'\textbf{Mr Smith}')
        self.assertEqual(merge(r'\emph{a} \emph{b}'), r'\emph{a b}')

    def test_does_not_merge_different_styles(self):
        self.assertEqual(merge(r'\emph{a} \uline{b}'), r'\emph{a} \uline{b}')

    def test_does_not_merge_across_plain_text(self):
        self.assertEqual(merge(r'\uline{a} and \uline{b}'), r'\uline{a} and \uline{b}')

    def test_leaves_nested_untouched(self):
        self.assertEqual(merge(r'\uline{\textbf{x}} \uline{y}'),
                         r'\uline{\textbf{x}} \uline{y}')

    def test_empty(self):
        self.assertEqual(merge(''), '')
        self.assertIsNone(merge(None))


class TestTranslatorIntegration(unittest.TestCase):
    def test_underline_uses_uline(self):
        ops = [{'attributes': {'underline': True}, 'insert': 'word'},
               {'insert': '\n'}]
        latex = TranslatorQuillJS().translate_to_latex(ops)
        self.assertIn(r'\uline{word}', latex)
        self.assertNotIn(r'\underline{', latex)

    def test_fragmented_phrase_merges_end_to_end(self):
        ops = [
            {'insert': 'No bill of attainder, '},
            {'attributes': {'underline': True}, 'insert': 'ex'},
            {'insert': ' '},
            {'attributes': {'underline': True}, 'insert': 'post'},
            {'insert': ' '},
            {'attributes': {'underline': True}, 'insert': 'facto'},
            {'insert': ' law.\n'},
        ]
        latex = TranslatorQuillJS().translate_to_latex(ops)
        self.assertIn(r'\uline{ex post facto}', latex)
        self.assertNotIn(r'\uline{ex} \uline{post}', latex)


from ncdeltaprocess.latex_line_render import (  # noqa: E402
    strip_empty_diff_commands as strip_empty,
    merge_adjacent_diff_commands as merge_diff,
    pair_adjacent_diff_replacements as pair_repl,
)

H = r'\hspace{0pt}'


class TestStripEmptyDiffCommands(unittest.TestCase):
    """Empty change markers render nothing but each is still a changes-package
    call — strip them."""

    def test_strips_empty_added_and_deleted(self):
        self.assertEqual(strip_empty(r'\added{}' + H + r'\deleted{}' + H), '')

    def test_keeps_non_empty(self):
        s = r'\added{x}' + H
        self.assertEqual(strip_empty(s), s)

    def test_strips_empty_between_real(self):
        self.assertEqual(strip_empty(r'a\added{}' + H + 'b'), 'ab')

    def test_empty_inputs(self):
        self.assertEqual(strip_empty(''), '')
        self.assertIsNone(strip_empty(None))


class TestMergeAdjacentDiffCommands(unittest.TestCase):
    """Consecutive same-status diff commands fold into one (empties stripped);
    different statuses and nested-brace operands are left alone."""

    def test_folds_two_added(self):
        self.assertEqual(
            merge_diff(r'\added{A}' + H + r'\added{B}' + H), r'\added{AB}' + H)

    def test_folds_run_of_three_with_empty(self):
        self.assertEqual(
            merge_diff(r'\added{A}' + H + r'\added{}' + H + r'\added{B}' + H),
            r'\added{AB}' + H)

    def test_folds_two_deleted(self):
        self.assertEqual(
            merge_diff(r'\deleted{A}' + H + r'\deleted{B}' + H),
            r'\deleted{AB}' + H)

    def test_leaves_nested_brace_operand(self):
        s = r'\added{\textbf{x}}' + H + r'\added{y}' + H
        self.assertEqual(merge_diff(s), s)

    def test_empty_inputs(self):
        self.assertEqual(merge_diff(''), '')
        self.assertIsNone(merge_diff(None))


class TestPairAdjacentDiffReplacements(unittest.TestCase):
    """An added run immediately followed by a deleted run (an insert-first
    replacement) folds into a single \\replaced{new}{old}."""

    def test_pairs_added_then_deleted(self):
        self.assertEqual(
            pair_repl(r'\added{new}' + H + r'\deleted{old}' + H),
            r'\replaced{new}{old}' + H)

    def test_does_not_pair_deleted_then_added(self):
        s = r'\deleted{old}' + H + r'\added{new}' + H
        self.assertEqual(pair_repl(s), s)

    def test_pairs_each_independent_replacement(self):
        s = (r'\added{A}' + H + r'\deleted{a}' + H +
             ' keep ' + r'\added{B}' + H + r'\deleted{b}' + H)
        self.assertEqual(
            pair_repl(s),
            r'\replaced{A}{a}' + H + ' keep ' + r'\replaced{B}{b}' + H)

    def test_leaves_lone_added_or_deleted(self):
        self.assertEqual(pair_repl(r'\added{x}' + H), r'\added{x}' + H)
        self.assertEqual(pair_repl(r'\deleted{x}' + H), r'\deleted{x}' + H)

    def test_leaves_nested_brace_operand(self):
        s = r'\added{\textbf{x}}' + H + r'\deleted{y}' + H
        self.assertEqual(pair_repl(s), s)

    def test_full_pipeline_via_merge(self):
        s = r'\added{New}' + H + r'\added{}' + H + r'\deleted{Old}' + H
        self.assertEqual(merge_diff(s), r'\replaced{New}{Old}' + H)


if __name__ == '__main__':
    unittest.main()
