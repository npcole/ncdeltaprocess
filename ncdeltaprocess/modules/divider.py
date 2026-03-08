"""Module for divider (horizontal rule) support.

Handles divider embeds as block-level elements: {'insert': {'divider': true}}
"""

from __future__ import annotations

from typing import Any
from .. import block as bks
from .. import node
from ..document import QDocument
from . import ModuleBase


class DividerModule(ModuleBase):
    """Module plugin for divider/horizontal rule handlers."""
    block_registry: dict[str, str] = {
        'divider_block_test': 'make_divider_block',
    }
    node_registry: dict[str, str] = {
        'divider_node_test': 'make_divider_node',
    }

    def is_block_embed(self, insert_instruction: Any) -> bool:
        return isinstance(insert_instruction, dict) and 'divider' in insert_instruction

    def divider_block_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        """A block whose only content is a divider embed."""
        return (len(qblock['contents']) == 1
                and isinstance(qblock['contents'][0].get('insert'), dict)
                and 'divider' in qblock['contents'][0]['insert'])

    def divider_node_test(
        self, block: bks.Block, contents: Any, attributes: dict[str, Any],
    ) -> bool:
        return isinstance(contents, dict) and 'divider' in contents

    def make_divider_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        """Create a tagless wrapper block for a block-level divider."""
        return this_document.add_block(
            bks.TextBlockPlain(
                parent=this_document,
                last_block=previous_block,
            )
        )

    def make_divider_node(
        self, block: bks.Block, contents: dict[str, Any], attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.DividerNode(contents=contents, attributes=attributes)
        )
