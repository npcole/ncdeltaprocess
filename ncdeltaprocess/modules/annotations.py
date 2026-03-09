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
from .lists import ListModule

# Compound attribute keys that embed annotation-content inside a block format.
_COMPOUND_KEYS: dict[str, str] = {
    'annotated-list': 'list',
    'annotated-blockquote': 'blockquote',
    'annotated-code-block': 'code-block',
}


def _is_valid_annotation_content(value: object) -> bool:
    """Return True if value is a dict with a string 'id' key."""
    return isinstance(value, dict) and isinstance(value.get('id'), str)


def _extract_annotation_content(
    attributes: dict[str, Any],
) -> tuple[dict[str, Any], str | None, str | bool | None] | None:
    """Extract annotation-content metadata from any attribute shape.

    Returns (annotation_content_dict, block_format_key, block_format_value)
    or None if no annotation content is present or the shape is malformed.

    Supported shapes:
    - Direct:   {'annotation-content': {...}}
    - Sibling:  {'annotation-content': {...}, 'list': 'bullet'}
    - Compound: {'annotated-list': {'list': 'bullet', 'annotation-content': {...}}}
    """
    # Direct / sibling format
    if 'annotation-content' in attributes:
        ann = attributes['annotation-content']
        if not _is_valid_annotation_content(ann):
            return None
        # Check for sibling block format keys
        if 'list' in attributes:
            return (ann, 'list', attributes['list'])
        if 'blockquote' in attributes:
            return (ann, 'blockquote', attributes['blockquote'])
        if 'code-block' in attributes:
            return (ann, 'code-block', attributes['code-block'])
        return (ann, None, None)

    # Compound format
    for compound_key, format_key in _COMPOUND_KEYS.items():
        if compound_key in attributes:
            compound = attributes[compound_key]
            if not isinstance(compound, dict):
                continue
            if 'annotation-content' in compound:
                ann = compound['annotation-content']
                if not _is_valid_annotation_content(ann):
                    continue
                return (ann, format_key, compound.get(format_key))
    return None


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
        return _extract_annotation_content(qblock['attributes']) is not None

    def annotation_node_an_test(
        self, block: bks.Block, contents: str | dict[str, Any], attributes: dict[str, Any],
    ) -> bool:
        return ('annotation-marker' in attributes
                and attributes['annotation-marker']['type'] == 'Annotation')

    def annotation_node_fn_test(
        self, block: bks.Block, contents: str | dict[str, Any], attributes: dict[str, Any],
    ) -> bool:
        return ('annotation-marker' in attributes
                and attributes['annotation-marker']['type'] == 'Footnote')

    def make_annotation_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        extracted = _extract_annotation_content(qblock['attributes'])
        ann_content, format_key, format_value = extracted

        annotation_id = ann_content['id']
        if annotation_id in this_document.block_index:
            container = this_document.block_index[annotation_id]
        else:
            # Build attributes dict that AnnotationBlockContents.__init__ expects
            container_attrs = {'annotation-content': ann_content}
            container = this_document.add_block(
                bks.AnnotationBlockContents(
                    parent=this_document,
                    last_block=previous_block,
                    attributes=container_attrs,
                ),
                this_type='data',
            )
            this_document.block_index[annotation_id] = container

        if format_key == 'list':
            return self._make_annotation_list_item(
                container, previous_block, qblock['attributes'], format_value,
            )
        elif format_key == 'blockquote':
            return container.add_block(
                bks.TextBlockParagraph(
                    parent=container,
                    last_block=previous_block,
                    attributes={'blockquote': True},
                )
            )
        elif format_key == 'code-block':
            return self._make_annotation_code_block(
                container, previous_block, format_value,
            )
        else:
            return container.add_block(
                bks.TextBlockPlain(
                    last_block=previous_block,
                    attributes={},
                )
            )

    def _make_annotation_list_item(
        self,
        container: bks.AnnotationBlockContents,
        previous_block: bks.Block | None,
        attributes: dict[str, Any],
        list_type: str,
    ) -> bks.Block:
        """Create a list item structure inside an annotation container."""
        required_depth: int = attributes.get('indent', 0) or 0
        list_container: bks.Block | None = None

        # Look for existing ListItemBlock ancestors from previous_block
        if previous_block is not None:
            ann_id = container.annotation_id
            lb_parents: list[bks.ListItemBlock] = [
                p for p in previous_block.get_parents()
                if isinstance(p, bks.ListItemBlock)
                and getattr(
                    p.find_ancestor(bks.AnnotationBlockContents),
                    'annotation_id', None,
                ) == ann_id
            ]
        else:
            lb_parents = []

        if lb_parents and (
            'indent' not in lb_parents[0].attributes
            or lb_parents[0].attributes['indent'] is None
        ):
            lb_parents[0].attributes['indent'] = 0

        if lb_parents and lb_parents[0].attributes.get('indent', 0) == required_depth:
            list_container = lb_parents[0].parent
        elif lb_parents and lb_parents[0].attributes.get('indent', 0) < required_depth:
            list_container = ListModule._build_list_depth(
                lb_parents[0], required_depth, list_type, attributes,
            )
        else:
            for candidate in lb_parents:
                if candidate.attributes.get('indent', 0) == required_depth:
                    list_container = candidate.parent
                    break

        if list_container is None:
            list_container = container.add_block(
                bks.ListBlock(
                    list_type=list_type,
                    parent=container,
                    last_block=previous_block,
                    attributes={},
                )
            )
            list_container = ListModule._build_list_depth(
                list_container, required_depth, list_type, attributes,
            )

        item = list_container.add_block(
            bks.ListItemBlock(
                parent=list_container,
                last_block=previous_block,
                attributes={'list': list_type, 'indent': required_depth},
            )
        )
        return item.add_block(
            bks.TextBlockPlain(
                parent=item,
                last_block=previous_block,
                attributes={},
            )
        )

    def _make_annotation_code_block(
        self,
        container: bks.AnnotationBlockContents,
        previous_block: bks.Block | None,
        language: str | bool | None,
    ) -> bks.Block:
        """Create or merge a code block inside an annotation container."""
        code_attrs = {'code-block': language if isinstance(language, str) else True}
        # Merge consecutive code blocks with matching attributes
        if container.contents:
            last = container.contents[-1]
            if isinstance(last, bks.TextBlockCode) and last.attributes == code_attrs:
                return last
        return container.add_block(
            bks.TextBlockCode(
                parent=container,
                last_block=previous_block,
                attributes=code_attrs,
            )
        )

    def make_annotation_marker_node(
        self, block: bks.Block, contents: str | dict[str, Any], attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.AnnotationMarkerNode(contents=contents, attributes=attributes)
        )

    def make_footnote_marker_node(
        self, block: bks.Block, contents: str | dict[str, Any], attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.FootnoteMarkerNode(contents=contents, attributes=attributes)
        )
