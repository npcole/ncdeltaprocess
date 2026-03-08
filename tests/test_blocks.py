"""Tests for block-level elements (paragraphs, headings, code blocks, dividers)."""

import unittest
from ncdeltaprocess import TranslatorQuillJS


class TestParagraph(unittest.TestCase):
    def test_simple_paragraph(self):
        ops = [{'insert': 'Hello world\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>Hello world</p>')

    def test_centered_paragraph(self):
        ops = [
            {'insert': 'Centered'},
            {'attributes': {'align': 'center'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('text-align: center', html)

    def test_empty_paragraph(self):
        ops = [{'insert': '\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p></p>')

    def test_multiple_paragraphs(self):
        ops = [{'insert': 'First\nSecond\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('First', html)
        self.assertIn('Second', html)
        self.assertEqual(html.count('<p>'), 2)

    def test_blockquote(self):
        ops = [
            {'insert': 'Quote'},
            {'attributes': {'blockquote': True}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<blockquote>', html)
        self.assertIn('</blockquote>', html)


class TestHeading(unittest.TestCase):
    def test_heading_levels(self):
        for level in range(1, 7):
            ops = [
                {'insert': f'Heading {level}'},
                {'attributes': {'header': level}, 'insert': '\n'},
            ]
            t = TranslatorQuillJS()
            html = t.translate_to_html(ops)
            self.assertIn(f'<h{level}>', html)
            self.assertIn(f'</h{level}>', html)

    def test_heading_none_not_matched(self):
        """header: None should NOT match the header test."""
        ops = [
            {'insert': 'Not a heading'},
            {'attributes': {'header': None}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Should be a plain paragraph, not a heading
        self.assertNotIn('<h', html)
        self.assertIn('<p>', html)

    def test_heading_with_base_level(self):
        ops = [
            {'insert': 'Title'},
            {'attributes': {'header': 1}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        from ncdeltaprocess.render import OutputObject
        output = OutputObject()
        output.heading_base_level = 2
        result = doc.render_tree()
        # Default render has heading_base_level=0 → h1
        self.assertIn('<h1>', result)


class TestCodeBlock(unittest.TestCase):
    def test_code_block(self):
        ops = [
            {'insert': 'print("hello")'},
            {'attributes': {'code-block': True}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<pre><code>', html)
        self.assertIn('</code></pre>', html)

    def test_code_block_with_language(self):
        ops = [
            {'insert': 'def foo(): pass'},
            {'attributes': {'code-block': 'python'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('language-python', html)

    def test_consecutive_code_blocks_merged(self):
        """Consecutive code blocks with same attributes should merge."""
        ops = [
            {'insert': 'line 1'},
            {'attributes': {'code-block': 'python'}, 'insert': '\n'},
            {'insert': 'line 2'},
            {'attributes': {'code-block': 'python'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Should be ONE <pre><code> block, not two
        self.assertEqual(html.count('<pre>'), 1)

    def test_different_language_code_blocks_not_merged(self):
        ops = [
            {'insert': 'line 1'},
            {'attributes': {'code-block': 'python'}, 'insert': '\n'},
            {'insert': 'line 2'},
            {'attributes': {'code-block': 'javascript'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html.count('<pre>'), 2)


class TestDivider(unittest.TestCase):
    def test_divider(self):
        ops = [
            {'insert': 'Before\n'},
            {'insert': {'divider': True}},
            {'insert': 'After\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<hr />', html)
        self.assertIn('Before', html)
        self.assertIn('After', html)


class TestImage(unittest.TestCase):
    def test_image(self):
        ops = [
            {'insert': {'image': 'photo.jpg'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<img src="photo.jpg">', html)


class TestEnsureFinalBlock(unittest.TestCase):
    def test_no_trailing_newline(self):
        """Delta without trailing newline should still produce output."""
        ops = [{'insert': 'No newline'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('No newline', html)

    def test_empty_ops(self):
        """Empty ops should produce empty output."""
        ops = []
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p></p>')


class TestDeepCopy(unittest.TestCase):
    def test_ops_not_mutated(self):
        """Caller's ops should not be mutated."""
        ops = [{'insert': 'Test\n'}]
        original = [{'insert': 'Test\n'}]
        t = TranslatorQuillJS()
        t.translate_to_html(ops)
        self.assertEqual(ops, original)


class TestNoneInsert(unittest.TestCase):
    def test_none_insert_skipped(self):
        """None insert values should be skipped with a warning."""
        ops = [
            {'insert': 'Before '},
            {'insert': None},
            {'insert': 'After\n'},
        ]
        t = TranslatorQuillJS()
        import warnings
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            html = t.translate_to_html(ops)
        self.assertIn('Before', html)
        self.assertIn('After', html)


if __name__ == '__main__':
    unittest.main()
