"""Block-level node classes for the document tree."""

from __future__ import annotations

import html as _html
from typing import Any, TYPE_CHECKING
from .render import RenderMixin, RenderOpenCloseMixin, OutputObject
from .document import QDocument
from .sanitize import CSS_SAFE_PATTERN
import weakref

if TYPE_CHECKING:
    from collections.abc import Generator
    from .node import Node

_PARA_DIFF_CSS_CLASSES: dict[str, str] = {
    'changed': 'quill-diff-para-changed',
    'unchanged': 'quill-diff-para-unchanged',
    'ellipsis': 'quill-diff-para-ellipsis',
}


def _get_para_diff_css_class(attributes: dict[str, Any]) -> str:
    """Return a CSS class string for ncquill_para_diff, or empty string."""
    value = attributes.get('ncquill_para_diff')
    if value and value in _PARA_DIFF_CSS_CLASSES:
        return _PARA_DIFF_CSS_CLASSES[value]
    return ''


__all__ = [
    'Block',
    'TextBlockPlain',
    'TextBlockParagraph',
    'TextBlockHeading',
    'TextBlockCode',
    'AnnotationBlockContents',
    'ListBlock',
    'ListItemBlock',
    'TableBlock',
    'TableRowBlock',
    'TableCellBlock',
    'TableBetterCellBlock',
    'TableColumnDescriptor',
    'BetterTableBlock',
    'plan_latex_table_columns',
    'open_latex_table',
    'close_latex_table',
    'cell_latex_separator',
]


def text_paragraph_style_inline(block: Block) -> str | None:
    """Return a CSS inline style string for paragraph-level attributes, or None."""
    styles: list[str] = []
    if 'align' in block.attributes:
        if block.attributes['align'] in ('center', 'left', 'right', 'justify'):
            styles.append(f'text-align: {block.attributes["align"]}')

    if hasattr(block.parent, 'depth') and 'indent' in block.attributes and block.attributes['indent']:
        parent_depth = block.parent.depth
        attr_depth = block.attributes['indent']
        if attr_depth > block.depth:
            this_depth = (attr_depth - parent_depth) * 5
            styles.append(f'text-indent: {this_depth}em')

    if not styles:
        return None
    else:
        return '; '.join(styles)


class Block(object):
    is_leaf: bool = False
    """The contents of Block should be a list of nodes or other blocks."""

    def __init__(
        self,
        parent: Block | QDocument | None = None,
        contents: list[Block | Node] | None = None,
        attributes: dict[str, Any] | None = None,
        last_block: Block | None = None,
    ) -> None:
        if contents:
            for content in contents:
                self.add_node(content)
        else:
            self.contents: list[Block | Node] = []
        self.attributes: dict[str, Any] = attributes or {}
        if parent:
            try:
                self.parent = weakref.proxy(parent)
            except TypeError:
                self.parent = parent
        else:
            self.parent: Block | QDocument | None = None
        self.last_block = last_block

    def add_node(self, this_node: Block | Node) -> Block | Node:
        if this_node in self.contents:
            raise ValueError("I can't contain a node twice!")
        if self.contents:
            this_node.previous_node = self.contents[-1]
        self.contents.append(this_node)
        try:
            this_node.parent = weakref.proxy(self)
        except TypeError:
            this_node.parent = self
        return this_node

    def add_block(self, block: Block) -> Block:
        return self.add_node(block)

    def get_parents(self) -> Generator[Block | QDocument]:
        working_block: Block | QDocument = self
        while hasattr(working_block, 'parent') and working_block.parent:
            working_block = working_block.parent
            yield working_block

    def find_ancestor(self, ancestor_type: type) -> Block | None:
        """Walk up the parent chain to find nearest ancestor of given type."""
        working_block = self.parent
        while working_block is not None:
            if isinstance(working_block, ancestor_type):
                return working_block
            if not hasattr(working_block, 'parent'):
                break
            working_block = working_block.parent
        return None

    @property
    def depth(self) -> int:
        if not self.parent:
            raise ValueError("Block has no parent — cannot compute depth")
        depth = 0
        working_object = self.parent
        while True:
            if isinstance(working_object, QDocument):
                break
            if not working_object.parent:
                raise ValueError("Reached a parentless node before finding QDocument")
            working_object = working_object.parent
            depth += 1
        return depth


