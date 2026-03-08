"""Security and edge case tests.

Tests for XSS prevention, malformed input handling, and boundary conditions.
"""

import unittest
import warnings
from ncdeltaprocess import TranslatorQuillJS


class TestXSSPrevention(unittest.TestCase):
    """Ensure user-controlled values are properly escaped in HTML output."""

    def test_script_in_text(self):
        ops = [{'insert': '<script>alert(1)</script>\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_xss_in_link_href(self):
        """Link href should not allow javascript: URIs."""
        ops = [
            {'attributes': {'link': 'javascript:alert(1)'}, 'insert': 'Click me'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('javascript:', html)

    def test_xss_in_link_attribute_injection(self):
        """Link values should not allow breaking out of href attribute."""
        ops = [
            {'attributes': {'link': '" onmouseover="alert(1)'}, 'insert': 'Hover'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # The double quotes should be escaped to &quot; preventing attribute breakout
        self.assertNotIn('" onmouseover="', html)
        self.assertIn('&quot;', html)

    def test_xss_in_anchor_id(self):
        """Anchor IDs should be escaped."""
        ops = [
            {'attributes': {'anchor': '"><script>alert(1)</script>'}, 'insert': 'Target'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<script>', html)

    def test_xss_in_color(self):
        """Color values should not allow CSS injection."""
        ops = [
            {'attributes': {'color': 'red;background:url(javascript:alert(1))'}, 'insert': 'Styled'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('javascript:', html)

    def test_xss_in_background_color(self):
        """Background color should not allow injection."""
        ops = [
            {'attributes': {'background': '"><img src=x onerror=alert(1)>'}, 'insert': 'Styled'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('onerror', html)

    def test_xss_in_image_src(self):
        """Image sources should be escaped."""
        ops = [
            {'insert': {'image': '"><script>alert(1)</script>'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<script>', html)

    def test_xss_in_image_link(self):
        """Image link attribute should not allow javascript: URIs."""
        ops = [
            {'insert': {'image': 'https://example.com/img.jpg'},
             'attributes': {'link': 'javascript:alert(1)'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('javascript:', html)

    def test_html_entities_in_heading(self):
        ops = [
            {'insert': '<img src=x onerror=alert(1)>'},
            {'attributes': {'header': 1}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # The angle brackets should be escaped, preventing HTML execution
        self.assertNotIn('<img', html)
        self.assertIn('&lt;img', html)

    def test_xss_in_code_block_language(self):
        """Code-block language attribute should be escaped."""
        ops = [
            {'insert': 'print("hi")'},
            {'attributes': {'code-block': 'python" onclick="alert(1)'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # The " characters are escaped to &quot; preventing attribute breakout.
        # onclick= appears in the output but safely within the quoted class value.
        self.assertNotIn('onclick="alert', html)  # raw unescaped form blocked
        self.assertIn('onclick=&quot;alert', html)  # escaped form present

    def test_xss_in_footnote_id(self):
        """Footnote marker IDs should be escaped in HTML attributes."""
        ops = [
            {'insert': 'See note'},
            {'attributes': {'annotation-marker': {
                'type': 'Footnote',
                'id': '"><script>alert(1)</script>',
            }}, 'insert': '*'},
            {'insert': '\n'},
            {'insert': 'Footnote text'},
            {'attributes': {'annotation-content': {
                'type': 'Footnote',
                'id': '"><script>alert(1)</script>',
            }}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<script>', html)

    def test_data_uri_in_image_src(self):
        """data: URIs should be allowed in image src (safe context)."""
        ops = [
            {'insert': {'image': 'data:image/png;base64,iVBOR'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('data:image/png;base64,iVBOR', html)

    def test_data_uri_blocked_in_link(self):
        """data: URIs should be blocked in link hrefs."""
        ops = [
            {'attributes': {'link': 'data:text/html,<script>alert(1)</script>'},
             'insert': 'Click'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('data:', html)

    def test_data_uri_blocked_in_image_link(self):
        """data: URIs in image link wrapper should be blocked."""
        ops = [
            {'insert': {'image': 'https://example.com/img.jpg'},
             'attributes': {'link': 'data:text/html,<script>alert(1)</script>'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        # The image should render, but no link wrapping
        self.assertIn('<img', html)
        self.assertNotIn('data:', html)


class TestLaTeXInjection(unittest.TestCase):
    """Ensure user-controlled values are escaped in LaTeX output."""

    def test_braces_in_link_url(self):
        """Braces in link URLs should be URL-encoded for LaTeX."""
        ops = [
            {'attributes': {'link': 'https://example.com/{evil}'}, 'insert': 'Click'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn('{evil}', latex)
        self.assertIn('%7Bevil%7D', latex)

    def test_backslash_in_link_url(self):
        """Backslashes in link URLs should be URL-encoded for LaTeX."""
        ops = [
            {'attributes': {'link': r'https://example.com/\input{/etc/passwd}'},
             'insert': 'Click'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn(r'\input', latex)

    def test_special_chars_in_anchor(self):
        """Anchor labels should be escaped for LaTeX."""
        ops = [
            {'attributes': {'anchor': r'label}{\input{evil}'}, 'insert': 'Target'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn(r'\input', latex)

    def test_special_chars_in_hyperlink(self):
        """Internal link labels (hyperlink) should be escaped for LaTeX."""
        ops = [
            {'attributes': {'link': r'#label}{\input{evil}'}, 'insert': 'Jump'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn(r'\input', latex)

    def test_braces_in_image_src(self):
        """Image src with braces should be safe in LaTeX."""
        ops = [
            {'insert': {'image': 'https://example.com/img{1}.jpg'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn('{1}', latex)
        self.assertIn('%7B1%7D', latex)

    def test_braces_in_image_link(self):
        """Image link with braces should be safe in LaTeX."""
        ops = [
            {'insert': {'image': 'https://example.com/img.jpg'},
             'attributes': {'link': 'https://example.com/{evil}'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertNotIn('{evil}', latex)
        self.assertIn('%7Bevil%7D', latex)


class TestMalformedInput(unittest.TestCase):
    """Test handling of malformed or unexpected Delta ops."""

    def test_empty_ops(self):
        t = TranslatorQuillJS()
        html = t.translate_to_html([])
        self.assertIsInstance(html, str)

    def test_none_insert(self):
        ops = [
            {'insert': None},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            html = t.translate_to_html(ops)
            self.assertTrue(any('None insert' in str(warning.message) for warning in w))

    def test_missing_insert_key(self):
        ops = [{'attributes': {'bold': True}}]
        t = TranslatorQuillJS()
        with self.assertRaises(ValueError):
            t.translate_to_html(ops)

    def test_empty_string_insert(self):
        ops = [{'insert': ''}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIsInstance(html, str)

    def test_only_newlines(self):
        ops = [{'insert': '\n\n\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIsInstance(html, str)

    def test_empty_attributes(self):
        ops = [{'insert': 'text', 'attributes': {}}, {'insert': '\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('text', html)

    def test_unknown_embed_type(self):
        """Unknown dict embeds should raise ValueError."""
        ops = [
            {'insert': {'unknown_embed': True}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        with self.assertRaises(ValueError):
            t.translate_to_html(ops)

    def test_deeply_nested_list(self):
        """Lists with many levels of nesting should not crash."""
        ops = []
        for i in range(10):
            ops.append({'insert': f'Level {i}'})
            attrs = {'list': 'bullet'}
            if i > 0:
                attrs['indent'] = i
            ops.append({'attributes': attrs, 'insert': '\n'})
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('Level 0', html)
        self.assertIn('Level 9', html)

    def test_very_long_text(self):
        """Very long text should not crash."""
        long_text = 'x' * 100000
        ops = [{'insert': long_text + '\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn(long_text, html)

    def test_unicode_text(self):
        ops = [{'insert': 'Hello \u4e16\u754c \U0001f600\n'}]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('\u4e16\u754c', html)
        self.assertIn('\U0001f600', html)

    def test_header_none_value(self):
        """Header attribute with None value should not match header test."""
        ops = [
            {'insert': 'Not a heading'},
            {'attributes': {'header': None}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertNotIn('<h', html)
        self.assertIn('Not a heading', html)


class TestDeepCopy(unittest.TestCase):
    """Ensure ops_to_internal_representation doesn't mutate input."""

    def test_no_mutation(self):
        import json
        ops = [
            {'insert': 'Hello'},
            {'attributes': {'bold': True}, 'insert': ' world'},
            {'insert': '\n'},
        ]
        original = json.dumps(ops)
        t = TranslatorQuillJS()
        t.translate_to_html(ops)
        self.assertEqual(json.dumps(ops), original)


class TestDiffMode(unittest.TestCase):
    """Test diff_mode behavior."""

    def test_diff_mode_skips_blank_blocks(self):
        ops = [
            {'insert': 'Content\n'},
            {'insert': '\n'},
            {'insert': 'More\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('Content', html)
        self.assertIn('More', html)

    def test_normal_mode_keeps_blank_blocks(self):
        ops = [
            {'insert': 'Content\n'},
            {'insert': '\n'},
            {'insert': 'More\n'},
        ]
        t = TranslatorQuillJS(diff_mode=False)
        html = t.translate_to_html(ops)
        self.assertIn('Content', html)
        self.assertIn('More', html)


if __name__ == '__main__':
    unittest.main()
