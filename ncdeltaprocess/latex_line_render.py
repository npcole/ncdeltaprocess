"""LaTeX inline rendering for Quill delta text runs.

LineRenderLaTeX converts individual text runs (with their Quill attributes)
into LaTeX markup. It is the LaTeX counterpart to the HTML line renderer.

Required LaTeX packages::

    \\usepackage{hyperref}          % \\href, \\hyperlink, \\hypertarget
    \\usepackage[normalem]{ulem}    % \\sout (strikethrough)
    \\usepackage{changes}           % \\added, \\deleted, \\highlight (diff markup)
"""

from __future__ import annotations

import re
import weakref
from typing import TYPE_CHECKING

from .sanitize import sanitize_latex_label, sanitize_latex_url

if TYPE_CHECKING:
    from .node import TextLine

try:
    from pylatexenc.latexencode import (
        UnicodeToLatexEncoder,
        UnicodeToLatexConversionRule,
        RULE_DICT,
    )

    # Extra mappings for characters pylatexenc doesn't know about.
    # Rendered using textcomp or math-mode equivalents that work with
    # standard pdflatex + utf8 inputenc.
    _EXTRA_LATEX_CHARS = {
        # ``[`` and ``]`` are wrapped ``{[}`` / ``{]}`` so LaTeX
        # doesn't mistake them for an optional argument to a preceding
        # ``\par`` / ``\\`` / ``\item`` etc. Folded into the encoder
        # dict (rather than a separate ``.replace()`` pass after
        # encoding) so bracket protection costs nothing extra per call.
        ord('['): r'{[}',
        ord(']'): r'{]}',
        ord('₵'): r'\textcent{}',          # ₵ Ghanaian cedi sign (closest available)
        ord('₦'): r'N\hspace{-0.3em}=',    # ₦ Nigerian naira sign
        ord('₱'): r'P\hspace{-0.3em}=',    # ₱ Philippine peso sign
        ord('₺'): r'TL',                    # ₺ Turkish lira sign
        ord('₹'): r'Rs',                    # ₹ Indian rupee sign
        ord('₫'): r'\dj{}',                 # ₫ Vietnamese dong sign
        ord('₿'): r'BTC',                   # ₿ Bitcoin sign
        ord('•'): r'\textbullet{}',         # • bullet
        ord('–'): r'\textendash{}',         # – en dash
        ord('—'): r'\textemdash{}',         # — em dash
        ord('‘'): r'\textquoteleft{}',      # ' left single quote
        ord('’'): r'\textquoteright{}',     # ' right single quote
        ord('“'): r'\textquotedblleft{}',   # " left double quote
        ord('”'): r'\textquotedblright{}',  # " right double quote
        ord('…'): r'\ldots{}',              # … ellipsis
        ord(' '): r'~',                     # non-breaking space
    }

    _encoder = UnicodeToLatexEncoder(
        conversion_rules=[
            UnicodeToLatexConversionRule(
                rule_type=RULE_DICT,
                rule=_EXTRA_LATEX_CHARS,
            ),
            'defaults',
        ],
        unknown_char_policy='replace',
        unknown_char_warning=True,
    )

    def unicode_to_latex(text: str) -> str:
        return _encoder.unicode_to_latex(text)

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
            # Bracket protection — see note on _EXTRA_LATEX_CHARS above.
            ("[", "{[}"), ("]", "{]}"),
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
        # \uline (ulem) underlines at a fixed depth regardless of descenders and
        # breaks across lines — unlike \underline, which sits at a different
        # height per word and overflows the margin. Requires
        # \usepackage[normalem]{ulem} in the document preamble.
        'underline': (r'\uline{', r'}'),
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

    # Maps ncquill_diff / quill_diff attribute values to LaTeX commands
    # from the ``changes`` package. ``\hspace{0pt}`` after the closing
    # brace inserts a zero-width breakpoint so adjacent diff commands
    # don't merge visually, without adding any visible space before
    # punctuation.
    diff_commands: dict[str, tuple[str, str]] = {
        'new': (r'\added{', r'}\hspace{0pt}'),
        'insert': (r'\added{', r'}\hspace{0pt}'),
        'removed': (r'\deleted{', r'}\hspace{0pt}'),
        'delete': (r'\deleted{', r'}\hspace{0pt}'),
        'edited': (r'\highlight{', r'}\hspace{0pt}'),
    }

    def pre_process_line(self, text_line: str) -> str:
        """Escape a plain text string for safe inclusion in LaTeX.

        Bracket protection (``[`` → ``{[}`` / ``]`` → ``{]}``) is
        folded into the encoder's char map, so the single
        ``unicode_to_latex`` pass handles everything.
        """
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

        # Diff markup (ncquill_diff or quill_diff attributes). Applied
        # last so it wraps all other formatting.
        diff_val = attrs.get('ncquill_diff') or attrs.get('quill_diff')
        if diff_val and diff_val in self.diff_commands:
            open_cmd, close_cmd = self.diff_commands[diff_val]
            output = open_cmd + output + close_cmd

        return output