class TextBlockPlain(RenderMixin, Block):
    def open_tag(self, output_object: OutputObject) -> str:
        return ''

    def close_tag(self, output_object: OutputObject) -> str:
        return ''

    def close_latex(self, output_object: OutputObject) -> str:
        return '\n\n'


class TextBlockParagraph(RenderOpenCloseMixin, TextBlockPlain):
    def get_paragraph_tag(self) -> str:
        if 'blockquote' in self.attributes and self.attributes['blockquote']:
            return 'blockquote'
        return 'p'

    def open_tag(self, output_object: OutputObject) -> str:
        inline_style = text_paragraph_style_inline(self)
        open_tag = self.get_paragraph_tag()
        css_class = _get_para_diff_css_class(self.attributes)
        parts: list[str] = []
        if css_class:
            parts.append(f'class="{css_class}"')
        if inline_style:
            parts.append(f'style="{inline_style}"')
        if parts:
            return f'<{open_tag} {" ".join(parts)}>'
        return f'<{open_tag}>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</%s>' % self.get_paragraph_tag()

    def get_latex_blocks(self) -> list[str]:
        blocks: list[str] = []
        if 'blockquote' in self.attributes and self.attributes['blockquote']:
            blocks.append('quotation')
        if 'align' in self.attributes:
            match self.attributes['align']:
                case 'center':
                    blocks.append('center')
                case 'right':
                    blocks.append('flushright')
                case 'left':
                    blocks.append('flushleft')
        return blocks

    def open_latex(self, output_object: OutputObject) -> str:
        blocks = self.get_latex_blocks()
        if blocks:
            return ''.join(f'\\begin{{{b}}}' for b in blocks) + '\n'
        return ''

    def close_latex(self, output_object: OutputObject) -> str:
        blocks = self.get_latex_blocks()
        if blocks:
            return ''.join(f'\\end{{{b}}}' for b in blocks) + '\n'
        return '\n\n'


class TextBlockCode(RenderOpenCloseMixin, TextBlockPlain):
    def open_tag(self, output_object: OutputObject) -> str:
        lang = self.attributes.get('code-block', '')
        if isinstance(lang, str) and lang:
            safe_lang = _html.escape(lang, quote=True)
            return f'<pre><code class="language-{safe_lang}">'
        return '<pre><code>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</code></pre>'

    def open_latex(self, output_object: OutputObject) -> str:
        return r'\begin{verbatim}' + '\n'

    def close_latex(self, output_object: OutputObject) -> str:
        return '\n' + r'\end{verbatim}' + '\n'


