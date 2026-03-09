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
        self.assertNotIn('<p>This is the annotation content</p>', html)
        # Annotation content block should be rendered as a hidden div
        self.assertIn('ql-annotation-content', html)
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
    def test_annotation_stored_in_data_blocks_when_disabled(self):
        """With render_annotation_content_blocks=False, blocks go to data_blocks."""
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
        t.settings['render_annotation_content_blocks'] = False
        doc = t.ops_to_internal_representation(ops)
        # Annotation should be in data_blocks
        self.assertEqual(len(doc.data_blocks), 1)
        # Main text should be in contents
        self.assertTrue(len(doc.contents) >= 1)
        # Block index should map the ID
        self.assertIn('test-id', doc.block_index)

    def test_annotation_always_in_data_blocks(self):
        """Annotation content blocks are always stored in data_blocks."""
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


class TestAnnotationContentWithList(unittest.TestCase):
    def test_annotation_content_with_list_attribute(self):
        """Annotation-content block with list attribute should not crash."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "list-ann", "type": "Footnote"},
                    "list": "bullet",
                },
                "insert": "A listed annotation item\n",
            },
            {"insert": "Body text"},
            {
                "attributes": {
                    "annotation-marker": {"id": "list-ann", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        # Should not raise "More than one block test matched"
        html = t.translate_to_html(ops)
        self.assertIn('footnote-marker', html)
        self.assertIn('A listed annotation item', html)


class TestRenderAnnotationContentBlocks(unittest.TestCase):
    def _make_ops(self):
        return [
            {
                "attributes": {
                    "annotation-content": {"id": "vis-ann", "type": "Annotation"}
                },
                "insert": "Annotation text here\n",
            },
            {"insert": "Main paragraph"},
            {
                "attributes": {
                    "annotation-marker": {"id": "vis-ann", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]

    def test_annotation_content_rendered_hidden_by_default(self):
        """With default settings, annotation content appears as hidden div."""
        t = TranslatorQuillJS()
        html = t.translate_to_html(self._make_ops())
        self.assertIn('ql-annotation-content', html)
        self.assertIn('display: none', html)
        self.assertIn('Annotation text here', html)

    def test_annotation_content_not_in_dom_when_disabled(self):
        """With render_annotation_content_blocks=False, no hidden div in DOM."""
        t = TranslatorQuillJS()
        t.settings['render_annotation_content_blocks'] = False
        html = t.translate_to_html(self._make_ops())
        # The hidden div should NOT appear as a top-level rendered block
        self.assertNotIn('ql-annotation-content', html)
        # But the annotation content should still be in the inline annotation span
        self.assertIn('annotation-content', html)
        self.assertIn('Annotation text here', html)


class TestRenderFootnoteBacklinks(unittest.TestCase):
    def _make_ops(self):
        return [
            {
                "attributes": {
                    "annotation-content": {"id": "fn-back", "type": "Footnote"}
                },
                "insert": "Footnote content text\n",
            },
            {"insert": "Body with footnote"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fn-back", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]

    def test_footnote_backlinks_present_by_default(self):
        """With default settings, footnote end-matter blocks are generated."""
        t = TranslatorQuillJS()
        html = t.translate_to_html(self._make_ops())
        self.assertIn('footnote-block', html)
        self.assertIn('footnote-number', html)
        self.assertIn('footnote-marker', html)
        self.assertIn('[1]', html)

    def test_footnote_backlinks_disabled(self):
        """With render_footnote_backlinks=False, no end-matter but inline markers remain."""
        t = TranslatorQuillJS()
        t.settings['render_footnote_backlinks'] = False
        html = t.translate_to_html(self._make_ops())
        # Inline marker should still be present
        self.assertIn('footnote-marker', html)
        self.assertIn('[1]', html)
        # End-matter should NOT be present
        self.assertNotIn('footnote-block', html)
        self.assertNotIn('footnote-number', html)


class TestAnnotatedList(unittest.TestCase):
    def test_bullet_list_compound_format(self):
        """Compound annotated-list with bullet type renders as <ul>."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "list-1", "type": "Annotation"},
                    }
                },
                "insert": "First bullet\n",
            },
            {"insert": "Body text"},
            {
                "attributes": {
                    "annotation-marker": {"id": "list-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        self.assertIn("list-1", doc.block_index)
        html = doc.render_tree()
        self.assertIn("<ul>", html)
        self.assertIn("<li>", html)
        self.assertIn("First bullet", html)
        self.assertNotIn("<p>First bullet</p>", html)

    def test_ordered_list_compound_format(self):
        """Compound annotated-list with ordered type renders as <ol>."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "ordered",
                        "annotation-content": {"id": "ol-1", "type": "Annotation"},
                    }
                },
                "insert": "First item\n",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "ordered",
                        "annotation-content": {"id": "ol-1", "type": "Annotation"},
                    }
                },
                "insert": "Second item\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ol-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        html = doc.render_tree()
        self.assertIn("<ol>", html)
        self.assertIn("First item", html)
        self.assertIn("Second item", html)
        # Both items should be in the same list inside the container
        container = doc.block_index["ol-1"]
        inner = container.render_inner()
        self.assertEqual(inner.count("<ol>"), 1)

    def test_nested_list_with_indent(self):
        """Annotated list items with indent produce nested list structure."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "nest-1", "type": "Annotation"},
                    }
                },
                "insert": "Top level\n",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "nest-1", "type": "Annotation"},
                    },
                    "indent": 1,
                },
                "insert": "Nested item\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "nest-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn("Top level", html)
        self.assertIn("Nested item", html)
        # Should have nested <ul> tags
        self.assertGreater(html.count("<ul>"), 1)

    def test_bullet_list_footnote_html(self):
        """Annotated-list in a footnote renders list in end-matter."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "fn-list", "type": "Footnote"},
                    }
                },
                "insert": "Footnote bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fn-list", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn("footnote-block", html)
        self.assertIn("<ul>", html)
        self.assertIn("Footnote bullet", html)


class TestAnnotatedBlockquote(unittest.TestCase):
    def test_blockquote_compound_format(self):
        """Compound annotated-blockquote renders as <blockquote>."""
        ops = [
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "bq-1", "type": "Annotation"},
                    }
                },
                "insert": "A quoted passage\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "bq-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        self.assertIn("<blockquote>", html)
        self.assertIn("A quoted passage", html)
        self.assertNotIn("<p>A quoted passage</p>", html)

    def test_blockquote_latex(self):
        """Annotated blockquote renders as quotation environment in LaTeX."""
        ops = [
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "bq-l", "type": "Annotation"},
                    }
                },
                "insert": "Quoted in latex\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "bq-l", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r"\begin{quotation}", latex)
        self.assertIn("Quoted in latex", latex)


class TestAnnotatedCodeBlock(unittest.TestCase):
    def test_code_block_compound_format(self):
        """Compound annotated-code-block renders as <pre><code>."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "cb-1", "type": "Annotation"},
                    }
                },
                "insert": "x = 42\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "cb-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        self.assertIn("<pre><code>", html)
        self.assertIn("x = 42", html)

    def test_code_block_with_language(self):
        """Code block with language attribute adds class."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": "python",
                        "annotation-content": {"id": "cb-lang", "type": "Annotation"},
                    }
                },
                "insert": "print('hi')\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "cb-lang", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('language-python', html)
        self.assertIn("print(&#x27;hi&#x27;)", html)

    def test_consecutive_code_blocks_merge(self):
        """Consecutive annotated-code-block ops with same attributes merge."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "cb-m", "type": "Annotation"},
                    }
                },
                "insert": "line 1\n",
            },
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "cb-m", "type": "Annotation"},
                    }
                },
                "insert": "line 2\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "cb-m", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        html = doc.render_tree()
        # Both lines should be present
        self.assertIn("line 1", html)
        self.assertIn("line 2", html)
        # Container should have only one TextBlockCode (merged)
        from ncdeltaprocess.block import TextBlockCode
        container = doc.block_index["cb-m"]
        code_blocks = [c for c in container.contents if isinstance(c, TextBlockCode)]
        self.assertEqual(len(code_blocks), 1)


