"""Module for list support.

Handles bullet, ordered, checked, and unchecked list types
with arbitrary nesting via indent attributes.
"""

from __future__ import annotations

from typing import Any
from .. import block as bks
from ..document import QDocument
from . import ModuleBase


class ListModule(ModuleBase):
    """Module plugin for list handlers."""
    block_registry: dict[str, str] = {
        'list_test': 'make_list_block',
    }

    def list_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        return ('list' in qblock['attributes']
                and 'annotation-content' not in qblock['attributes'])

    @staticmethod
    def _build_list_depth(
        container: bks.Block,
        target_depth: int,
        list_type: str,
        attributes: dict[str, Any],
    ) -> bks.Block:
        """Build nested ListBlock/ListItemBlock pairs up to target_depth."""
        while target_depth > (container.attributes.get('indent', 0) or 0):
            current_depth: int = container.attributes.get('indent', 0) or 0
            if isinstance(container, bks.ListBlock):
                container = container.add_block(
                    bks.ListItemBlock(
                        parent=container,
                        last_block=container,
                        attributes=attributes.copy(),
                    )
                )
                container.attributes['indent'] = current_depth + 1
            container = container.add_block(
                bks.ListBlock(
                    list_type=list_type,
                    parent=container,
                    last_block=container,
                    attributes=attributes.copy(),
                )
            )
            container.attributes['indent'] = current_depth + 1
        return container

    def make_list_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        container_block: bks.Block | None = None
        required_depth: int = qblock['attributes'].get('indent', 0) or 0
        list_type: str = qblock['attributes']['list']

        # Find parent list blocks from previous block
        if previous_block:
            lb_parents: list[bks.ListItemBlock] = [
                p for p in previous_block.get_parents()
                if isinstance(p, bks.ListItemBlock)
            ]
        else:
            lb_parents = []

        if lb_parents and (
            'indent' not in lb_parents[0].attributes
            or lb_parents[0].attributes['indent'] is None
        ):
            lb_parents[0].attributes['indent'] = 0

        if lb_parents and lb_parents[0].attributes.get('indent', 0) == required_depth:
            # Same depth — add to the parent ListBlock (not the ListItemBlock)
            container_block = lb_parents[0].parent
        elif lb_parents and lb_parents[0].attributes.get('indent', 0) < required_depth:
            # Deeper — build up to the required depth
            container_block = self._build_list_depth(
                lb_parents[0], required_depth, list_type, qblock['attributes'],
            )
        else:
            # Search for a parent at the required depth
            container_block = None
            for candidate_block in lb_parents:
                if candidate_block.attributes.get('indent', 0) == required_depth:
                    container_block = candidate_block.parent  # the ListBlock
                    break
            else:
                if (required_depth > 0 and previous_block
                        and previous_block.attributes.get('indent', 0) == required_depth):
                    container_block = previous_block.add_block(
                        bks.ListBlock(
                            list_type=list_type,
                            parent=container_block,
                            last_block=container_block,
                            attributes=qblock['attributes'].copy(),
                        )
                    )
                else:
                    # Fall back to root document, building up depth
                    container_block = this_document.add_block(
                        bks.ListBlock(
                            list_type=list_type,
                            parent=container_block,
                            last_block=container_block,
                            attributes=qblock['attributes'].copy(),
                        )
                    )
                    container_block = self._build_list_depth(
                        container_block, required_depth, list_type, qblock['attributes'],
                    )

        # Wrap in a list item
        container_block = container_block.add_block(
            bks.ListItemBlock(
                parent=container_block,
                last_block=container_block,
                attributes=qblock['attributes'].copy(),
            )
        )

        if self.parent.settings['list_text_blocks_are_p']:
            this_block = container_block.add_block(
                bks.TextBlockParagraph(
                    parent=container_block,
                    last_block=previous_block,
                    attributes=qblock['attributes'].copy(),
                )
            )
        else:
            this_block = container_block.add_block(
                bks.TextBlockPlain(
                    parent=container_block,
                    last_block=previous_block,
                    attributes=qblock['attributes'].copy(),
                )
            )
        return this_block