class TextBlockHeading(RenderOpenCloseMixin, Block):
    def get_header_tag(self, output_object: OutputObject) -> str | None:
        if 'header' not in self.attributes:
            raise ValueError("Heading block has no 'header' attribute")

        if self.attributes['header'] is None:
            return None

        header_val = int(self.attributes['header'])
        if not (1 <= header_val <= 6):
            raise ValueError("Header must be a value between 1 and 6, got %s" % self.attributes['header'])

        adjusted = header_val + output_object.heading_base_level
        return f'h{min(adjusted, 6)}'

    def open_tag(self, output_object: OutputObject) -> str:
        header_tag = self.get_header_tag(output_object)
        if header_tag is None:
            return '<p>'
        inline_style = text_paragraph_style_inline(self)
        css_class = _get_para_diff_css_class(self.attributes)
        parts: list[str] = []
        if css_class:
            parts.append(f'class="{css_class}"')
        if inline_style:
            parts.append(f'style="{inline_style}"')
        if parts:
            return f'<{header_tag} {" ".join(parts)}>'
        return f'<{header_tag}>'

    def close_tag(self, output_object: OutputObject) -> str:
        header_tag = self.get_header_tag(output_object)
        if header_tag is None:
            return '</p>'
        return f'</{header_tag}>'

    # Font-size commands for centred/aligned headings (no \section spacing).
    _ALIGNED_HEADING_SIZES: dict[int, str] = {
        1: r'\Large\bfseries',
        2: r'\large\bfseries',
        3: r'\normalsize\bfseries',
        4: r'\normalsize\bfseries',
        5: r'\small\bfseries',
    }

    def _get_latex_align_envs(self) -> list[str]:
        """Return LaTeX environment names for the heading's align attribute."""
        envs: list[str] = []
        if 'align' in self.attributes:
            match self.attributes['align']:
                case 'center':
                    envs.append('center')
                case 'right':
                    envs.append('flushright')
                case 'left':
                    envs.append('flushleft')
        return envs

    def open_latex(self, output_object: OutputObject) -> str:
        header_val = int(self.attributes['header']) + output_object.heading_base_level
        envs = self._get_latex_align_envs()
        if envs:
            # Aligned headings: use font sizing rather than \section so the
            # large vertical spacing that sectioning commands add doesn't
            # bracket the alignment env.
            size_cmd = self._ALIGNED_HEADING_SIZES.get(header_val, r'\bfseries')
            prefix = ''.join(f'\\begin{{{e}}}' for e in envs) + '\n'
            return prefix + '{' + size_cmd + ' '
        match header_val:
            case 1:
                return r'\section{'
            case 2:
                return r'\subsection{'
            case 3:
                return r'\subsubsection{'
            case 4:
                return r'\paragraph{'
            case 5:
                return r'\subparagraph{'
            case _:
                return r'\textbf{'

    def close_latex(self, output_object: OutputObject) -> str:
        envs = self._get_latex_align_envs()
        suffix = ''.join(f'\\end{{{e}}}' for e in envs) + '\n' if envs else ''
        return '}\n' + suffix


class AnnotationBlockContents(RenderOpenCloseMixin, Block):
    """Container for annotation/footnote content, stored in document data_blocks.

    Rendered as a leaf in both modes: the full opening wrapper, the
    children's inlined contents (via :meth:`render_inner`), and the
    closing wrapper are emitted in a single shot. This keeps the body
    render path (the hidden div assembled in ``QDocument.open_tag``)
    and the inline render path (called from marker nodes) producing the
    same text — multi-block content keeps its line structure in both.
    """

    is_leaf: bool = True

    def __init__(
        self,
        parent: Block | QDocument | None = None,
        contents: list[Block | Node] | None = None,
        attributes: dict[str, Any] | None = None,
        last_block: Block | None = None,
    ) -> None:
        super().__init__(parent=parent, contents=contents, attributes=attributes, last_block=last_block)
        self.annotation_type: str = attributes['annotation-content']['type']
        self.annotation_id: str = attributes['annotation-content']['id']

    def render_contents_html(self, output: OutputObject) -> str:
        return (
            '<div class="ql-annotation-content" style="display: none;">'
            + self.render_inner('html')
            + '</div>'
        )

    def render_contents_latex(self, output: OutputObject) -> str:
        # Annotation content has no top-level LaTeX wrapper — markers
        # pull it inline via ``\footnote{...}`` / ``\marginpar{...}``.
        # Nothing should be emitted at the document level.
        return ''

    # Visual separator between bare-plain children when inlining the
    # annotation content (inside marker spans, footnote/marginpar
    # commands). Block-shaped children (lists, paragraphs, code blocks)
    # already terminate themselves so we don't add a separator before
    # or after them.
    _INNER_SEPARATORS: dict[str, str] = {'html': '<br>', 'latex': '\\\\\n'}

    def render_inner(self, mode: str = 'html') -> str:
        """Render children, inlining them with a visual separator between
        bare-plain blocks so multi-block annotation content keeps its
        line structure when dropped inside a marker span or LaTeX
        ``\\footnote{...}``. Plain children's trailing newlines (the
        ``\\n\\n`` paragraph break emitted by ``TextBlockPlain.close_latex``)
        are stripped so they don't compound with the inline separator.
        """
        sep = self._INNER_SEPARATORS.get(mode, '')
        parts: list[str] = []
        prev_is_plain = False
        for child in self.contents:
            # Only TextBlockPlain (not its subclasses, which carry their
            # own block markers) participates in the inline separator.
            is_plain = type(child) is TextBlockPlain
            rendered = child.render_tree(mode)
            if is_plain:
                rendered = rendered.strip('\n')
            if sep and parts and prev_is_plain and is_plain:
                parts.append(sep)
            parts.append(rendered)
            prev_is_plain = is_plain
        return ''.join(parts)