class TestAnnotatedMixedContent(unittest.TestCase):
    def test_plain_paragraph_plus_list(self):
        """Mixed annotation: plain paragraph followed by list items."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "mix-1", "type": "Annotation"}
                },
                "insert": "Intro paragraph\n",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "mix-1", "type": "Annotation"},
                    }
                },
                "insert": "Bullet one\n",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "mix-1", "type": "Annotation"},
                    }
                },
                "insert": "Bullet two\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "mix-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # All stored in same data block
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        self.assertIn("Intro paragraph", html)
        self.assertIn("<ul>", html)
        self.assertIn("Bullet one", html)
        self.assertIn("Bullet two", html)

    def test_paragraph_blockquote_code(self):
        """Mixed annotation: paragraph + blockquote + code block."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "mix-2", "type": "Annotation"}
                },
                "insert": "A note\n",
            },
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "mix-2", "type": "Annotation"},
                    }
                },
                "insert": "Quoted text\n",
            },
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "mix-2", "type": "Annotation"},
                    }
                },
                "insert": "code()\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "mix-2", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        self.assertIn("A note", html)
        self.assertIn("<blockquote>", html)
        self.assertIn("Quoted text", html)
        self.assertIn("<pre><code>", html)
        self.assertIn("code()", html)


class TestAnnotatedOldFormatListFix(unittest.TestCase):
    def test_old_format_list_renders_as_list(self):
        """Old format (annotation-content + list siblings) now renders as <ul>/<ol>."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "old-list", "type": "Footnote"},
                    "list": "bullet",
                },
                "insert": "Old format bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "old-list", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        self.assertIn("<ul>", html)
        self.assertIn("<li>", html)
        self.assertIn("Old format bullet", html)


class TestAnnotatedLatex(unittest.TestCase):
    def test_list_latex(self):
        """Annotated list renders as itemize/enumerate in LaTeX."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "ltx-list", "type": "Annotation"},
                    }
                },
                "insert": "LaTeX bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ltx-list", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r"\begin{itemize}", latex)
        self.assertIn(r"\item", latex)
        self.assertIn("LaTeX bullet", latex)

    def test_ordered_list_latex(self):
        """Annotated ordered list renders as enumerate in LaTeX."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "ordered",
                        "annotation-content": {"id": "ltx-ol", "type": "Annotation"},
                    }
                },
                "insert": "Numbered item\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ltx-ol", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r"\begin{enumerate}", latex)
        self.assertIn("Numbered item", latex)

    def test_blockquote_latex(self):
        """Annotated blockquote renders as quotation in LaTeX."""
        ops = [
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "ltx-bq", "type": "Annotation"},
                    }
                },
                "insert": "A quote\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ltx-bq", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r"\begin{quotation}", latex)
        self.assertIn("A quote", latex)

    def test_code_block_latex(self):
        """Annotated code block renders as verbatim in LaTeX."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "ltx-cb", "type": "Annotation"},
                    }
                },
                "insert": "some_code()\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "ltx-cb", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r"\begin{verbatim}", latex)
        # Underscore is LaTeX-escaped inside verbatim rendering
        self.assertIn("some\\_code()", latex)


