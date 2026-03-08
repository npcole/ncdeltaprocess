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

    def render_tree(self, mode: str = 'html') -> str:
        """A non-recursive way to render the tree.

        Uses set-based visited tracking with id() for O(1) lookups
        and cycle detection to prevent infinite loops.
        """
        open_block_call = self.modes[mode]['open_block']
        render_call = self.modes[mode]['render_block']
        close_block_call = self.modes[mode]['close_block']
        output = self.modes[mode]['output_object']()

        stack: list[RenderMixin] = []
        already_visited: set[int] = set()
        stack.append(self)
        while stack:
            this_node = stack.pop()
            node_id = id(this_node)
            if node_id not in already_visited:
                already_visited.add(node_id)
                if this_node.is_leaf:
                    output.append(getattr(this_node, render_call)(output))
                else:
                    if hasattr(this_node, open_block_call):
                        output.append(getattr(this_node, open_block_call)(output))
                    if hasattr(this_node, close_block_call):
                        stack.append(this_node)
                    for c in reversed(this_node.contents):
                        stack.append(c)
            else:
                if this_node.is_leaf:
                    pass
                else:
                    if hasattr(this_node, close_block_call):
                        output.append(getattr(this_node, close_block_call)(output))
        return output.merge()


class RenderOpenCloseMixin(RenderMixin):
    def open_tag(self, output_object: OutputObject) -> str:
        return ''

    def close_tag(self, output_object: OutputObject) -> str:
        return ''
