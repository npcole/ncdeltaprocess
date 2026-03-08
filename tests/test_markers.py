"""Tests for annotation and footnote markers — adapted from quill deltaprocess tests."""

import unittest
from ncdeltaprocess import TranslatorQuillJS


class TestAnnotation(unittest.TestCase):
    def test_annotation_produces_inline_content(self):
        """Annotation marker should render inline with its content."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "abc-123", "type": "Annotation"}
                },
                "insert": "This is the annotation content\n",
            },
            {"insert": "Here is some text with an "},
            {
                "attributes": {
                    "annotation-marker": {"id": "abc-123", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": " in it.\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # The annotation content should be in the output
        self.assertIn('annotation', html)
        self.assertIn('This is the annotation content', html)
        # The content should NOT appear as a separate paragraph
        # (annotation blocks go into data_blocks, not contents)
        self.assertNotIn('<p>This is the annotation content</p>', html)
        # The body text should be present
        self.assertIn('Here is some text with an', html)
        self.assertIn('in it.', html)


class TestFootnote(unittest.TestCase):
    def test_single_footnote(self):
        """Footnote marker should render numbered reference with end-matter."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "abc-123", "type": "Footnote"}
                },
                "insert": "This is the annotation content\n",
            },
            {"insert": "Here is some text with an "},
            {
                "attributes": {
                    "annotation-marker": {"id": "abc-123", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": " in it.\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # Should have a footnote marker reference
        self.assertIn('footnote-marker', html)
        self.assertIn('[1]', html)
        self.assertIn('#fn-abc-123', html)
        # Should have a footnote block at the end
        self.assertIn('footnote-block', html)
        self.assertIn('footnote-number', html)
        self.assertIn('This is the annotation content', html)

    def test_two_footnotes(self):
        """Two footnotes should be numbered sequentially."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "abc-123", "type": "Footnote"}
                },
                "insert": "First footnote content\n",
            },
            {
                "attributes": {
                    "annotation-content": {"id": "def-456", "type": "Footnote"}
                },
                "insert": "Second footnote content\n",
            },
            {"insert": "Text with first"},
            {
                "attributes": {
                    "annotation-marker": {"id": "abc-123", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": " and second"},
            {
                "attributes": {
                    "annotation-marker": {"id": "def-456", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": ".\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('[1]', html)
        self.assertIn('[2]', html)
        self.assertIn('#fn-abc-123', html)
        self.assertIn('#fn-def-456', html)
        self.assertIn('First footnote content', html)
        self.assertIn('Second footnote content', html)


class TestAnnotationDataBlocks(unittest.TestCase):
    def test_annotation_stored_in_data_blocks(self):
        """Annotation content blocks should be in data_blocks, not contents."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "test-id", "type": "Annotation"}
                },
                "insert": "Hidden content\n",
            },
            {"insert": "Visible text\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Annotation should be in data_blocks
        self.assertEqual(len(doc.data_blocks), 1)
        # Main text should be in contents
        self.assertTrue(len(doc.contents) >= 1)
        # Block index should map the ID
        self.assertIn('test-id', doc.block_index)


class TestAnnotationLatex(unittest.TestCase):
    def test_annotation_latex(self):
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "ann-1", "type": "Annotation"}
                },
                "insert": "Margin note\n",
            },
            {"insert": "Main text"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ann-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\marginpar{', latex)
        self.assertIn('Margin note', latex)

    def test_footnote_latex(self):
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "fn-1", "type": "Footnote"}
                },
                "insert": "Footnote text\n",
            },
            {"insert": "Main text"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fn-1", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\footnote{', latex)
        self.assertIn('Footnote text', latex)


if __name__ == '__main__':
    unittest.main()
