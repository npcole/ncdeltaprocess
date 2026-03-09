"""Translator classes for converting Quill Delta ops into a document tree."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
from .document import QDocument
from . import block as bks
from . import node
from .modules.annotations import AnnotationModule
from .modules.divider import DividerModule
from .modules.lists import ListModule
from .modules.table_quill2 import TableQuill2Module
from .modules.table_better_table import BetterTableModule
import warnings
import copy

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from .modules import ModuleBase

__all__ = ['TranslatorBase', 'TranslatorQuillJS']

# Type alias for a single Quill Delta operation dict.
DeltaOp = dict[str, Any]


class TranslatorBase(object):
    """Base class for Delta format translators.

    Provides a module/plugin system, block and node registries, and the core
    ``ops_to_internal_representation`` method that converts Quill Delta ops
    into a QDocument tree.
    """
    def __init__(self, diff_mode: bool = False) -> None:
        self.DIFF_MODE: bool = diff_mode
        self._modules: list[ModuleBase] = []
        self.block_registry: dict[Callable[..., bool], Callable[..., bks.Block]] = {}
        self.node_registry: dict[Callable[..., bool], Callable[..., node.Node]] = {}
        self.settings: dict[str, Any] = {
            'list_text_blocks_are_p': True,
            'list_better_table_cells_are_p': True,
            'render_annotation_content_blocks': True,
            'render_footnote_backlinks': True,
        }

    def add_module(self, module_class: type[ModuleBase]) -> None:
        """Register a module that provides additional block/node handlers."""
        module = module_class(parent=self)
        self._modules.append(module)
        self.settings.update(module.settings)
        for reg in ('block_registry', 'node_registry'):
            module_registry = getattr(module, reg)
            my_registry = getattr(self, reg)
            for kn, vln in module_registry.items():
                if isinstance(kn, str):
                    if not hasattr(module, kn):
                        raise AttributeError(
                            f"{module_class.__name__}.{reg} references "
                            f"missing test method '{kn}'"
                        )
                    ky = getattr(module, kn)
                else:
                    ky = kn
                if isinstance(vln, str):
                    if not hasattr(module, vln):
                        raise AttributeError(
                            f"{module_class.__name__}.{reg} references "
                            f"missing factory method '{vln}'"
                        )
                    vl = getattr(module, vln)
                else:
                    vl = vln
                my_registry[ky] = vl

    def translate_to_html(self, delta_ops: list[DeltaOp]) -> str:
        return self.ops_to_internal_representation(delta_ops).render_tree()

    def translate_to_latex(self, delta_ops: list[DeltaOp]) -> str:
        return self.ops_to_internal_representation(delta_ops).render_tree(mode='latex')

    def ops_to_internal_representation(
        self,
        delta_ops: list[DeltaOp],
        ensure_final_block: bool = True,
        recopy: bool = True,
        debug: bool = False,
    ) -> QDocument:
        """Convert Quill Delta ops into a QDocument tree.

        Args:
            delta_ops: List of Quill Delta operation dicts.
            ensure_final_block: If True, append a trailing newline when the
                ops don't end with one, so the last block is yielded.
            recopy: If True, deep-copy delta_ops to avoid mutating the caller's data.
            debug: If True, print diagnostic information during processing.
        """
        if recopy:
            delta_ops = copy.deepcopy(delta_ops)
        if ensure_final_block and (
                not delta_ops
                or not ('insert' in delta_ops[-1]
                        and isinstance(delta_ops[-1]['insert'], str)
                        and delta_ops[-1]['insert']
                        and delta_ops[-1]['insert'][-1] == '\n')
        ):
            delta_ops.append({'insert': '\n'})

        this_document = QDocument()
        this_document.settings = self.settings
        previous_block: bks.Block | None = None
        for qblock in self.yield_blocks(delta_ops):
            # Match against registered block handlers
            arguments = (qblock, this_document, previous_block)
            matched_tests = tuple(
                test for test in self.block_registry.keys() if test(*arguments)
            )
            if len(matched_tests) == 1:
                if debug:
                    print(f"\n + Matched test: {matched_tests[0]} - {arguments}")
                this_block = self.block_registry[matched_tests[0]](*arguments)
            elif len(matched_tests) > 1:
                raise ValueError(
                    f"More than one block test matched: "
                    f"{[t.__name__ for t in matched_tests]} for {qblock}"
                )
            else:
                if self.DIFF_MODE and ''.join(
                    s['insert'] for s in qblock['contents']
                ) in ('', '\n'):
                    if debug:
                        print("DIFF MODE - Skipping blank block")
                    continue
                if debug:
                    print(f" - No test matched for {arguments}.")
                this_block = self.make_standard_text_block(*arguments)
            previous_block = this_block

            # Process inline nodes within the block
            for this_content in qblock['contents']:
                node_arguments: dict[str, Any] = {
                    'block': this_block,
                    'contents': this_content['insert'],
                    'attributes': this_content.get('attributes', {}).copy(),
                }
                node_matched_tests = tuple(
                    test for test in self.node_registry.keys()
                    if test(**node_arguments)
                )
                if len(node_matched_tests) == 1:
                    previous_node = self.node_registry[node_matched_tests[0]](**node_arguments)
                elif len(node_matched_tests) > 1:
                    raise ValueError(
                        f"More than one node test matched: "
                        f"{[t.__name__ for t in node_matched_tests]} for {this_content}"
                    )
                else:
                    if isinstance(this_content['insert'], str):
                        previous_node = self.make_string_node(**node_arguments)
                    elif this_content['insert'] is None:
                        warnings.warn(f'Skipping node with None insert: {this_content}')
                        continue
                    else:
                        raise ValueError(
                            "I don't know how to add this node. Default string "
                            "handler failed. Node contents is %s" % node_arguments['contents']
                        )
                # Allow custom node creators to reparent (e.g. divider splitting a block)
                this_block = previous_node.parent
        return this_document

    def is_block(self, insert_instruction: str | dict[str, Any]) -> bool:
        """Return True if this non-string insert is a block-level embed."""
        return any(m.is_block_embed(insert_instruction) for m in self._modules)

    @staticmethod
    def _copy_block_attrs(source: DeltaOp, target: dict[str, Any]) -> None:
        """Copy block-level attributes from a source instruction to a target dict."""
        if 'attributes' in source:
            target['attributes'] = source['attributes']

    def yield_blocks(self, delta_ops: list[DeltaOp]) -> Generator[dict[str, Any]]:
        """Yield each block-level chunk from raw Delta ops.

        Splits on newline characters to de-normalize Quill's compact format.
        Each yielded block is a dict with 'contents' (list of node dicts)
        and 'attributes' (block-level attributes from the newline op).
        """
        block_marker = '\n'
        temporary_nodes: list[DeltaOp] = []
        for instruction in delta_ops:
            if 'insert' not in instruction:
                raise ValueError(
                    f"This parser can only deal with documents. "
                    f"Instruction was: {instruction}."
                )
            insert_instruction = instruction['insert']
            if isinstance(insert_instruction, str):
                if 'attributes' not in instruction:
                    instruction['attributes'] = {}
                if block_marker not in insert_instruction:
                    temporary_nodes.append(instruction)
                elif insert_instruction == block_marker:
                    block_attributes = instruction['attributes']
                    temporary_nodes.append(
                        {"insert": "\n", "attributes": block_attributes.copy()}
                    )
                    yield_this: dict[str, Any] = {'contents': temporary_nodes[:]}
                    self._copy_block_attrs(instruction, yield_this)
                    temporary_nodes = []
                    yield yield_this
                else:
                    sub_blocks = insert_instruction.split(block_marker)
                    sub_blocks_len = len(sub_blocks)
                    if sub_blocks[-1] == '':
                        sub_blocks.pop()
                        last_node_completes_block = True
                    else:
                        last_node_completes_block = False
                    for this_c, contents in enumerate(sub_blocks):
                        if last_node_completes_block or this_c < sub_blocks_len - 1:
                            new_node: DeltaOp = {'insert': contents}
                            self._copy_block_attrs(instruction, new_node)
                            temporary_nodes.append(new_node)
                            yield_this = {'contents': temporary_nodes[:]}
                            temporary_nodes = []
                            self._copy_block_attrs(instruction, yield_this)
                            yield yield_this
                        else:
                            new_node = {'insert': contents}
                            self._copy_block_attrs(instruction, new_node)
                            temporary_nodes.append(new_node)
            else:
                if not self.is_block(insert_instruction):
                    temporary_nodes.append(instruction)
                else:
                    # Flush pending inline nodes before yielding a block embed
                    if temporary_nodes:
                        yield {'contents': temporary_nodes[:], 'attributes': {}}
                        temporary_nodes = []
                    yield {'contents': [instruction], 'attributes': {}}

    def make_standard_text_block(
        self,
        qblock: dict[str, Any],
        this_document: QDocument,
        previous_block: bks.Block | None,
    ) -> bks.Block:
        return this_document.add_block(
            bks.TextBlockParagraph(
                parent=this_document,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )

    def make_string_node(
        self,
        block: bks.Block,
        contents: str,
        attributes: dict[str, Any],
    ) -> node.Node:
        if isinstance(block, bks.TextBlockCode):
            return block.add_node(
                node.TextLine(contents=contents, attributes=attributes, strip_newline=False)
            )
        else:
            return block.add_node(
                node.TextLine(contents=contents, attributes=attributes, strip_newline=True)
            )


class TranslatorQuillJS(TranslatorBase):
    """Translator for the QuillJS flavour of Delta formats."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.block_registry.update({
            self.header_test: self.make_header_block,
            self.code_block_test: self.make_code_block,
        })

        self.node_registry.update({
            self.image_node_test: self.make_image_node,
        })

        self.add_module(ListModule)
        self.add_module(AnnotationModule)
        self.add_module(DividerModule)
        self.add_module(TableQuill2Module)
        self.add_module(BetterTableModule)

    # ---- Block test functions ----

    def header_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        return ('header' in qblock['attributes']
                and qblock['attributes']['header'] is not None)

    def code_block_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        return 'code-block' in qblock['attributes']

    # ---- Node test functions ----

    def image_node_test(
        self, block: bks.Block, contents: str | dict[str, Any], attributes: dict[str, Any],
    ) -> bool:
        return isinstance(contents, dict) and 'image' in contents

    # ---- Block creators ----

    def make_header_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        return this_document.add_block(
            bks.TextBlockHeading(
                parent=this_document,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )

    def make_code_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        # Merge consecutive code blocks with the same attributes
        if (isinstance(previous_block, bks.TextBlockCode)
                and previous_block.attributes == qblock['attributes']):
            return previous_block

        return this_document.add_block(
            bks.TextBlockCode(
                parent=this_document,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )

    def make_standard_text_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        return this_document.add_block(
            bks.TextBlockParagraph(
                parent=this_document,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )

    # ---- Node creators ----

    def make_image_node(
        self, block: bks.Block, contents: dict[str, Any], attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(node.Image(contents=contents, attributes=attributes))

    def make_string_node(
        self, block: bks.Block, contents: str, attributes: dict[str, Any],
    ) -> node.Node:
        if isinstance(block, bks.TextBlockCode):
            return block.add_node(
                node.TextLine(contents=contents, attributes=attributes, strip_newline=False)
            )
        else:
            return block.add_node(
                node.TextLine(contents=contents, attributes=attributes, strip_newline=True)
            )