class ListBlock(RenderOpenCloseMixin, Block):
    _tags_list_type: dict[str, tuple[str, str]] = {
        'bullet': ('<ul>', '</ul>'),
        'ordered': ('<ol>', '</ol>'),
        'checked': ('<ul class="checklist">', '</ul>'),
        'unchecked': ('<ul class="checklist">', '</ul>'),
    }
    _latex_list_type: dict[str, tuple[str, str]] = {
        'bullet': (r'\begin{itemize}', r'\end{itemize}'),
        'ordered': (r'\begin{enumerate}', r'\end{enumerate}'),
        'checked': (r'\begin{itemize}', r'\end{itemize}'),
        'unchecked': (r'\begin{itemize}', r'\end{itemize}'),
    }

    def __init__(self, list_type: str | None = None, *args: Any, **keywords: Any) -> None:
        super(ListBlock, self).__init__(*args, **keywords)
        self.attributes['list'] = list_type or keywords.get('list', 'bullet')

    def open_tag(self, output_object: OutputObject) -> str:
        return self._tags_list_type[self.attributes['list']][0]

    def close_tag(self, output_object: OutputObject) -> str:
        return self._tags_list_type[self.attributes['list']][1]

    def open_latex(self, output_object: OutputObject) -> str:
        return self._latex_list_type[self.attributes['list']][0]

    def close_latex(self, output_object: OutputObject) -> str:
        return self._latex_list_type[self.attributes['list']][1]


class ListItemBlock(RenderOpenCloseMixin, Block):
    _checkbox: dict[str, str] = {
        'checked': '<input type="checkbox" checked disabled /> ',
        'unchecked': '<input type="checkbox" disabled /> ',
    }
    _latex_checkbox: dict[str, str] = {
        'checked': r'$\boxtimes$ ',
        'unchecked': r'$\square$ ',
    }

    def open_tag(self, output_object: OutputObject) -> str:
        list_type = self.attributes.get('list', '')
        checkbox = self._checkbox.get(list_type, '')
        return f'<li>{checkbox}'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</li>'

    def open_latex(self, output_object: OutputObject) -> str:
        list_type = self.attributes.get('list', '')
        checkbox = self._latex_checkbox.get(list_type, '')
        return rf'\item {checkbox}'

    def close_latex(self, output_object: OutputObject) -> str:
        return '\n\n'


class TableBlock(RenderOpenCloseMixin, Block):
    """A table in the legacy Quill 2.x dialect (``modules/table_quill2.py``).

    This class carried ``open_tag``/``close_tag`` and NOTHING for LaTeX,
    while the rows and cells beneath it emitted ``&``, ``\\\\`` and
    ``\\hline`` regardless -- alignment material with no alignment
    around it. ``render_tree`` asks for ``open_latex`` with ``getattr``
    and skips the close when the attribute is absent, so the omission
    was silent, and the result could not compile at all: pdflatex gives
    "Misplaced alignment tab character &" and "Misplaced \\noalign"
    and produces no PDF. Every stored document in this dialect was an
    unprintable report waiting to happen.
    """

    def open_tag(self, output_object: OutputObject) -> str:
        return '<table>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</table>'

    def open_latex(self, output_object: OutputObject) -> str:
        # This dialect has no column descriptors at all, so the rows are
        # the only statement of how wide the table is.
        return open_latex_table(plan_latex_table_columns(self))

    def close_latex(self, output_object: OutputObject) -> str:
        return close_latex_table()


