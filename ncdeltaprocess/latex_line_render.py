"""LaTeX inline rendering for Quill delta text runs.

LineRenderLaTeX converts individual text runs (with their Quill attributes)
into LaTeX markup. It is the LaTeX counterpart to the HTML line renderer.

Required LaTeX packages::

    \\usepackage{hyperref}          % \\href, \\hyperlink, \\hypertarget
    \\usepackage[normalem]{ulem}    % \\sout (strikethrough)
"""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

from .sanitize import sanitize_latex_label, sanitize_latex_url

if TYPE_CHECKING:
    from .node import TextLine

try:
    from pylatexenc.latexencode import unicode_to_latex
except ImportError:
    def unicode_to_latex(text: str) -> str:
        """Fallback LaTeX escaping when pylatexenc is not installed."""
        # Order matters: escape backslash first, then braces, then the rest.
        # Use sentinel to avoid re-escaping braces introduced by replacements.
        _LBRACE = '\x00LBRACE\x00'
        _RBRACE = '\x00RBRACE\x00'
        text = text.replace("\\", f"\\textbackslash{_LBRACE}{_RBRACE}")
        text = text.replace("{", f"\\{_LBRACE}")
        text = text.replace("}", f"\\{_RBRACE}")
        text = text.replace(_LBRACE, "{")
        text = text.replace(_RBRACE, "}")
        for char, replacement in [
            ("&", "\\&"), ("%", "\\%"), ("$", "\\$"),
            ("#", "\\#"), ("_", "\\_"),
            ("~", "\\textasciitilde{}"), ("^", "\\textasciicircum{}"),
        ]:
            text = text.replace(char, replacement)
        return text


class LineRenderLaTeX(object):
    """Renders a single text run (with Quill attributes) to LaTeX.

    Attributes:
        host: Weak reference to the owning ``TextLine`` node. Provides
            ``host.attributes`` (the Quill inline attributes dict, e.g.
            bold, italic, link, size) and ``host.contents`` (the raw
            text string). Stored as a ``weakref.proxy`` to avoid circular
            references (TextLine → renderer → TextLine).
    """

    def __init__(self, host: TextLine) -> None:
        self.host: TextLine = weakref.proxy(host)

    standard_inline_styles: dict[str, tuple[str, str]] = {
        'italic': (r'\emph{', r'}'),
        'bold': (r'\textbf{', r'}'),
        'strike': (r'\sout{', r'}'),
        'underline': (r'\underline{', r'}'),
    }

    script_styles: dict[str, tuple[str, str]] = {
        'sub': (r'\textsubscript{', r'}'),
        'super': (r'\textsuperscript{', r'}'),
    }

    font_sizes: dict[str, str] = {
        'small': r'\small',
        'normal': r'\normalsize',
        'large': r'\large',
        'huge': r'\huge',
    }

    font_types: dict[str, str] = {
        'monospace': r'\texttt',
        'serif': r'\textrm',
        'sans-serif': r'\textsf',
    }

    def pre_process_line(self, text_line: str) -> str:
        """Escape a plain text string for safe inclusion in LaTeX."""
        return unicode_to_latex(text_line)

    def process_line_with_attributes(self, text_line: str) -> str:
        """Convert a text run to LaTeX, wrapping with commands for active attributes."""
        output = self.pre_process_line(text_line)
        attrs = self.host.attributes

        # Inline code
        if attrs.get('code'):
            output = r'\texttt{' + output + r'}'

        for this_i, (open_cmd, close_cmd) in self.standard_inline_styles.items():
            if attrs.get(this_i):
                output = open_cmd + output + close_cmd

        link = attrs.get('link')
        if link:
            if link.startswith('#'):
                safe_label = sanitize_latex_label(link[1:])
                output = r'\hyperlink{' + safe_label + '}{' + output + '}'
            else:
                safe_link = sanitize_latex_url(link)
                output = r'\href{' + safe_link + '}{' + output + '}'

        script_val = attrs.get('script')
        if script_val and script_val in self.script_styles:
            open_cmd, close_cmd = self.script_styles[script_val]
            output = open_cmd + output + close_cmd

        size = attrs.get('size')
        if size and size in self.font_sizes:
            output = f'{{{self.font_sizes[size]} {output} }}'

        font = attrs.get('font')
        if font and font in self.font_types:
            output = f'{self.font_types[font]}{{{output}}}'

        anchor = attrs.get('anchor')
        if anchor:
            safe_anchor = sanitize_latex_label(anchor)
            output = r'\hypertarget{' + safe_anchor + r'}{}' + output

        return output
