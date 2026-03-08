"""Tests for inline formatting (bold, italic, underline, superscript, etc.)."""

import unittest
from ncdeltaprocess import TranslatorQuillJS


class TestBold(unittest.TestCase):
    def test_bold(self):
        ops = [
            {'insert': 'Plain'},
            {'attributes': {'bold': True}, 'insert': 'Bold'},
            {'insert': 'Plain'},
            {'attributes': {'bold': True}, 'insert': 'Bold'},
            {'insert': 'Plain'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(
            html,
            '<p>Plain<strong>Bold</strong>Plain<strong>Bold</strong>Plain</p>'
        )


class TestItalic(unittest.TestCase):
    def test_italic(self):
        ops = [
            {'insert': 'Normal '},
            {'attributes': {'italic': True}, 'insert': 'italic'},
            {'insert': ' normal\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>Normal <em>italic</em> normal</p>')


class TestUnderline(unittest.TestCase):
    def test_underline(self):
        ops = [
            {'insert': 'Normal '},
            {'attributes': {'underline': True}, 'insert': 'underlined'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>Normal <u>underlined</u></p>')


class TestStrike(unittest.TestCase):
    def test_strike(self):
        ops = [
            {'attributes': {'strike': True}, 'insert': 'deleted'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p><s>deleted</s></p>')


class TestSuperscript(unittest.TestCase):
    def test_superscript(self):
        ops = [
            {'insert': 'E=mc'},
            {'attributes': {'script': 'super'}, 'insert': '2'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>E=mc<sup>2</sup></p>')

    def test_subscript(self):
        ops = [
            {'insert': 'H'},
            {'attributes': {'script': 'sub'}, 'insert': '2'},
            {'insert': 'O\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>H<sub>2</sub>O</p>')

    def test_alternating_super(self):
        ops = [
            {'insert': 'Test'},
            {'attributes': {'script': 'super'}, 'insert': 'Test'},
            {'insert': 'Test'},
            {'attributes': {'script': 'super'}, 'insert': 'Test'},
            {'insert': 'Test'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(
            html,
            '<p>Test<sup>Test</sup>Test<sup>Test</sup>Test</p>'
        )


class TestInlineCode(unittest.TestCase):
    def test_inline_code(self):
        ops = [
            {'insert': 'Use '},
            {'attributes': {'code': True}, 'insert': 'print()'},
            {'insert': ' function\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(html, '<p>Use <code>print()</code> function</p>')


class TestLink(unittest.TestCase):
    def test_link(self):
        ops = [
            {'insert': 'Visit '},
            {'attributes': {'link': 'https://example.com'}, 'insert': 'Example'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertEqual(
            html,
            '<p>Visit <a href="https://example.com">Example</a></p>'
        )


class TestCombinedFormatting(unittest.TestCase):
    def test_bold_italic(self):
        ops = [
            {'attributes': {'bold': True, 'italic': True}, 'insert': 'both'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<strong>', html)
        self.assertIn('<em>', html)
        self.assertIn('both', html)


class TestFontSize(unittest.TestCase):
    def test_small(self):
        ops = [
            {'attributes': {'size': 'small'}, 'insert': 'tiny'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('font-size: small', html)

    def test_large(self):
        ops = [
            {'attributes': {'size': 'large'}, 'insert': 'big'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('font-size: large', html)


class TestColor(unittest.TestCase):
    def test_color(self):
        ops = [
            {'attributes': {'color': 'red'}, 'insert': 'red text'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('color: red', html)

    def test_background(self):
        ops = [
            {'attributes': {'background': 'yellow'}, 'insert': 'highlighted'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('background-color: yellow', html)


class TestFont(unittest.TestCase):
    def test_monospace(self):
        ops = [
            {'attributes': {'font': 'monospace'}, 'insert': 'code'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('font-family: monospace', html)


class TestHtmlEscaping(unittest.TestCase):
    def test_escape_angle_brackets(self):
        ops = [
            {'insert': '<script>alert("xss")</script>\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)


if __name__ == '__main__':
    unittest.main()