class BetterTableBlock(RenderOpenCloseMixin, Block):
    def __init__(self, *args: Any, **keywords: Any) -> None:
        super().__init__(*args, **keywords)
        self._columns: list[TableColumnDescriptor] = []

    def add_column(
        self,
        parent: Block | None = None,
        contents: list[Block | Node] | None = None,
        attributes: dict[str, Any] | None = None,
        last_block: Block | None = None,
    ) -> TableColumnDescriptor:
        new_block = TableColumnDescriptor(
            parent=parent or self,
            contents=contents,
            attributes=attributes,
            last_block=last_block,
        )
        self.add_node(new_block)
        self._columns.append(weakref.proxy(new_block))
        return new_block

    def open_tag(self, output_object: OutputObject) -> str:
        return '<table>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</table>'

    def open_latex(self, output_object: OutputObject) -> str:
        return open_latex_table(
            plan_latex_table_columns(self, declared_columns=len(self._columns)))

    def close_latex(self, output_object: OutputObject) -> str:
        return close_latex_table()


class TableRowBlock(RenderOpenCloseMixin, Block):
    #: Read by :func:`plan_latex_table_columns`. A marker rather than an
    #: ``isinstance`` check because the table dialects in ``modules/``
    #: import this module, so it cannot import them back.
    is_latex_table_row = True

    def __init__(self, row_id: str, *args: Any, **keywords: Any) -> None:
        super(TableRowBlock, self).__init__(*args, **keywords)
        self.row_id: str = row_id
        self._cells: list[TableBetterCellBlock] = []

    def add_cell(self, *args: Any, **keywords: Any) -> TableBetterCellBlock:
        new_cell = TableBetterCellBlock(*args, **keywords)
        self.add_node(new_cell)
        self._cells.append(weakref.proxy(new_cell))
        return new_cell

    def open_tag(self, output_object: OutputObject) -> str:
        return '<tr>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</tr>'

    def open_latex(self, output_object: OutputObject) -> str:
        # Start a fresh per-row cell counter; cells in this row will
        # consume and increment it. Pushed (not assigned) so nested
        # tables are handled correctly.
        output_object.cell_position_stack.append(0)
        return ''

    def close_latex(self, output_object: OutputObject) -> str:
        output_object.cell_position_stack.pop()
        return r' \\' '\n' r'\hline' '\n'


class TableCellBlock(RenderOpenCloseMixin, Block):
    #: Read by :func:`plan_latex_table_columns` -- see TableRowBlock.
    is_latex_table_cell = True
    #: Filled by :func:`plan_latex_table_columns` before this cell
    #: renders: everything it must emit before its content (separators,
    #: multicolumn, multirow) and the braces that close them. ``None``
    #: means no table planned this cell, and it falls back to the
    #: shared separator.
    latex_cell_open: str | None = None
    latex_cell_close: str = ''
    #: Spans; the legacy Quill 2.x dialect declares neither.
    col_span: int | None = None
    row_span: int | None = None

    def open_tag(self, output_object: OutputObject) -> str:
        return '<td>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</td>'

    def open_latex(self, output_object: OutputObject) -> str:
        if self.latex_cell_open is None:
            return cell_latex_separator(output_object)
        return self.latex_cell_open

    def close_latex(self, output_object: OutputObject) -> str:
        return self.latex_cell_close


class TableBetterCellBlock(RenderOpenCloseMixin, Block):
    #: Read by :func:`plan_latex_table_columns` -- see TableRowBlock.
    is_latex_table_cell = True
    #: Filled by :func:`plan_latex_table_columns` before this cell
    #: renders: everything it must emit before its content (separators,
    #: multicolumn, multirow) and the braces that close them. ``None``
    #: means no table planned this cell, and it falls back to the
    #: shared separator.
    latex_cell_open: str | None = None
    latex_cell_close: str = ''
    #: Spans; the legacy Quill 2.x dialect declares neither.
    col_span: int | None = None
    row_span: int | None = None

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

    def open_latex(self, output_object: OutputObject) -> str:
        if self.latex_cell_open is None:
            return cell_latex_separator(output_object)
        return self.latex_cell_open

    def close_latex(self, output_object: OutputObject) -> str:
        return self.latex_cell_close


