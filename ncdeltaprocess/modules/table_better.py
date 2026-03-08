"""Support for the quill-table-better QuillJS extension.

https://github.com/attoae/quill-table-better

Not to be confused with quill-better-table (handled by the core translator).

quill-table-better uses 'style' attributes more heavily and defines
heading and list blocks for use *inside* tables. It does not use
separate hidden column-definition blocks — column info is derived
from the first row's cells.
"""

from __future__ import annotations

import weakref
from typing import Any
from ..block import RenderOpenCloseMixin, Block, TextBlockParagraph
from ..document import QDocument
from ..render import OutputObject
from . import ModuleBase
from typing import NamedTuple


class CellInfo(NamedTuple):
    cell_id: str
    row_id: str
    col_span: int | None
    row_span: int | None


class ColumnInfo(NamedTuple):
    width: str | None = None


class TableBetterModule(ModuleBase):
    """Module plugin for quill-table-better format support."""
    block_registry: dict[str, str] = {
        'new_table_test': 'create_better_table',
        'table_better_cell_test': 'create_better_table_cell',
    }
    settings: dict[str, Any] = {
        'list_text_blocks_are_p': True,
        'list_better_table_cells_are_p': True,
    }

    def new_table_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: Block | None,
    ) -> bool:
        return 'table-temporary' in qblock['attributes']

    def table_better_cell_test(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: Block | None,
    ) -> bool:
        return 'table-cell' in qblock['attributes']

    def create_better_table(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: Block | None,
    ) -> Block:
        return this_document.add_block(
            TableBetter2Block(
                parent=this_document,
                attributes=qblock['attributes'],
                last_block=previous_block,
            )
        )

    def _get_cell_details(self, qblock: dict[str, Any]) -> CellInfo:
        """Extract cell metadata from block attributes."""
        attributes = qblock['attributes']
        if 'table-header' in attributes:
            cell_id = attributes['table-header']['cellId']
            row_id = attributes['table-cell']['data-row']
            col_span = attributes['table-header'].get('colspan', None)
            row_span = attributes['table-header'].get('rowspan', None)
        elif 'table-list' in attributes:
            cell_id = attributes['table-list-container']['cellId']
            row_id = attributes['table-cell']['data-row']
            col_span = attributes['table-list-container'].get('colspan', None)
            row_span = attributes['table-list-container'].get('rowspan', None)
        else:
            cell_id = attributes['table-cell-block']
            row_id = attributes['table-cell']['data-row']
            col_span = attributes['table-cell'].get('colspan', None)
            row_span = attributes['table-cell'].get('rowspan', None)

        return CellInfo(
            cell_id=cell_id,
            row_id=row_id,
            col_span=col_span,
            row_span=row_span,
        )

    def _get_cell_block(
        self,
        cell_info: CellInfo,
        this_document: QDocument,
        previous_block: Block,
    ) -> TableBetter2CellBlock:
        """Get or create the cell block for the given cell info."""
        if isinstance(previous_block, TableBetter2Block):
            new_row = previous_block.add_row(cell_info.row_id)
            previous_cell = new_row.add_cell(cell_info.cell_id)
        elif isinstance(previous_block, TableBetter2CellBlock):
            previous_cell = previous_block
        else:
            test_block: Block = previous_block
            previous_cell: TableBetter2CellBlock | None = None
            while test_block is not this_document:
                if isinstance(test_block.parent, TableBetter2CellBlock):
                    previous_cell = test_block.parent
                    break
                test_block = test_block.parent
            if previous_cell is None:
                raise ValueError(
                    f"Can't find previous cell! {cell_info=} {previous_block=}"
                )

        # Same cell?
        if (cell_info.cell_id == previous_cell.cell_id
                and cell_info.row_id == previous_cell.row_id):
            return previous_cell
        # Same row?
        if cell_info.row_id == previous_cell.row_id:
            return previous_cell.parent.add_cell(cell_info.cell_id)
        # New row
        this_row = previous_cell.find_ancestor(TableBetter2Block).add_row(cell_info.row_id)
        return this_row.add_cell(
            cell_info.cell_id,
            col_span=cell_info.col_span,
            row_span=cell_info.row_span,
        )

    def create_better_table_cell(
        self, qblock: dict[str, Any], this_document: QDocument, previous_block: Block | None,
    ) -> Block:
        """Create a cell content block within a quill-table-better table."""
        attributes = qblock['attributes']
        cell_info = self._get_cell_details(qblock)
        this_cell = self._get_cell_block(cell_info, this_document, previous_block)

        if 'table-header' in attributes:
            new_block: Block = TableBetter2CellHeadingBlock(
                parent=this_cell,
                attributes=attributes.copy(),
                last_block=this_cell,
            )
            this_cell.contents.append(new_block)

        elif 'table-list' in attributes:
            list_style = attributes['table-list']
            if isinstance(previous_block.parent, TableBetter2CellListItemBlock):
                new_block = TableBetter2CellListItemBlock(
                    parent=previous_block.parent.parent,
                    attributes=attributes.copy(),
                    last_block=previous_block,
                )
                previous_block.parent.parent.add_block(new_block)
            elif isinstance(previous_block, TableBetter2CellListContainerBlock):
                new_block = previous_block.add_item_block(
                    parent=previous_block,
                    attributes=attributes.copy(),
                    last_block=previous_block,
                )
                previous_block.contents.append(new_block)
            else:
                this_list_block = TableBetter2CellListContainerBlock(
                    parent=this_cell,
                    attributes=attributes.copy(),
                    last_block=previous_block,
                    list_type=list_style,
                )
                this_cell.contents.append(this_list_block)
                new_block = this_list_block.add_item_block(
                    attributes=attributes.copy(),
                    last_block=this_list_block,
                )

            if self.settings['list_text_blocks_are_p']:
                CELL_BLOCK: type[Block] = TextBlockParagraph
            else:
                CELL_BLOCK = Block
            last = this_cell.contents[-1] if this_cell.contents else this_cell
            contents_block = CELL_BLOCK(
                parent=new_block,
                last_block=last,
            )
            new_block.contents.append(contents_block)
            new_block = contents_block

        else:
            new_block = TextBlockParagraph(
                parent=this_cell,
                last_block=previous_block,
            )
            this_cell.contents.append(new_block)

        return new_block


