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

    def open_latex(self, output_object: OutputObject) -> str:
        header_val = int(self.attributes['header']) + output_object.heading_base_level
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
        return '}\n'


class AnnotationBlockContents(RenderOpenCloseMixin, Block):
    """Container for annotation/footnote content, stored in document data_blocks."""

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

    def open_tag(self, output_object: OutputObject) -> str:
        return '<div class="ql-annotation-content" style="display: none;">'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</div>'

    def render_inner(self, mode: str = 'html') -> str:
        """Render children without the block's own open/close tags."""
        return ''.join(child.render_tree(mode) for child in self.contents)


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
    def open_tag(self, output_object: OutputObject) -> str:
        return '<table>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</table>'


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
        cols = '|'.join('c' for _ in self._columns) if self._columns else 'c'
        return r'\begin{tabular}{|' + cols + r'|} \hline'

    def close_latex(self, output_object: OutputObject) -> str:
        return r'\end{tabular}'


class TableRowBlock(RenderOpenCloseMixin, Block):
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

    def close_latex(self, output_object: OutputObject) -> str:
        return r'\\ \hline'


class TableCellBlock(RenderOpenCloseMixin, Block):
    def open_tag(self, output_object: OutputObject) -> str:
        return '<td>'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</td>'

    def close_latex(self, output_object: OutputObject) -> str:
        return r' & '


class TableBetterCellBlock(RenderOpenCloseMixin, Block):
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


class TableColumnDescriptor(RenderOpenCloseMixin, Block):
    def open_tag(self, output_object: OutputObject) -> str:
        if self.attributes and 'width' in self.attributes:
            w = str(self.attributes['width'])
            if CSS_SAFE_PATTERN.match(w):
                return f'<col style="width: {w}">'
        return '<col>'

    def close_tag(self, output_object: OutputObject) -> str:
        return ''
