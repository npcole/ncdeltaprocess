"""Module for quill-better-table support.

Handles the quill-better-table format with column defs (table-col)
and cell lines (table-cell-line) with row/cell IDs.

https://github.com/soccerloway/quill-better-table
"""

from __future__ import annotations

from typing import Any
from .. import block as bks
from ..document import QDocument
from . import ModuleBase


class BetterTableModule(ModuleBase):
    """Module plugin for quill-better-table format."""
    block_registry: dict[str, str] = {
        'better_table_test': 'make_better_table_blocks',
    }

    def better_table_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bool:
        if qblock['attributes']:
            return bool(
                qblock['attributes'].get('table-col', False)
                or qblock['attributes'].get('table-cell-line', False)
            )
        return False

    def make_better_table_blocks(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: bks.Block | None,
    ) -> bks.Block:
        """Handle quill-better-table format (column defs + table-cell-line)."""
        if self.parent.settings['list_better_table_cells_are_p']:
            CELL_BLOCK: type[bks.Block] = bks.TextBlockParagraph
        else:
            CELL_BLOCK = bks.Block

        if 'table-col' in qblock['attributes']:
            # Column descriptor — create table if needed
            if not previous_block or not isinstance(previous_block, bks.TableColumnDescriptor):
                container_table = this_document.add_block(
                    bks.BetterTableBlock(
                        attributes=None,
                        last_block=previous_block,
                    )
                )
                container_column = container_table.add_column(
                    attributes=qblock['attributes']['table-col'].copy()
                )
                return container_column
            elif isinstance(previous_block, bks.TableColumnDescriptor):
                container_column = previous_block.parent.add_column(
                    attributes=qblock['attributes']['table-col'].copy()
                )
                return container_column

        elif 'table-cell-line' in qblock['attributes']:
            orig_previous_block = previous_block

            # Navigate up to find the cell context
            if (previous_block is not None
                    and not isinstance(previous_block, bks.TableColumnDescriptor)
                    and not isinstance(previous_block.parent, bks.TableBetterCellBlock)):
                while (hasattr(previous_block, 'parent')
                       and not isinstance(previous_block.parent, bks.TableBetterCellBlock)
                       and previous_block.parent is not None):
                    previous_block = previous_block.parent

            if (not hasattr(previous_block, 'parent')
                    or (not isinstance(previous_block, bks.TableColumnDescriptor)
                        and not isinstance(previous_block.parent, bks.TableBetterCellBlock))):
                # No table context found — create a new table without column defs
                # (can happen in diff documents where paragraphs precede table cells)
                container_table = this_document.add_block(
                    bks.BetterTableBlock(
                        attributes=None,
                        last_block=orig_previous_block,
                    )
                )
                cell_line: dict[str, Any] = qblock['attributes']['table-cell-line']
                new_row = container_table.add_node(
                    bks.TableRowBlock(
                        row_id=qblock['attributes']['row'],
                        last_block=orig_previous_block,
                    )
                )
                new_cell = new_row.add_cell(
                    row_id=cell_line['row'],
                    cell_id=cell_line['cell'],
                    row_span=cell_line.get('rowspan'),
                    col_span=cell_line.get('colspan', 1),
                    attributes=cell_line.copy(),
                    last_block=new_row,
                )
                return new_cell.add_node(
                    CELL_BLOCK(last_block=new_cell)
                )

            cell_line = qblock['attributes']['table-cell-line']

            if isinstance(previous_block, bks.TableColumnDescriptor):
                # First row and first cell of the table
                new_row = previous_block.parent.add_node(
                    bks.TableRowBlock(
                        row_id=qblock['attributes']['row'],
                        last_block=previous_block,
                    )
                )
                new_cell = new_row.add_cell(
                    row_id=cell_line['row'],
                    cell_id=cell_line['cell'],
                    row_span=cell_line.get('rowspan'),
                    col_span=cell_line.get('colspan', 1),
                    attributes=cell_line.copy(),
                    last_block=new_row,
                )
                return new_cell.add_node(
                    CELL_BLOCK(last_block=new_cell)
                )

            elif isinstance(previous_block.parent, bks.TableBetterCellBlock):
                # Same cell?
                if previous_block.parent.cell_id == cell_line['cell']:
                    return previous_block.parent.add_node(
                        CELL_BLOCK(last_block=previous_block)
                    )

                # Same row?
                containing_row = previous_block.find_ancestor(bks.TableRowBlock)
                if containing_row.row_id == cell_line['row']:
                    new_cell = containing_row.add_cell(
                        row_id=cell_line['row'],
                        cell_id=cell_line['cell'],
                        row_span=cell_line.get('rowspan'),
                        col_span=cell_line.get('colspan', 1),
                        attributes=cell_line.copy(),
                        last_block=previous_block,
                    )
                    return new_cell.add_node(
                        CELL_BLOCK(last_block=new_cell)
                    )

                # New row — navigate up: cell → row → table
                table_block = previous_block.find_ancestor(bks.BetterTableBlock)
                new_row = table_block.add_node(
                    bks.TableRowBlock(
                        row_id=qblock['attributes']['row'],
                        last_block=previous_block,
                    )
                )
                new_cell = new_row.add_cell(
                    row_id=cell_line['row'],
                    cell_id=cell_line['cell'],
                    row_span=cell_line.get('rowspan'),
                    col_span=cell_line.get('colspan', 1),
                    attributes=cell_line.copy(),
                    last_block=new_row,
                )
                return new_cell.add_node(
                    CELL_BLOCK(last_block=new_cell)
                )
