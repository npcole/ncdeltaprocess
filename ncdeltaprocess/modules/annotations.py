"""Module for annotation and footnote support.

Handles:
- annotation-content blocks (stored in document data_blocks)
- annotation-marker inline nodes (Annotation type → inline, Footnote type → end-matter)
"""

from __future__ import annotations

from typing import Any
from .. import block as bks
from .. import node
from ..document import QDocument
from . import ModuleBase


class AnnotationModule(ModuleBase):
    """Module plugin for annotation/footnote handlers."""
    block_registry: dict[str, str] = {
        'annotation_block_test': 'make_annotation_block',
    }
    node_registry: dict[str, str] = {
        'annotation_node_an_test': 'make_annotation_marker_node',
        'annotation_node_fn_test': 'make_footnote_marker_node',
    }

    def annotation_block_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        return 'annotation-content' in qblock['attributes']

    def annotation_node_an_test(
        self, block: bks.Block, contents: Any, attributes: dict[str, Any],
    ) -> bool:
        return ('annotation-marker' in attributes
                and attributes['annotation-marker']['type'] == 'Annotation')

    def annotation_node_fn_test(
        self, block: bks.Block, contents: Any, attributes: dict[str, Any],
    ) -> bool:
        return ('annotation-marker' in attributes
                and attributes['annotation-marker']['type'] == 'Footnote')

    def make_annotation_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        annotation_id = qblock['attributes']['annotation-content']['id']
        if annotation_id in this_document.block_index:
            this_block = this_document.block_index[annotation_id]
        else:
            this_block = this_document.add_block(
                bks.AnnotationBlockContents(
                    parent=this_document,
                    last_block=previous_block,
                    attributes=qblock['attributes'].copy(),
                ),
                this_type='data',
            )
            this_document.block_index[annotation_id] = this_block
        attr = qblock['attributes'].copy()
        del attr['annotation-content']
        text_block = this_block.add_block(
            bks.TextBlockPlain(
                last_block=previous_block,
                attributes=attr,
            )
        )
        return text_block

    def make_annotation_marker_node(
        self, block: bks.Block, contents: Any, attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.AnnotationMarkerNode(contents=contents, attributes=attributes)
        )

    def make_footnote_marker_node(
        self, block: bks.Block, contents: Any, attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.FootnoteMarkerNode(contents=contents, attributes=attributes)
        )
