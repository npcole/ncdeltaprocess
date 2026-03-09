"""QDocument — root container for the parsed document tree."""

from __future__ import annotations

import weakref
from typing import Any, TYPE_CHECKING
from .render import RenderMixin, OutputObject

if TYPE_CHECKING:
    from .block import Block

__all__ = ['QDocument']


class QDocument(RenderMixin):
    is_leaf = False

    def __init__(self) -> None:
        self.contents: list[Block] = []
        self.hidden_blocks: list[Block] = []
        self.data_blocks: list[Block] = []
        self.block_index: dict[str, Block] = {}
        self.settings: dict[str, Any] = {}

    @property
    def depth(self) -> int:
        return -1

    def open_tag(self, output_object: OutputObject) -> str:
        if not self.settings.get('render_annotation_content_blocks', True):
            return ''
        from .block import AnnotationBlockContents
        parts: list[str] = []
        for block in self.data_blocks:
            if isinstance(block, AnnotationBlockContents):
                parts.append(block.render_tree())
        return ''.join(parts)

    def add_block(self, block: Block, this_type: str = 'contents') -> Block:
        match this_type:
            case 'contents':
                this_blocklist = self.contents
            case 'hidden':
                this_blocklist = self.hidden_blocks
            case 'data':
                this_blocklist = self.data_blocks
            case _:
                raise ValueError(f'Invalid {this_type=} specified.')
        if this_blocklist:
            block.previous_block = this_blocklist[-1]
        block.parent = weakref.proxy(self)
        this_blocklist.append(block)
        return block