# Inline-style commands whose adjacent groups should read as one continuous run.
# A Quill delta often fragments a styled phrase across several ops (e.g.
# "ex post facto" as three underlined ops), which renders as
# ``\uline{ex} \uline{post} \uline{facto}`` — choppy per-word styling with the
# inter-word spaces left *outside* the rule. ``merge_adjacent_inline_styles``
# folds such neighbours, separated only by whitespace or a ``~`` tie, back
# together so they render continuously.
_INLINE_MERGE_CMDS = ('uline', 'emph', 'textbf', 'sout')


def merge_adjacent_inline_styles(latex: str) -> str:
    """Merge adjacent identical inline-style groups separated only by
    whitespace, so a run-fragmented styled phrase renders as one run.

    Conservative by design: only folds neighbours with the *same* command and
    brace-free content (so nested commands like ``\\uline{\\textbf{x}}`` and
    runs separated by real text are left untouched), and never touches the diff
    commands (``\\added`` / ``\\deleted``).
    """
    if not latex:
        return latex
    for cmd in _INLINE_MERGE_CMDS:
        pattern = re.compile(
            r'\\' + cmd + r'\{([^{}]*)\}([ ~\t]+)\\' + cmd + r'\{([^{}]*)\}')
        prev = None
        while prev != latex:           # fold runs of three or more
            prev = latex
            latex = pattern.sub(r'\\' + cmd + r'{\1\2\3}', latex)
    return latex


# Diff markup commands (the ``changes`` package) emitted by ``diff_commands``
# above, each closed with ``}\hspace{0pt}``.
_DIFF_MERGE_CMDS = ('added', 'deleted', 'highlight')


def strip_empty_diff_commands(latex: str) -> str:
    """Drop empty diff markers (``\\added{}\\hspace{0pt}`` etc.).

    A run-fragmented diff often emits empty change commands at op boundaries;
    they render nothing but each is still a ``changes``-package call the LaTeX
    engine must process. Removing them is purely cosmetic-free.
    """
    if not latex:
        return latex
    for cmd in _DIFF_MERGE_CMDS:
        latex = latex.replace('\\' + cmd + '{}\\hspace{0pt}', '')
    return latex


def merge_adjacent_diff_commands(latex: str) -> str:
    """Coalesce consecutive **same-status** diff commands into one.

    ``\\added{A}\\hspace{0pt}\\added{B}\\hspace{0pt}`` →
    ``\\added{AB}\\hspace{0pt}``. A document changed throughout (e.g. a clause
    reformatted word-by-word) otherwise renders as thousands of separate
    ``\\added``/``\\deleted`` commands — each a comparatively slow ``changes``-
    package invocation — which bloats the LaTeX and can make it compile-bound
    (the redline of a ~120KB document produced ~210KB of markup and timed out).

    Conservative by design, mirroring :func:`merge_adjacent_inline_styles`: only
    **brace-free** content is folded (so nested formatting like
    ``\\added{\\textbf{x}}`` is left untouched), and **different** statuses
    (``\\added`` vs ``\\deleted``) are never merged. The dropped inter-command
    ``\\hspace{0pt}`` is a zero-width breakpoint only; the merged run keeps its
    own trailing one and still breaks at the spaces inside it.
    """
    if not latex:
        return latex
    latex = strip_empty_diff_commands(latex)
    for cmd in _DIFF_MERGE_CMDS:
        pattern = re.compile(
            r'\\' + cmd + r'\{([^{}]*)\}\\hspace\{0pt\}\\' + cmd + r'\{([^{}]*)\}')
        prev = None
        while prev != latex:           # fold runs of three or more
            prev = latex
            latex = pattern.sub(r'\\' + cmd + r'{\1\2}', latex)
    return pair_adjacent_diff_replacements(latex)


# An added run immediately followed by a deleted run is a *replacement* — the
# diff renders it added-then-deleted (new text, then the struck-through old).
_REPLACE_PAIR_RE = re.compile(
    r'\\added\{([^{}]*)\}\\hspace\{0pt\}\\deleted\{([^{}]*)\}\\hspace\{0pt\}')


def pair_adjacent_diff_replacements(latex: str) -> str:
    """Fold an adjacent added+deleted pair into a single ``\\replaced`` command.

    ``\\added{new}\\hspace{0pt}\\deleted{old}\\hspace{0pt}`` →
    ``\\replaced{new}{old}\\hspace{0pt}``. The diff renders every word-level
    edit as a *replacement* — an added run (the new text) immediately followed
    by a deleted run (the struck-through old text) — i.e. two ``changes``-package
    commands. ``\\replaced{new}{old}`` is the package's own single-command form
    for exactly this, rendering identically (new text, then old struck) while
    roughly halving the comparatively slow ``changes`` commands in heavily-
    revised text. Conservative: only brace-free operands are folded, so a pair
    wrapping nested formatting is left as the explicit add/delete.
    """
    if not latex:
        return latex
    return _REPLACE_PAIR_RE.sub(r'\\replaced{\1}{\2}\\hspace{0pt}', latex)
