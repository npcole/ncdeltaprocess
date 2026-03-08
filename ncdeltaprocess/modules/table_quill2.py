"""Module for standard Quill 2.x table support.

Handles the simple row-id based table format: {'table': 'row-xxxx'}
"""

from __future__ import annotations

from typing import Any
from .. import block as bks
from ..document import QDocument
from . import ModuleBase


class TableQuill2Module(ModuleBase):
    """Module plugin for standard Quill 2.x table format."""
    block_registry: dict[str, str] = {
        'table_cell_test': 'make_table_cell_block',
    }

    def table_cell_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        if qblock['attributes']:
            return qblock['attributes'].get('table', False)
        return False

    def make_table_cell_block(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        """Handle standard Quill 2.x table format (simple row-id based)."""
        container_row: bks.TableRowBlock | None = None
        container_table: bks.TableBlock | None = None

        # Best case: same row as previous block
        ancestor_row = previous_block.find_ancestor(bks.TableRowBlock) if previous_block else None
        if (ancestor_row is not None
                and ancestor_row.row_id == qblock['attributes']['table']):
            container_row = ancestor_row
            container_table = ancestor_row.find_ancestor(bks.TableBlock)
        # Next: still in a table, but need a new row
        elif ancestor_row is not None:
            container_table = ancestor_row.find_ancestor(bks.TableBlock)
            container_row = container_table.add_block(
                bks.TableRowBlock(
                    qblock['attributes']['table'],
                    attributes=qblock['attributes'].copy(),
                )
            )
        else:
            # Need a new table
            table_attributes = qblock['attributes'].copy()
            del table_attributes['table']
            container_table = this_document.add_block(
                bks.TableBlock(attributes=table_attributes)
            )
            container_row = container_table.add_block(
                bks.TableRowBlock(
                    qblock['attributes']['table'],
                    attributes=qblock['attributes'].copy(),
                )
            )

        this_cell = container_row.add_block(
            bks.TableCellBlock(attributes=qblock['attributes'].copy())
        )
        this_block = this_cell.add_block(
            bks.TextBlockPlain(
                parent=container_row,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )
        return this_block