class TableBetter2Block(RenderOpenCloseMixin, Block):
    """Table container for quill-table-better format."""
    def __init__(self, *args: Any, **keywords: Any) -> None:
        super().__init__(*args, **keywords)
        self._rows_by_id: dict[str, TableBetter2RowBlock] = {}

    def add_row(
        self,
        row_id: str,
        parent: Block | None = None,
        contents: list[Block] | None = None,
        attributes: dict[str, Any] | None = None,
        last_block: Block | None = None,
    ) -> TableBetter2RowBlock:
        new_block = TableBetter2RowBlock(
            row_id=row_id,
            parent=parent or self,
            contents=contents,
            attributes=attributes,
            last_block=last_block,
        )
        self.add_node(new_block)
        self._rows_by_id[row_id] = weakref.proxy(new_block)
        return new_block

    def get_columns(self) -> list[ColumnInfo]:
        if not self._rows_by_id:
            return []
        columns: list[ColumnInfo] = []
        first_row = next(iter(self._rows_by_id.values()))
        for c in first_row._cells_by_id.values():
            for _ in range(c.col_span or 1):
                columns.append(ColumnInfo(width=None))
        return columns

    @property
    def _columns(self) -> list[ColumnInfo]:
        return self.get_columns()

    def open_tag(self, output_object: OutputObject) -> str:
        return '<table>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</table>'

    def open_latex(self, output_object: OutputObject) -> str:
        cols = '|'.join('c' for _ in self._columns)
        if cols:
            cols = '|' + cols + '|'
        return r'\begin{tabular}{' + cols + r'} \hline'

    def close_latex(self, output_object: OutputObject) -> str:
        return r'\end{tabular}'


