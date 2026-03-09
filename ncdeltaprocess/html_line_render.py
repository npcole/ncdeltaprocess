"""HTML inline rendering for Quill delta text runs.

LineRenderHTML converts individual text runs (with their Quill attributes)
into HTML markup. It is instantiated by TextLine and delegates to the host
node for attribute access.
"""

from __future__ import annotations

import html as _html
import weakref
from typing import TYPE_CHECKING

from .sanitize import sanitize_url, CSS_SAFE_PATTERN

if TYPE_CHECKING:
    from .node import TextLine


class LineRenderHTML(object):
    """Renders a single text run (with Quill attributes) to HTML.

    Attributes:
        host: Weak reference to the owning ``TextLine`` node. Provides
            ``host.attributes`` (the Quill inline attributes dict, e.g.
            bold, italic, link, color) and ``host.contents`` (the raw
            text string). Stored as a ``weakref.proxy`` to avoid circular
            references (TextLine → renderer → TextLine).
    """

    def __init__(self, host: TextLine) -> None:
        self.host: TextLine = weakref.proxy(host)

    standard_inline_styles: dict[str, tuple[str, str]] = {
        'italic': ('<em>', '</em>'),
        'bold': ('<strong>', '</strong>'),
        'strike': ('<s>', '</s>'),
        'underline': ('<u>', '</u>'),
    }

    script_styles: dict[str, tuple[str, str]] = {
        'sub': ('<sub>', '</sub>'),
        'super': ('<sup>', '</sup>'),
    }

    css_font_size: dict[str, str] = {
        'small': 'small',
        'large': 'large',
        'huge': 'x-large',
    }

    allowed_fonts: dict[str, str] = {
        'monospace': 'monospace, monospace',
        'serif': 'serif',
        'sans-serif': 'sans-serif',
    }

    text_span_css: list[tuple[str, str, str | None]] = [
        # (quilljs attribute, css property, translator dict name or None)
        ('size', 'font-size', 'css_font_size'),
        ('font', 'font-family', 'allowed_fonts'),
        ('color', 'color', None),
        ('background', 'background-color', None),
    ]

    quill_diff_translator: dict[str, str] = {
        'insert': 'quill-diff-insert',
        'delete': 'quill-diff-delete',
        'new': 'quill-diff-insert',
        'removed': 'quill-diff-delete',
        'edited': 'quill-diff-edit',
    }

    css_classes: list[tuple[str, str]] = [
        # (attribute name, translator dict name)
        ('quill_diff', 'quill_diff_translator'),
        ('ncquill_diff', 'quill_diff_translator'),
    ]

    post_processing: list[str] = [
        'add_links',
    ]

    def _sanitize_css_value(self, value: str | int | float) -> str | None:
        """Sanitize a CSS value: only allow safe characters."""
        if CSS_SAFE_PATTERN.match(str(value)):
            return str(value)
        return None

    def add_links(self, current_output: str) -> str:
        if 'link' in self.host.attributes:
            link = sanitize_url(self.host.attributes['link'])
            if link:
                current_output = f'<a href="{link}">{current_output}</a>'
        if 'anchor' in self.host.attributes:
            anchor_id = _html.escape(self.host.attributes['anchor'], quote=True)
            current_output = f'<a class="anchor" id="{anchor_id}">{current_output}</a>'
        return current_output

    def pre_process_line(self, line: str) -> str:
        return _html.escape(line)

    def process_line_with_attributes(self, text_string: str, debug: bool = False) -> str:
        output = text_string
        attrs = self.host.attributes

        # Inline code wrapping
        if attrs.get('code'):
            output = f'<code>{output}</code>'

        for this_i, (open_tag, close_tag) in self.standard_inline_styles.items():
            if attrs.get(this_i):
                output = open_tag + output + close_tag

        script_val = attrs.get('script')
        if script_val and script_val in self.script_styles:
            open_tag, close_tag = self.script_styles[script_val]
            output = open_tag + output + close_tag

        css_styles: list[str] = []
        for qflag, css_attribute, translator in self.text_span_css:
            if qflag in attrs:
                if not translator:
                    value = self._sanitize_css_value(attrs[qflag])
                    if value:
                        css_styles.append(f"{css_attribute}: {value}")
                else:
                    translated = getattr(self, translator).get(attrs[qflag], None)
                    if translated:
                        css_styles.append(f"{css_attribute}: {translated}")

        these_css_classes: list[str] = []
        for qflag, translator in self.css_classes:
            if qflag in attrs:
                translated = getattr(self, translator).get(attrs[qflag], None)
                if translated:
                    these_css_classes.append(translated)

        if css_styles:
            css_styles_string = ';'.join(css_styles)
            output = f'<span style="{css_styles_string}">{output}</span>'

        if these_css_classes:
            css_classes_string = ' '.join(these_css_classes)
            output = f'<span class="{css_classes_string}">{output}</span>'

        for fname in self.post_processing:
            f = getattr(self, fname)
            output = f(output)

        return output