#: Share of ``\linewidth`` a table's columns divide between them. The
#: remainder is the margin the surrounding environments expect.
_TABLE_LINEWIDTH_SHARE = 0.9

def close_latex_table() -> str:
    """Close the environment :func:`open_latex_table` opened."""
    return r'\end{longtable}' '\n' r'\medskip' '\n'


def _table_rows_and_cells(table):
    """The table's rows, each as its ordered list of cell blocks.

    Read by marker rather than by ``isinstance`` because the dialects in
    ``modules/`` import this module, so it cannot import them back.
    """
    return [[cell for cell in row.contents
             if getattr(cell, 'is_latex_table_cell', False)]
            for row in table.contents
            if getattr(row, 'is_latex_table_row', False)]


def _occupancy_walk(rows_cells, n_cols=None):
    r"""Walk the table's occupancy grid, yielding each cell's placement.

    The usual grid walk, and the one thing a per-cell renderer cannot do
    for itself: a cell claims ``colspan`` columns starting at the first
    column no earlier row's ``rowspan`` still reserves, and reserves
    those columns for the rows it spans downward. A covered position
    carries NO cell of its own in any of these wire formats, so a row
    that must skip a column has no way to know it from its own contents.

    Yields ``(cell, column, span, rows_below, slots_before)`` per cell,
    then ``(None, width, 0, 0, slots)`` at the end of each row so a
    caller can see how wide the row came out. ``slots_before`` counts
    the ``&``-separated positions already used in the row, blank fillers
    for reserved columns included. ``n_cols`` clamps the spans; ``None``
    measures instead, which is how the width is found before there is a
    width to clamp to.

    Trailing reservations included: a row can END inside a reservation
    and so be wider than any cell of its own shows.
    """
    reserved = {}
    for cells in rows_cells:
        claimed_below = {}
        column = 0
        slots = 0
        for cell in cells:
            while reserved.get(column, 0) > 0:
                column += 1
                slots += 1          # a blank filler holds one slot
            span = max(1, cell.col_span or 1)
            if n_cols is not None:
                # Defensive: the measuring pass already made n_cols wide
                # enough for every span, so this cannot bite for data it
                # measured. \multicolumn wider than the spec is the
                # compile error all of this exists to prevent.
                span = max(1, min(span, n_cols - column))
            rows_below = max(1, cell.row_span or 1) - 1
            yield cell, column, span, rows_below, slots
            if rows_below:
                for occupied in range(column, column + span):
                    claimed_below[occupied] = rows_below
            column += span
            slots += 1
        trailing = max((index + 1 for index, rows in reserved.items()
                        if rows > 0), default=0)
        yield None, max(column, trailing), 0, 0, slots
        reserved = {index: rows - 1
                    for index, rows in reserved.items() if rows > 1}
        reserved.update(claimed_below)


