"""Inline node classes for the document tree."""

from __future__ import annotations

import html as _html
from typing import Any
from .render import RenderMixin, OutputObject
from .sanitize import sanitize_url, sanitize_latex_url
from .document import QDocument
from .html_line_render import LineRenderHTML
from .latex_line_render import LineRenderLaTeX


__all__ = [
    'Node', 'TextLine', 'Image', 'DividerNode',
    'AnnotationMarkerNode', 'FootnoteMarkerNode',
]


class Node(object):
    is_leaf: bool = True

    def __init__(
        self,
        contents: str | dict[str, Any],
        attributes: dict[str, Any] | None = None,
        parent: Any = None,
        previous_node: Node | None = None,
    ) -> None:
        self.contents = contents
        self.attributes: dict[str, Any] = attributes or {}
        self.parent = parent
        self.previous_node = previous_node

    def find_document(self) -> QDocument:
        if not self.parent:
            raise ValueError("No parent for node")
        this_parent = self.parent
        while True:
            if isinstance(this_parent, QDocument):
                break
            if not this_parent:
                raise ValueError("Cannot find document")
            this_parent = this_parent.parent
        return this_parent


class TextLine(RenderMixin, Node):
    HTML_RENDER_CLASS: type[LineRenderHTML] = LineRenderHTML
    LATEX_RENDER_CLASS: type[LineRenderLaTeX] = LineRenderLaTeX

    def __init__(self, strip_newline: bool = False, *args: Any, **keywords: Any) -> None:
        super(TextLine, self).__init__(*args, **keywords)
        if strip_newline and self.contents.endswith("\n"):
            self.contents = self.contents[:-1]
        self.html_renderer: LineRenderHTML = self.HTML_RENDER_CLASS(self)
        self.latex_renderer: LineRenderLaTeX = self.LATEX_RENDER_CLASS(self)

    def render_contents_html(self, output: OutputObject) -> str:
        result = self.html_renderer.pre_process_line(self.contents)
        result = self.html_renderer.process_line_with_attributes(result)
        return result

    def render_contents_latex(self, output: OutputObject) -> str:
        return self.latex_renderer.process_line_with_attributes(self.contents)


class Image(RenderMixin, Node):
    def render_contents_html(self, output: OutputObject) -> str:
        src = sanitize_url(self.contents['image'], allow_data=True)
        result = '<img src="%s">' % src
        if 'link' in self.attributes:
            link = sanitize_url(self.attributes['link'])
            if link:
                result = '<a href="%s">' % link + result + '</a>'
        return result

    def render_contents_latex(self, output: OutputObject) -> str:
        src = self.contents['image']
        if src.startswith('data:'):
            # Data URIs can't be embedded in LaTeX directly
            result = r'\fbox{\textit{[embedded image]}}'
        else:
            result = r'\includegraphics[max width=\textwidth]{%s}' % sanitize_latex_url(src)
        if 'link' in self.attributes:
            result = r'\href{%s}{%s}' % (sanitize_latex_url(self.attributes['link']), result)
        return result


class DividerNode(RenderMixin, Node):
    """Renders a thematic break / horizontal rule."""

    def render_contents_html(self, output: OutputObject) -> str:
        return '<hr />'

    def render_contents_latex(self, output: OutputObject) -> str:
        return r'\noindent\rule{\textwidth}{0.4pt}'


class AnnotationMarkerNode(RenderMixin, Node):
    """Renders an annotation marker — content shown inline."""

    def _get_annotation_block(self) -> 'Block':
        """Look up the paired annotation content block, or raise."""
        this_id = self.attributes['annotation-marker']['id']
        doc = self.find_document()
        if this_id not in doc.block_index:
            raise KeyError(
                f"Annotation content block not found for marker id '{this_id}'"
            )
        return doc.block_index[this_id]

    def render_contents_html(self, output: OutputObject) -> str:
        an_block = self._get_annotation_block()
        return '<span class="annotation"><span class="annotation-content">' + an_block.render_tree() + '</span></span>'

    def render_contents_latex(self, output: OutputObject) -> str:
        an_block = self._get_annotation_block()
        return r'\marginpar{' + an_block.render_tree(mode='latex') + '}'


class FootnoteMarkerNode(RenderMixin, Node):
    """Renders a footnote marker — numbered reference with end-matter content."""

    def _get_annotation_block(self) -> 'Block':
        """Look up the paired annotation content block, or raise."""
        this_id = self.attributes['annotation-marker']['id']
        doc = self.find_document()
        if this_id not in doc.block_index:
            raise KeyError(
                f"Footnote content block not found for marker id '{this_id}'"
            )
        return doc.block_index[this_id]

    def render_contents_html(self, output: OutputObject) -> str:
        output.fn_count += 1
        this_id = _html.escape(self.attributes['annotation-marker']['id'], quote=True)
        an_block = self._get_annotation_block()
        output.end_matter.append(
            f'<div class="footnote-block"><span id="fn-{this_id}" class="footnote-number">'
            f'[{output.fn_count}]</span> '
            + an_block.render_tree()
            + '</div>'
        )
        return f'<span class="footnote-marker"><a href="#fn-{this_id}">[{output.fn_count}]</a></span>'

    def render_contents_latex(self, output: OutputObject) -> str:
        an_block = self._get_annotation_block()
        return r'\footnote{' + an_block.render_tree(mode='latex') + '}'