class TableBetter2RowBlock(RenderOpenCloseMixin, Block):
    """Row block for quill-table-better format."""
    def __init__(self, row_id: str, *args: Any, **keywords: Any) -> None:
        super().__init__(*args, **keywords)
        self.row_id: str = row_id
        self._cells_by_id: dict[str, TableBetter2CellBlock] = {}

    def add_cell(self, cell_id: str, parent: Block | None = None, *args: Any, **keywords: Any) -> TableBetter2CellBlock:
        new_cell = TableBetter2CellBlock(
            cell_id=cell_id, row_id=self.row_id, parent=self, *args, **keywords
        )
        self.add_node(new_cell)
        self._cells_by_id[cell_id] = weakref.proxy(new_cell)
        return new_cell

    def get_tag(self) -> str:
        if self.attributes and self.attributes.get('header', False):
            return 'th'
        return 'tr'

    def open_tag(self, output_object: OutputObject) -> str:
        return '<%s>' % self.get_tag()

    def close_tag(self, output_object: OutputObject) -> str:
        return '</%s>' % self.get_tag()

    def close_latex(self, output_object: OutputObject) -> str:
        return r'\\ \hline'


class TableBetter2CellBlock(RenderOpenCloseMixin, Block):
    """Cell block for quill-table-better format."""
    def __init__(
        self,
        row_id: str,
        cell_id: str,
        row_span: int | str | None = None,
        col_span: int | str | None = None,
        *args: Any,
        **keywords: Any,
    ) -> None:
        super().__init__(*args, **keywords)
        self.row_id: str = row_id
        self.cell_id: str = cell_id
        self.row_span: int | None = int(row_span) if row_span is not None else None
        self.col_span: int | None = int(col_span) if col_span is not None else None

    def open_tag(self, output_object: OutputObject) -> str:
        row_span = f' rowspan="{self.row_span}"' if (self.row_span and self.row_span != 1) else ''
        col_span = f' colspan="{self.col_span}"' if (self.col_span and self.col_span != 1) else ''
        return f'<td{row_span}{col_span}>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</td>'


class TableBetter2CellHeadingBlock(RenderOpenCloseMixin, Block):
    """Heading block inside a table cell."""
    pass


class TableBetter2CellListContainerBlock(RenderOpenCloseMixin, Block):
    """List container inside a table cell."""
    _tags_list_type: dict[str, tuple[str, str]] = {
        'bullet': ('<ul>', '</ul>'),
        'ordered': ('<ol>', '</ol>'),
    }
    _latex_list_type: dict[str, tuple[str, str]] = {
        'bullet': (r'\begin{itemize}', r'\end{itemize}'),
        'ordered': (r'\begin{enumerate}', r'\end{enumerate}'),
    }

    def __init__(self, list_type: str | None = None, *args: Any, **keywords: Any) -> None:
        super().__init__(*args, **keywords)
        self.attributes['list'] = list_type or keywords.get('list', 'bullet')

    def add_item_block(
        self,
        parent: Block | None = None,
        contents: list[Block] | None = None,
        attributes: dict[str, Any] | None = None,
        last_block: Block | None = None,
    ) -> TableBetter2CellListItemBlock:
        new_block = TableBetter2CellListItemBlock(
            parent=parent or self,
            contents=contents,
            attributes=attributes,
            last_block=last_block,
        )
        self.contents.append(new_block)
        return new_block

    def open_tag(self, output_object: OutputObject) -> str:
        return self._tags_list_type[self.attributes['list']][0]

    def close_tag(self, output_object: OutputObject) -> str:
        return self._tags_list_type[self.attributes['list']][1]

    def open_latex(self, output_object: OutputObject) -> str:
        return self._latex_list_type[self.attributes['list']][0]

    def close_latex(self, output_object: OutputObject) -> str:
        return self._latex_list_type[self.attributes['list']][1]


class TableBetter2CellListItemBlock(RenderOpenCloseMixin, Block):
    """List item inside a table cell."""
    def open_tag(self, output_object: OutputObject) -> str:
        return '<li>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</li>'

    def open_latex(self, output_object: OutputObject) -> str:
        return r'\item '

    def close_latex(self, output_object: OutputObject) -> str:
        return '\n\n'
