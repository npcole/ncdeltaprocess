"""Tests for list rendering — adapted from quill deltaprocess tests."""

import unittest
from ncdeltaprocess import TranslatorQuillJS


class TestFlatList(unittest.TestCase):
    def test_bullet_list(self):
        ops = [
            {'insert': 'Item 1'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
            {'insert': 'Item 2'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
            {'insert': 'Item 3'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(
            html,
            '<ul>'
            '<li><p>Item 1</p></li>'
            '<li><p>Item 2</p></li>'
            '<li><p>Item 3</p></li>'
            '</ul>'
        )

    def test_ordered_list(self):
        ops = [
            {'insert': 'First'}, {'insert': '\n', 'attributes': {'list': 'ordered'}},
            {'insert': 'Second'}, {'insert': '\n', 'attributes': {'list': 'ordered'}},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(
            html,
            '<ol>'
            '<li><p>First</p></li>'
            '<li><p>Second</p></li>'
            '</ol>'
        )


class TestListAsFirstBlock(unittest.TestCase):
    """Adapted from quill list_bug.py test_list_as_first_item_in_delta."""
    def test_list_as_first_item_in_delta(self):
        ops = [
            {"insert": "one"}, {"attributes": {"list": "ordered"}, "insert": "\n"},
            {"insert": "two"}, {"attributes": {"list": "ordered"}, "insert": "\n"},
            {"insert": "three"}, {"attributes": {"list": "ordered"}, "insert": "\n"},
            {"insert": "\nAnd some text.\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<ol>', html)
        self.assertIn('one', html)
        self.assertIn('two', html)
        self.assertIn('three', html)
        self.assertIn('And some text.', html)


class TestNestedList(unittest.TestCase):
    def test_nested_list(self):
        """Test list with indent depth 1."""
        ops = [
            {'insert': 'Outer'},
            {'attributes': {'list': 'ordered'}, 'insert': '\n'},
            {'insert': 'Inner'},
            {'attributes': {'indent': 1, 'list': 'ordered'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Should have nested <ol> inside the outer <li>
        self.assertIn('<ol>', html)
        self.assertIn('Outer', html)
        self.assertIn('Inner', html)

    def test_sub_list_then_back(self):
        """Items, sub-items, then back to top level."""
        ops = [
            {'insert': 'A'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'A1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'B'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<ul>', html)
        self.assertIn('A', html)
        self.assertIn('A1', html)
        self.assertIn('B', html)


class TestListWithNoneIndent(unittest.TestCase):
    """Adapted from quill list_bug.py — indent can be None."""
    def test_list_with_none_indent(self):
        ops = [
            {"insert": "Yarn"},
            {"attributes": {"indent": None, "list": "ordered"}, "insert": "\n"},
            {"insert": "Knitting"},
            {"attributes": {"indent": None, "list": "ordered"}, "insert": "\n"},
        ]
        t = TranslatorQuillJS()
        # Should not crash; None indent treated as 0
        html = t.translate_to_html(ops)
        self.assertIn('<ol>', html)
        self.assertIn('Yarn', html)
        self.assertIn('Knitting', html)


class TestListWithMixedContent(unittest.TestCase):
    """Adapted from quill list_bug.py test_list."""
    def test_mixed_list_and_paragraphs(self):
        ops = [
            {"insert": "Main text 1"},
            {"attributes": {"align": "center"}, "insert": "\n"},
            {"insert": "\nClause 1. Bethany likes:\nYarn"},
            {"attributes": {"indent": None, "list": "ordered"}, "insert": "\n"},
            {"insert": "Knitting"},
            {"attributes": {"indent": None, "list": "ordered"}, "insert": "\n"},
            {"insert": "Greyhounds"},
            {"attributes": {"indent": None, "list": "ordered"}, "insert": "\n"},
            {"insert": "Gardening"},
            {"attributes": {"indent": 1, "list": "ordered"}, "insert": "\n"},
            {"insert": "\nClause 2. \n\nClause 3. \n\n4. \n\n5. \n\n6. \n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Should have centered paragraph, list items, and trailing paragraphs
        self.assertIn('text-align: center', html)
        self.assertIn('<ol>', html)
        self.assertIn('Yarn', html)
        self.assertIn('Gardening', html)
        self.assertIn('Clause 2.', html)


class TestNestedListComprehensive(unittest.TestCase):
    """Comprehensive nested list tests covering depth transitions and structure."""

    def test_two_level_bullet_nesting(self):
        """Bullet list with sub-items at indent 1."""
        ops = [
            {'insert': 'Top 1'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Sub 1a'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Sub 1b'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Top 2'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Sub-items should be in a nested <ul> inside the first <li>
        self.assertIn('<ul><li><p>Top 1</p><ul><li><p>Sub 1a</p></li><li><p>Sub 1b</p></li></ul></li><li><p>Top 2</p></li></ul>', html)

    def test_three_level_nesting(self):
        """Three levels of nesting: 0, 1, 2."""
        ops = [
            {'insert': 'L0'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'L1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'L2'}, {'attributes': {'indent': 2, 'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('L0', html)
        self.assertIn('L1', html)
        self.assertIn('L2', html)
        # Count nesting depth by counting <ul> occurrences
        self.assertEqual(html.count('<ul>'), 3)
        self.assertEqual(html.count('</ul>'), 3)

    def test_deep_to_shallow_transition(self):
        """Going from indent 2 back to indent 0."""
        ops = [
            {'insert': 'Top'}, {'attributes': {'list': 'ordered'}, 'insert': '\n'},
            {'insert': 'Mid'}, {'attributes': {'indent': 1, 'list': 'ordered'}, 'insert': '\n'},
            {'insert': 'Deep'}, {'attributes': {'indent': 2, 'list': 'ordered'}, 'insert': '\n'},
            {'insert': 'Back to top'}, {'attributes': {'list': 'ordered'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('Top', html)
        self.assertIn('Deep', html)
        self.assertIn('Back to top', html)
        # All <ol> tags should be properly closed
        self.assertEqual(html.count('<ol>'), html.count('</ol>'))

    def test_mixed_list_types_nested(self):
        """Ordered list with bullet sub-items."""
        ops = [
            {'insert': 'Step 1'}, {'attributes': {'list': 'ordered'}, 'insert': '\n'},
            {'insert': 'Detail A'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Detail B'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Step 2'}, {'attributes': {'list': 'ordered'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<ol>', html)
        self.assertIn('<ul>', html)
        self.assertIn('Step 1', html)
        self.assertIn('Detail A', html)
        self.assertIn('Step 2', html)

    def test_siblings_at_same_depth(self):
        """Multiple items at the same indent level should be siblings, not nested."""
        ops = [
            {'insert': 'Parent'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child 1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child 2'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child 3'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Children should be siblings in one <ul>, not nested
        # The inner <ul> should contain 3 <li> items
        self.assertEqual(html.count('<li><p>Child'), 3)
        # Only 2 <ul> tags: outer and one inner
        self.assertEqual(html.count('<ul>'), 2)

    def test_alternating_depths(self):
        """Items alternating between depth 0 and 1."""
        ops = [
            {'insert': 'A'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'A.1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'B'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'B.1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('A', html)
        self.assertIn('A.1', html)
        self.assertIn('B', html)
        self.assertIn('B.1', html)
        # All tags balanced
        self.assertEqual(html.count('<ul>'), html.count('</ul>'))
        self.assertEqual(html.count('<li>'), html.count('</li>'))

    def test_nested_list_tree_structure(self):
        """Verify tree structure: items at same indent are siblings under same ListBlock."""
        from ncdeltaprocess import block as bks
        ops = [
            {'insert': 'A'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'B'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'C'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Document should have exactly one content block: a ListBlock
        self.assertEqual(len(doc.contents), 1)
        list_block = doc.contents[0]
        self.assertIsInstance(list_block, bks.ListBlock)
        # That ListBlock should have 3 ListItemBlock children
        self.assertEqual(len(list_block.contents), 3)
        for child in list_block.contents:
            self.assertIsInstance(child, bks.ListItemBlock)

    def test_nested_list_tree_structure_two_levels(self):
        """Verify two-level tree: sub-items under their parent's ListItemBlock."""
        from ncdeltaprocess import block as bks
        ops = [
            {'insert': 'Parent'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child 1'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child 2'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Document → ListBlock → ListItemBlock (Parent)
        list_block = doc.contents[0]
        self.assertIsInstance(list_block, bks.ListBlock)
        self.assertEqual(len(list_block.contents), 1)  # One top-level item
        parent_item = list_block.contents[0]
        self.assertIsInstance(parent_item, bks.ListItemBlock)
        # Parent item should have: TextBlockParagraph + nested ListBlock
        child_types = [type(c) for c in parent_item.contents]
        self.assertIn(bks.TextBlockParagraph, child_types)
        self.assertIn(bks.ListBlock, child_types)
        # The nested ListBlock should have 2 children
        nested_list = [c for c in parent_item.contents if isinstance(c, bks.ListBlock)][0]
        self.assertEqual(len(nested_list.contents), 2)

    def test_nested_list_latex(self):
        """Nested lists render correctly in LaTeX."""
        ops = [
            {'insert': 'Top'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Sub'}, {'attributes': {'indent': 1, 'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Top 2'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{itemize}', latex)
        self.assertIn(r'\item', latex)
        self.assertIn(r'\end{itemize}', latex)
        self.assertIn('Top', latex)
        self.assertIn('Sub', latex)
        # Nested itemize
        self.assertEqual(latex.count(r'\begin{itemize}'), 2)
        self.assertEqual(latex.count(r'\end{itemize}'), 2)

    def test_list_after_paragraph(self):
        """List following a paragraph is a separate block."""
        ops = [
            {'insert': 'Some text.\n'},
            {'insert': 'Item 1'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Item 2'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<p>Some text.</p>', html)
        self.assertIn('<ul>', html)
        self.assertIn('<li><p>Item 1</p></li>', html)

    def test_paragraph_after_list(self):
        """Paragraph following a list is a separate block."""
        ops = [
            {'insert': 'Item'}, {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'After list.\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('</ul><p>After list.</p>', html)

    def test_list_with_formatted_items(self):
        """List items containing bold/italic formatting."""
        ops = [
            {'insert': 'Normal '}, {'attributes': {'bold': True}, 'insert': 'bold'},
            {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'attributes': {'italic': True}, 'insert': 'italic item'},
            {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<strong>bold</strong>', html)
        self.assertIn('<em>italic item</em>', html)
        self.assertIn('<ul>', html)

    def test_checklist(self):
        """Checked/unchecked list items."""
        ops = [
            {'insert': 'Done'}, {'attributes': {'list': 'checked'}, 'insert': '\n'},
            {'insert': 'Not done'}, {'attributes': {'list': 'unchecked'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<ul class="checklist">', html)
        self.assertIn('<input type="checkbox" checked disabled />', html)
        self.assertIn('<input type="checkbox" disabled />', html)
        self.assertIn('Done', html)
        self.assertIn('Not done', html)

    def test_checklist_latex(self):
        """Checked/unchecked list items in LaTeX."""
        ops = [
            {'insert': 'Done'}, {'attributes': {'list': 'checked'}, 'insert': '\n'},
            {'insert': 'Not done'}, {'attributes': {'list': 'unchecked'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{itemize}', latex)
        self.assertIn(r'$\boxtimes$', latex)
        self.assertIn(r'$\square$', latex)


class TestListTextBlockSetting(unittest.TestCase):
    def test_list_without_p(self):
        ops = [
            {'insert': 'Item'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
        ]
        t = TranslatorQuillJS()
        t.settings['list_text_blocks_are_p'] = False
        html = t.translate_to_html(ops)
        # Without p setting, items should not have <p> wrappers
        self.assertNotIn('<p>', html)
        self.assertIn('Item', html)


if __name__ == '__main__':
    unittest.main()
