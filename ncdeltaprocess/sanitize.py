"""Shared URL and CSS sanitization utilities."""

from __future__ import annotations

import html as _html
import re

_dangerous_url_schemes: frozenset[str] = frozenset(['javascript', 'vbscript', 'data'])

CSS_SAFE_PATTERN: re.Pattern[str] = re.compile(r'^[a-zA-Z0-9#(),.\s%-]+$')


def sanitize_latex_label(label: str) -> str:
    """Escape characters that break TeX parsing in label arguments.

    Used for ``\\hypertarget`` and ``\\hyperlink`` labels.  Lighter than
    ``unicode_to_latex()`` — only strips the characters that cause TeX
    tokenizer errors, preserving underscores and other common ID characters
    so that label matching between targets and links is not disrupted.
    """
    for char in ('\\', '{', '}', '#', '%'):
        label = label.replace(char, '')
    return label


def sanitize_latex_url(url: str) -> str:
    """Escape characters that break TeX parsing in a URL argument.

    Handles ``\\href`` and ``\\includegraphics`` — URL-encodes the
    characters that cause TeX tokenizer errors before hyperref can
    process them.  Leaves ``%`` and ``#`` alone since hyperref handles
    those internally via catcode changes.
    """
    url = url.replace('\\', '%5C')
    url = url.replace('{', '%7B')
    url = url.replace('}', '%7D')
    return url


def sanitize_url(url: str, *, allow_data: bool = False) -> str:
    """Escape HTML entities and block dangerous URI schemes.

    Args:
        url: The URL to sanitize.
        allow_data: If True, permit data: URIs (safe for <img src>,
            dangerous for <a href>).
    """
    url = _html.escape(url, quote=True)
    scheme = url.split(':', 1)[0].lower().strip() if ':' in url else ''
    if scheme in _dangerous_url_schemes:
        if not (allow_data and scheme == 'data'):
            return ''
    return url