class TestAnnotatedDiffMode(unittest.TestCase):
    """Compound annotation attributes work correctly with DIFF_MODE and diff attributes."""

    def test_compound_annotation_stored_in_diff_mode(self):
        """Compound annotated-list is stored in data_blocks even in diff_mode=True."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "diff-1", "type": "Annotation"},
                    },
                    "ncquill_para_diff": "changed",
                },
                "insert": "Changed bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        self.assertIn("diff-1", doc.block_index)
        html = doc.render_tree()
        self.assertIn("<ul>", html)
        self.assertIn("Changed bullet", html)

    def test_empty_annotation_not_skipped_in_diff_mode(self):
        """Empty annotation block in diff mode is NOT skipped (unlike empty body paragraphs)."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "diff-e", "type": "Annotation"}
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-e", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        self.assertIn("diff-e", doc.block_index)

    def test_inline_diff_inside_annotation_content(self):
        """ncquill_diff on inline text within annotation content renders diff CSS classes."""
        ops = [
            {
                "attributes": {
                    "ncquill_diff": "delete",
                },
                "insert": "Removed text",
            },
            {
                "attributes": {
                    "annotation-content": {"id": "diff-2", "type": "Annotation"},
                },
                "insert": "\n",
            },
            {
                "attributes": {
                    "ncquill_diff": "insert",
                },
                "insert": "new_code()",
            },
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": "python",
                        "annotation-content": {"id": "diff-2", "type": "Annotation"},
                    },
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-2", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        container = doc.block_index["diff-2"]
        inner = container.render_inner()
        self.assertIn("quill-diff-delete", inner)
        self.assertIn("Removed text", inner)
        self.assertIn("quill-diff-insert", inner)
        self.assertIn("new_code()", inner)
        self.assertIn("<pre><code", inner)

    def test_compound_list_with_inline_diff_in_footnote(self):
        """Annotated-list footnote with inline diff renders list + diff + end-matter."""
        ops = [
            {
                "attributes": {
                    "ncquill_diff": "insert",
                },
                "insert": "New bullet text",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "diff-3", "type": "Footnote"},
                    },
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-3", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn("<ul>", html)
        self.assertIn("quill-diff-insert", html)
        self.assertIn("footnote-block", html)
        self.assertIn("New bullet text", html)

    def test_compound_blockquote_with_para_diff(self):
        """Annotated-blockquote with ncquill_para_diff is stored in data_blocks."""
        ops = [
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "diff-4", "type": "Annotation"},
                    },
                    "ncquill_para_diff": "changed",
                },
                "insert": "A changed quote\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-4", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        container = doc.block_index["diff-4"]
        inner = container.render_inner()
        self.assertIn("<blockquote>", inner)
        self.assertIn("A changed quote", inner)

    def test_compound_code_block_with_para_diff(self):
        """Annotated-code-block with ncquill_para_diff is stored in data_blocks."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "diff-5", "type": "Annotation"},
                    },
                    "ncquill_para_diff": "changed",
                },
                "insert": "x = 1\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "diff-5", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        container = doc.block_index["diff-5"]
        inner = container.render_inner()
        self.assertIn("<pre><code>", inner)
        self.assertIn("x = 1", inner)


class TestMalformedAnnotationInput(unittest.TestCase):
    """Malformed annotation attributes should fall through gracefully, not crash."""

    def test_annotation_content_none_value(self):
        """annotation-content: None should not crash — falls through to paragraph."""
        ops = [
            {
                "attributes": {"annotation-content": None},
                "insert": "Should be a paragraph\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)
        self.assertTrue(len(doc.contents) >= 1)

    def test_annotation_content_empty_dict(self):
        """annotation-content: {} (no id) should not crash — falls through."""
        ops = [
            {
                "attributes": {"annotation-content": {}},
                "insert": "No id here\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_annotation_content_missing_id(self):
        """annotation-content with type but no id should not crash."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"type": "Annotation"}
                },
                "insert": "Missing id\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_compound_list_non_dict_value(self):
        """annotated-list: 'not-a-dict' should not crash."""
        ops = [
            {
                "attributes": {"annotated-list": "not-a-dict"},
                "insert": "Should be a paragraph\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)
        self.assertTrue(len(doc.contents) >= 1)

    def test_compound_list_missing_annotation_content(self):
        """annotated-list without annotation-content inside should fall through."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {"list": "bullet"}
                },
                "insert": "No annotation-content\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_compound_list_annotation_content_no_id(self):
        """annotated-list with annotation-content missing id should fall through."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"type": "Annotation"},
                    }
                },
                "insert": "Missing id in compound\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_compound_blockquote_non_dict_value(self):
        """annotated-blockquote: True should not crash."""
        ops = [
            {
                "attributes": {"annotated-blockquote": True},
                "insert": "Boolean value\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_compound_code_block_non_dict_value(self):
        """annotated-code-block: 42 should not crash."""
        ops = [
            {
                "attributes": {"annotated-code-block": 42},
                "insert": "Numeric value\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)

    def test_annotation_content_id_not_string(self):
        """annotation-content with non-string id should fall through."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": 123, "type": "Annotation"}
                },
                "insert": "Numeric id\n",
            },
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 0)


class TestAnnotationIsolation(unittest.TestCase):
    """Compound annotation blocks must not contaminate other structures."""

    def test_two_annotations_different_formats(self):
        """Two annotations with different block formats are independent."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "ann-A", "type": "Annotation"},
                    }
                },
                "insert": "Bullet in A\n",
            },
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "ann-B", "type": "Annotation"},
                    }
                },
                "insert": "Quote in B\n",
            },
            {"insert": "Body text with "},
            {
                "attributes": {
                    "annotation-marker": {"id": "ann-A", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": " and "},
            {
                "attributes": {
                    "annotation-marker": {"id": "ann-B", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 2)
        container_a = doc.block_index["ann-A"]
        container_b = doc.block_index["ann-B"]
        inner_a = container_a.render_inner()
        inner_b = container_b.render_inner()
        self.assertIn("<ul>", inner_a)
        self.assertNotIn("<blockquote>", inner_a)
        self.assertIn("<blockquote>", inner_b)
        self.assertNotIn("<ul>", inner_b)

    def test_annotation_list_then_document_list(self):
        """Annotated list items must not merge with a regular document list."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "iso-1", "type": "Annotation"},
                    }
                },
                "insert": "Annotation bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "iso-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
            {"insert": "Document bullet"},
            {"attributes": {"list": "bullet"}, "insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Annotation list is in data_blocks
        self.assertEqual(len(doc.data_blocks), 1)
        # Document list is in contents (not data_blocks)
        from ncdeltaprocess.block import ListBlock
        doc_lists = [b for b in doc.contents if isinstance(b, ListBlock)]
        self.assertEqual(len(doc_lists), 1)
        # No cross-contamination: annotation container has its own list
        container = doc.block_index["iso-1"]
        ann_lists = [b for b in container.contents if isinstance(b, ListBlock)]
        self.assertEqual(len(ann_lists), 1)

    def test_plain_then_compound_same_id(self):
        """Plain annotation-content followed by compound annotated-list with same ID."""
        ops = [
            {
                "attributes": {
                    "annotation-content": {"id": "mix-id", "type": "Annotation"}
                },
                "insert": "Plain paragraph\n",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "ordered",
                        "annotation-content": {"id": "mix-id", "type": "Annotation"},
                    }
                },
                "insert": "List item\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "mix-id", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Same annotation container
        self.assertEqual(len(doc.data_blocks), 1)
        container = doc.block_index["mix-id"]
        inner = container.render_inner()
        self.assertIn("Plain paragraph", inner)
        self.assertIn("<ol>", inner)
        self.assertIn("List item", inner)


class TestInlineFormattingInCompoundBlocks(unittest.TestCase):
    """Inline formatting (bold, italic, etc.) works inside compound annotation blocks."""

    def test_bold_in_annotated_list(self):
        """Bold text inside an annotated list item."""
        ops = [
            {
                "attributes": {"bold": True},
                "insert": "Bold bullet",
            },
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "fmt-1", "type": "Annotation"},
                    }
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fmt-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        container = doc.block_index["fmt-1"]
        inner = container.render_inner()
        self.assertIn("<strong>Bold bullet</strong>", inner)
        self.assertIn("<ul>", inner)

    def test_link_in_annotated_blockquote(self):
        """Link inside an annotated blockquote."""
        ops = [
            {
                "attributes": {"link": "https://example.com"},
                "insert": "Click here",
            },
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "fmt-2", "type": "Annotation"},
                    }
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fmt-2", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        container = doc.block_index["fmt-2"]
        inner = container.render_inner()
        self.assertIn('<a href="https://example.com">Click here</a>', inner)
        self.assertIn("<blockquote>", inner)

    def test_inline_code_in_annotated_code_block(self):
        """Inline code attribute does not interfere with block code rendering."""
        ops = [
            {"insert": "x = 1"},
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": "python",
                        "annotation-content": {"id": "fmt-3", "type": "Annotation"},
                    }
                },
                "insert": "\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "fmt-3", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        container = doc.block_index["fmt-3"]
        inner = container.render_inner()
        self.assertIn('<pre><code class="language-python">', inner)
        self.assertIn("x = 1", inner)


class TestCompoundAnnotationSettings(unittest.TestCase):
    """Settings interact correctly with compound annotation formats."""

    def test_compound_list_hidden_when_disabled(self):
        """render_annotation_content_blocks=False hides compound list content."""
        ops = [
            {
                "attributes": {
                    "annotated-list": {
                        "list": "bullet",
                        "annotation-content": {"id": "set-1", "type": "Annotation"},
                    }
                },
                "insert": "Hidden bullet\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "set-1", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        t.settings["render_annotation_content_blocks"] = False
        doc = t.ops_to_internal_representation(ops)
        self.assertEqual(len(doc.data_blocks), 1)
        html = doc.render_tree()
        # Hidden div should NOT appear
        self.assertNotIn("ql-annotation-content", html)
        # But inline annotation span should still contain the content
        self.assertIn("annotation-content", html)
        self.assertIn("Hidden bullet", html)

    def test_compound_code_block_hidden_when_disabled(self):
        """render_annotation_content_blocks=False hides compound code block content."""
        ops = [
            {
                "attributes": {
                    "annotated-code-block": {
                        "code-block": True,
                        "annotation-content": {"id": "set-2", "type": "Annotation"},
                    }
                },
                "insert": "hidden_code()\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "set-2", "type": "Annotation"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        t.settings["render_annotation_content_blocks"] = False
        html = t.translate_to_html(ops)
        self.assertNotIn("ql-annotation-content", html)
        self.assertIn("annotation-content", html)

    def test_compound_blockquote_footnote_backlinks_disabled(self):
        """render_footnote_backlinks=False with compound blockquote footnote."""
        ops = [
            {
                "attributes": {
                    "annotated-blockquote": {
                        "blockquote": True,
                        "annotation-content": {"id": "set-3", "type": "Footnote"},
                    }
                },
                "insert": "Footnote quote\n",
            },
            {"insert": "Body"},
            {
                "attributes": {
                    "annotation-marker": {"id": "set-3", "type": "Footnote"}
                },
                "insert": "※",
            },
            {"insert": "\n"},
        ]
        t = TranslatorQuillJS()
        t.settings["render_footnote_backlinks"] = False
        html = t.translate_to_html(ops)
        # Inline marker present
        self.assertIn("footnote-marker", html)
        self.assertIn("[1]", html)
        # End-matter should NOT be present
        self.assertNotIn("footnote-block", html)


if __name__ == '__main__':
    unittest.main()