def plan_latex_table_columns(table, declared_columns=0):
    r"""Return the table's LaTeX column count, and prepare its cells.

    A ``longtable`` preamble fixes the row width for the whole table, so
    a row that emits more ``&``-separated slots than the preamble
    declares does not render badly -- pdflatex refuses it outright with
    "Extra alignment tab has been changed to \cr", one error per surplus
    slot and no PDF at all. Column descriptors therefore cannot be the
    whole answer, because stored data need not agree with them.
    Documents exist whose cells outlived their column group entirely --
    concurrent edits can delete a table while another client inserts a
    row into it, and a delete can never remove concurrently-inserted
    content -- and sized from the descriptors alone such a table became
    a ONE-column ``longtable`` full of alignment tabs, which took a
    whole report down with it.

    So the descriptors are a FLOOR and the measured grid is the other
    floor; the table takes whichever is larger and can therefore only
    grow. The grid is MEASURED, not counted, because neither the cells
    nor the sum of their spans is the width: a row under a ``rowspan``
    from above is wider than its own cell list shows, and a row can end
    inside a reservation and be wider than any cell it holds.

    **Cells are prepared here, not in the cell.** Each is given the exact
    string it must emit (``latex_cell_open`` / ``latex_cell_close``): the
    ``&`` separators that carry it to its column -- one per blank slot a
    ``rowspan`` from above has reserved -- and its ``\multicolumn`` /
    ``\multirow`` wrappers. None of that is knowable from inside a cell,
    which can see neither its siblings nor the rows before it. A table's
    ``open_latex`` runs immediately before its rows and cells render,
    which is what makes preparing them here work.

    Any dialect can use this: a row marks itself ``is_latex_table_row``,
    a cell ``is_latex_table_cell`` and carries ``col_span`` /
    ``row_span``. All three table readers (``table_quill2``,
    ``table_better_table``, ``table_better``) had written the same
    ``len(self._columns) or 1`` independently and were wrong in the same
    way.

    A span is HONOURED, never clipped: it is the document's statement of
    its own structure, so a title spanning nine columns above a row that
    fills two is a nine-column table. Clipping it to keep the table
    narrow would render a different table than the one stored.
    """
    rows_cells = _table_rows_and_cells(table)
    measured = max((width for cell, width, _span, _rows, _slots
                    in _occupancy_walk(rows_cells) if cell is None),
                   default=0)
    n_cols = max(declared_columns, measured, 1)
    column_share = _TABLE_LINEWIDTH_SHARE / n_cols

    # Separators already emitted in the current row. A cell emits the ones
    # between it and the PREVIOUS cell -- one per blank slot a rowspan from
    # above reserved, plus the one that ends the previous cell -- not one
    # per slot before it, which would double every separator after the
    # second cell in a row.
    emitted = 0
    for cell, column, span, rows_below, slots_before in _occupancy_walk(
            rows_cells, n_cols):
        if cell is None:
            emitted = 0          # row ended
            continue
        opener = ' & ' * (slots_before - emitted)
        emitted = slots_before
        closer = ''
        if span > 1:
            width = f'{column_share * span:.2f}\\linewidth'
            # A \multicolumn replaces the columns it covers, rules
            # included, so only a cell starting at column 0 restores the
            # table's left rule; anywhere else the preceding column has
            # already drawn it.
            left_rule = '|' if column == 0 else ''
            opener += (r'\multicolumn{' + str(span) + '}{'
                       + left_rule + 'p{' + width + '}|}{')
            closer = '}' + closer
        if rows_below:
            # \multirow INSIDE \multicolumn: the column wrapper has to
            # be the outer one for the width it names to mean anything.
            opener += r'\multirow{' + str(rows_below + 1) + '}{*}{'
            closer = '}' + closer
        cell.latex_cell_open = opener
        cell.latex_cell_close = closer
    return n_cols


def open_latex_table(n_cols: int) -> str:
    """Open a ``longtable`` of ``n_cols`` equal wrapping columns.

    ``longtable`` rather than ``tabular`` so the table may break across
    pages, which a signature block or a long schedule routinely does.
    """
    column_width = f'{_TABLE_LINEWIDTH_SHARE / n_cols:.2f}\\linewidth'
    columns = '|'.join(f'p{{{column_width}}}' for _ in range(n_cols))
    return (
        r'\par\medskip' '\n'
        r'\begin{longtable}{|' + columns + r'|}' '\n'
        r'\hline' '\n'
    )


def cell_latex_separator(output_object: OutputObject) -> str:
    """Return '' for the first cell in the current row, ' & ' for the rest.

    Reads the per-row counter pushed by the enclosing row's ``open_latex``
    and increments it in place. ``O(1)`` per cell — no sibling iteration.
    """
    stack = output_object.cell_position_stack
    if not stack:
        # Defensive: a cell rendered outside any row gets no separator.
        return ''
    pos = stack[-1]
    stack[-1] = pos + 1
    return '' if pos == 0 else ' & '


class TableColumnDescriptor(RenderOpenCloseMixin, Block):
    def open_tag(self, output_object: OutputObject) -> str:
        if self.attributes and 'width' in self.attributes:
            w = str(self.attributes['width'])
            if CSS_SAFE_PATTERN.match(w):
                return f'<col style="width: {w}">'
        return '<col>'

    def close_tag(self, output_object: OutputObject) -> str:
        return ''
