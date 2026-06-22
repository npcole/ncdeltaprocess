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
    pair_adjacent_diff_replacements as pair_repl,
)
from ncdeltaprocess.delta_process import (  # noqa: E402
    coalesce_adjacent_string_ops as coalesce,
)

H = r'\hspace{0pt}'


class TestCoalesceAdjacentStringOps(unittest.TestCase):
    """Op-level same-status fold — the safe place to merge: it can check that
    neighbours share attributes and carry string (not embed) content."""

    def test_merges_same_attributes(self):
        self.assertEqual(
            coalesce([{'insert': 'a', 'attributes': {'ncquill_diff': 'new'}},
                      {'insert': 'b', 'attributes': {'ncquill_diff': 'new'}}]),
            [{'insert': 'ab', 'attributes': {'ncquill_diff': 'new'}}])

    def test_merges_same_formatting_too(self):
        a = {'insert': 'one', 'attributes': {'italic': True, 'ncquill_diff': 'new'}}
        b = {'insert': ' two', 'attributes': {'italic': True, 'ncquill_diff': 'new'}}
        self.assertEqual(coalesce([a, b]),
                         [{'insert': 'one two',
                           'attributes': {'italic': True, 'ncquill_diff': 'new'}}])

    def test_does_not_merge_different_attributes(self):
        a = {'insert': 'new', 'attributes': {'bold': True, 'ncquill_diff': 'new'}}
        d = {'insert': 'old', 'attributes': {'italic': True, 'ncquill_diff': 'removed'}}
        self.assertEqual(coalesce([a, d]), [a, d])

    def test_drops_empty_string_ops(self):
        self.assertEqual(
            coalesce([{'insert': 'a', 'attributes': {'ncquill_diff': 'new'}},
                      {'insert': '', 'attributes': {'ncquill_diff': 'new'}},
                      {'insert': 'b', 'attributes': {'ncquill_diff': 'new'}}]),
            [{'insert': 'ab', 'attributes': {'ncquill_diff': 'new'}}])

    def test_never_merges_across_embed_object(self):
        embed = {'insert': {'image': 'x.png'}, 'attributes': {'ncquill_diff': 'new'}}
        ops = [{'insert': 'a', 'attributes': {'ncquill_diff': 'new'}}, embed,
               {'insert': 'b', 'attributes': {'ncquill_diff': 'new'}}]
        self.assertEqual(coalesce(ops), ops)

    def test_newline_is_a_boundary(self):
        ops = [{'insert': 'a', 'attributes': {'ncquill_diff': 'new'}},
               {'insert': '\n'},
               {'insert': 'b', 'attributes': {'ncquill_diff': 'new'}}]
        self.assertEqual(coalesce(ops), ops)

    def test_does_not_mutate_input(self):
        a = {'insert': 'a', 'attributes': {'ncquill_diff': 'new'}}
        b = {'insert': 'b', 'attributes': {'ncquill_diff': 'new'}}
        coalesce([a, b])
        self.assertEqual(a['insert'], 'a')


class TestPairAdjacentDiffReplacements(unittest.TestCase):
    """Render-level fold of a replacement (different-status add+delete) into a
    single \\replaced{new}{old}."""

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

    def test_leaves_formatted_replacement_explicit(self):
        s = r'\added{\textbf{new}}' + H + r'\deleted{\emph{old}}' + H
        self.assertEqual(pair_repl(s), s)

    def test_empty_inputs(self):
        self.assertEqual(pair_repl(''), '')
        self.assertIsNone(pair_repl(None))


if __name__ == '__main__':
    unittest.main()
