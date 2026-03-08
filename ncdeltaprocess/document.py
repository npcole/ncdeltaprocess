"""QDocument — root container for the parsed document tree."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING
from .render import RenderMixin

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

    @property
    def depth(self) -> int:
        return -1

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
