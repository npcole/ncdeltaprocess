"""Rendering mixins for multi-format output (HTML, LaTeX)."""

from __future__ import annotations

import itertools

__all__ = ['RenderMixin', 'RenderOpenCloseMixin', 'OutputObject']


class OutputObject(object):
    """Accumulates front matter, body contents, and end matter during rendering."""
    def __init__(self) -> None:
        self.front_matter: list[str] = []
        self.contents: list[str] = []
        self.end_matter: list[str] = []
        self.fn_count: int = 0
        self.heading_base_level: int = 0
        # Per-row cell counter for LaTeX table rendering. A row's
        # ``open_latex`` pushes 0 here, each cell increments and reads,
        # and the row's ``close_latex`` pops. Stack form supports
        # nested tables.
        self.cell_position_stack: list[int] = []

    def append(self, content: str) -> None:
        return self.contents.append(content)

    def extend(self, content: list[str]) -> None:
        return self.contents.extend(content)

    def merge(self) -> str:
        return ''.join(
            itertools.chain(self.front_matter, self.contents, self.end_matter)
        )


class RenderMixin(object):
    modes: dict[str, dict[str, str | type]] = {
        'html': {
            'output_object': OutputObject,
            'open_block': 'open_tag',
            'render_block': 'render_contents_html',
            'close_block': 'close_tag'
        },
        'latex': {
            'output_object': OutputObject,
            'open_block': 'open_latex',
            'render_block': 'render_contents_latex',
            'close_block': 'close_latex'
        }
    }

    def render_tree(
        self,
        mode: str = 'html',
        heading_base_level: int | None = None,
    ) -> str:
        """Iteratively render the document tree.

        Each non-leaf block is pushed twice: once as ``(node, False)``
        so its open marker fires and its children are queued, then
        re-pushed as ``(node, True)`` so the second pop emits its close
        marker. Leaves are pushed once. The document is assumed to be a
        proper tree — no cycle detection is performed.

        Args:
            mode: ``'html'`` or ``'latex'``.
            heading_base_level: If set, offset applied to heading levels
                in the output. For example, ``heading_base_level=3``
                maps h1→h4 in HTML and h1→``\\paragraph`` in LaTeX.
                Useful for embedding document content inside a larger
                report without clashing with the report's section
                numbering.
        """
        open_block_call = self.modes[mode]['open_block']
        render_call = self.modes[mode]['render_block']
        close_block_call = self.modes[mode]['close_block']
        output = self.modes[mode]['output_object']()
        if heading_base_level is not None:
            output.heading_base_level = heading_base_level

        stack: list[tuple[RenderMixin, bool]] = [(self, False)]
        while stack:
            this_node, is_close = stack.pop()
            if is_close:
                close = getattr(this_node, close_block_call, None)
                if close is not None:
                    output.append(close(output))
            elif this_node.is_leaf:
                output.append(getattr(this_node, render_call)(output))
            else:
                open_fn = getattr(this_node, open_block_call, None)
                if open_fn is not None:
                    output.append(open_fn(output))
                if hasattr(this_node, close_block_call):
                    stack.append((this_node, True))
                for c in reversed(this_node.contents):
                    stack.append((c, False))
        return output.merge()


class RenderOpenCloseMixin(RenderMixin):
    def open_tag(self, output_object: OutputObject) -> str:
        return ''

    def close_tag(self, output_object: OutputObject) -> str:
        return ''
