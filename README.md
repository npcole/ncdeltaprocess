# ncdeltaprocess

An extensible processor for QuillJS Delta formats, converting Delta ops into
HTML and LaTeX output via an intermediate document tree.

## About the QuillJS Delta Format

The QuillJS project uses a linear (rather than tree-based) format for document
exchange:

- https://github.com/quilljs/delta
- https://quilljs.com/docs/delta/

This JSON-based format represents documents as an ordered array of insert
operations.  Each operation is either a string with optional formatting
attributes, or an object describing an embedded element (image, divider, etc.).

Blocks are separated by newline characters.  Block-level attributes (headings,
lists, alignment) are attached to the terminating newline.  Nesting is inferred
from attributes — for example, list indent depth.

## Installation

```bash
pip install ncdeltaprocess

# With LaTeX support:
pip install ncdeltaprocess[latex]
```

## Usage

```python
from ncdeltaprocess import TranslatorQuillJS

t = TranslatorQuillJS()

# One-step conversion
html = t.translate_to_html([
    {"insert": "Gandalf", "attributes": {"bold": True}},
    {"insert": " the "},
    {"insert": "Grey", "attributes": {"italic": True}},
    {"insert": "\n"},
])

# Or get the document tree for inspection
doc = t.ops_to_internal_representation(ops)
html = doc.render_tree()
latex = doc.render_tree(mode='latex')
```

### Embedding inside another document

When a Delta document is rendered inside a larger report (an article
with its own section numbering, say), its h1/h2 headings will clash
with the host structure. Pass `heading_base_level=N` to shift every
heading down by N levels:

```python
# h1 → h4, h2 → h5 (HTML); h1 → \paragraph, h2 → \subparagraph (LaTeX)
html = t.translate_to_html(ops, heading_base_level=3)
latex = t.translate_to_latex(ops, heading_base_level=3)

# Same shape if you're working with the document tree directly:
html = doc.render_tree(mode='html', heading_base_level=3)
```

In HTML the offset is clamped at `h6`. In LaTeX it walks the natural
`\section` → `\subsection` → `\subsubsection` → `\paragraph` →
`\subparagraph` chain, falling back to `\textbf{...}` for anything
deeper.

## Supported Formats

**Block types:** paragraphs, headings (h1-h6), code blocks, blockquotes,
ordered/bullet/checklist lists with arbitrary nesting, dividers.

**Inline formatting:** bold, italic, underline, strikethrough, inline code,
subscript, superscript, links, anchors, font family, font size, text colour,
background colour.

**Tables:** three formats supported via the module system:
- Standard Quill 2.x tables (`table` attribute with row IDs)
- quill-better-table (column defs + `table-cell-line` with row/cell IDs)
- quill-table-better (style-based with headers and in-cell lists)

In LaTeX, tables render as `longtable` environments with
`p{...\linewidth}` columns so they break across pages and wrap long
content. Include `\usepackage{longtable}` in your preamble.

**Annotations and footnotes:** annotation markers render inline content;
footnote markers generate numbered references with end-matter blocks.
Multi-block annotation content keeps its line structure when inlined
into a marker span or LaTeX `\footnote{...}` — consecutive bare-plain
blocks are joined with `<br>` (HTML) or `\\` (LaTeX).

**Soft breaks:** `{'insert': {'softbreak': True}}` embeds render as
`<br>` in HTML and `\\` in LaTeX, giving a visual line break inside a
single block (e.g. a multi-line heading) without starting a new
section.

**Output modes:** HTML (default) and LaTeX.

## Extending the Processor

The translator uses a module/plugin system.  Each module registers *test*
functions (to recognise block or node types) and *factory* functions (to build
the document tree nodes).  When a block or inline element is encountered, every
registered test is called; exactly one must match (zero → default handler,
more than one → error).

### Architecture overview

```
Delta ops  →  yield_blocks()  →  block test/factory  →  Block tree
                                     ↓
                                 node test/factory  →  Node leaves
                                     ↓
                               render_tree()  →  HTML or LaTeX
```

- **Blocks** are container nodes (paragraphs, headings, list items, table
  cells).  They produce open/close tags in the output.
- **Nodes** are leaf nodes inside blocks (text runs, images, dividers).  They
  produce self-contained output fragments.

### Writing a module

Every module inherits from `ModuleBase` and declares two registries mapping
test method names to factory method names:

```python
from ncdeltaprocess.modules import ModuleBase

class MyModule(ModuleBase):
    block_registry = {
        'my_block_test': 'my_block_factory',
    }
    node_registry = {
        'my_node_test': 'my_node_factory',
    }
```

Method names are resolved via `getattr` on the module instance, so they must
be defined as methods on the same class.

Register the module after creating the translator:

```python
from ncdeltaprocess import TranslatorQuillJS

t = TranslatorQuillJS()
t.add_module(MyModule)
```

If the module needs per-instance state (such as a config object or a
set of event ids), pass extra keyword arguments to `add_module` —
they're forwarded to the module's constructor. `add_module` returns
the instantiated module so callers can hold a reference:

```python
class MyModule(ModuleBase):
    def __init__(self, parent, target_class='highlight'):
        super().__init__(parent=parent)
        self.target_class = target_class

t = TranslatorQuillJS()
module = t.add_module(MyModule, target_class='callout')
```

### Block tests and factories

A **block test** receives the parsed block dict, the document being built, and
the previous block (or `None`).  It returns `True` if this module should handle
the block.

```python
def my_block_test(self, qblock, this_document, previous_block):
    return 'my-attribute' in qblock.get('attributes', {})
```

`qblock` has two keys:

- `qblock['attributes']` — block-level attributes from the terminating newline
  (e.g. `{'header': 1}`, `{'list': 'bullet', 'indent': 2}`)
- `qblock['contents']` — list of inline op dicts, each with `'insert'` and
  optionally `'attributes'`

A **block factory** creates a `Block` subclass instance, adds it to the
document, and returns it:

```python
from ncdeltaprocess import block as bks

def my_block_factory(self, qblock, this_document, previous_block):
    return this_document.add_block(
        MyCustomBlock(
            parent=this_document,
            last_block=previous_block,
            attributes=qblock['attributes'].copy(),
        )
    )
```

### Creating a custom Block class

Block classes control how the container renders in each output mode.  Inherit
from `RenderOpenCloseMixin` (provides open/close tag pairs) and `Block`:

```python
from ncdeltaprocess.block import Block
from ncdeltaprocess.render import RenderOpenCloseMixin, OutputObject

class MyCustomBlock(RenderOpenCloseMixin, Block):
    def open_tag(self, output_object: OutputObject) -> str:
        return '<div class="custom">'

    def close_tag(self, output_object: OutputObject) -> str:
        return '</div>'

    # Optional: LaTeX output (defaults to empty strings)
    def open_latex(self, output_object: OutputObject) -> str:
        return r'\begin{custom}'

    def close_latex(self, output_object: OutputObject) -> str:
        return r'\end{custom}'
```

The renderer walks the tree non-recursively: it calls `open_tag` when first
visiting a block, renders all child nodes, then calls `close_tag` on the
second visit.

### Node tests and factories

Node tests and factories use keyword arguments with a different signature to
block handlers:

```python
def my_node_test(self, block, contents, attributes):
    """Return True if this inline element should be handled by this module.

    Args:
        block: The parent Block this node will be added to.
        contents: The 'insert' value — a string for text, or a dict for embeds.
        attributes: The inline attributes dict (bold, italic, link, etc.).
    """
    return isinstance(contents, dict) and 'my-embed' in contents
```

The factory creates a `Node` subclass, adds it to the block, and returns it:

```python
from ncdeltaprocess import node

def my_node_factory(self, block, contents, attributes):
    return block.add_node(
        MyEmbedNode(contents=contents, attributes=attributes)
    )
```

### Creating a custom Node class

Node classes are leaves.  They inherit from `RenderMixin` and `Node`, and
implement `render_contents_html` and `render_contents_latex`:

```python
from ncdeltaprocess.node import Node
from ncdeltaprocess.render import RenderMixin, OutputObject

class MyEmbedNode(RenderMixin, Node):
    def render_contents_html(self, output: OutputObject) -> str:
        value = self.contents['my-embed']
        return f'<span class="my-embed">{value}</span>'

    def render_contents_latex(self, output: OutputObject) -> str:
        value = self.contents['my-embed']
        return rf'\myembed{{{value}}}'
```

### Block-level embeds

By default, non-string inserts (dicts) are treated as inline content within a
block.  If your embed should be its own block (like a divider or page break),
override `is_block_embed` in your module:

```python
class PageBreakModule(ModuleBase):
    block_registry = {'page_break_test': 'make_page_break'}
    node_registry = {'page_break_node_test': 'make_page_break_node'}

    def is_block_embed(self, insert_instruction):
        """Tell the parser this embed terminates the current block."""
        return isinstance(insert_instruction, dict) and 'page-break' in insert_instruction

    def page_break_test(self, qblock, this_document, previous_block):
        return (len(qblock['contents']) == 1
                and isinstance(qblock['contents'][0].get('insert'), dict)
                and 'page-break' in qblock['contents'][0]['insert'])

    def make_page_break(self, qblock, this_document, previous_block):
        return this_document.add_block(
            bks.TextBlockPlain(parent=this_document, last_block=previous_block)
        )

    def page_break_node_test(self, block, contents, attributes):
        return isinstance(contents, dict) and 'page-break' in contents

    def make_page_break_node(self, block, contents, attributes):
        return block.add_node(PageBreakNode(contents=contents, attributes=attributes))
```

### Complete example

Putting it all together — a module that handles a custom "callout" block type
with a `{'callout': 'warning'}` attribute:

```python
from ncdeltaprocess import TranslatorQuillJS, block as bks
from ncdeltaprocess.render import RenderOpenCloseMixin, OutputObject
from ncdeltaprocess.modules import ModuleBase

class CalloutBlock(RenderOpenCloseMixin, bks.Block):
    def open_tag(self, output_object):
        level = self.attributes.get('callout', 'info')
        return f'<div class="callout callout-{level}">'

    def close_tag(self, output_object):
        return '</div>'

class CalloutModule(ModuleBase):
    block_registry = {'callout_test': 'make_callout'}

    def callout_test(self, qblock, this_document, previous_block):
        return 'callout' in qblock.get('attributes', {})

    def make_callout(self, qblock, this_document, previous_block):
        return this_document.add_block(
            CalloutBlock(
                parent=this_document,
                last_block=previous_block,
                attributes=qblock['attributes'].copy(),
            )
        )

t = TranslatorQuillJS()
t.add_module(CalloutModule)

html = t.translate_to_html([
    {'insert': 'Watch out!'},
    {'attributes': {'callout': 'warning'}, 'insert': '\n'},
])
# → '<div class="callout callout-warning">Watch out!</div>'
```

### Text-run post-processors

Some modules don't add new block or node types — they wrap or annotate
*every* text run in the document. Examples: a diff-marker pass that
wraps inserted/deleted runs in coloured spans, a search-highlighter
that wraps matched runs in `<mark>`, an attribution overlay that emits
tooltip-ready spans showing who wrote each fragment.

`ModuleBase` exposes two list attributes for this:

```python
class HighlightModule(ModuleBase):
    html_text_post_processors: list[str] = ['highlight_html']
    latex_text_post_processors: list[str] = ['highlight_latex']

    def __init__(self, parent, term=''):
        super().__init__(parent=parent)
        self.term = term

    def highlight_html(self, node, current_output):
        if self.term and self.term in node.contents:
            return f'<mark>{current_output}</mark>'
        return current_output

    def highlight_latex(self, node, current_output):
        if self.term and self.term in node.contents:
            return r'\hl{' + current_output + r'}'
        return current_output
```

Each post-processor takes `(text_line, current_output)` and returns a
new `current_output` string. They run *after* the renderer's built-in
pipeline (escape, inline styles, links), so the output they receive is
already valid HTML/LaTeX.

Modules' post-processors chain in registration order — multiple
text-modifier modules can co-exist on the same translator, and the
processor added last wraps the output of the one added first. Modules
that need per-node state (cached event ids, accepted-amendment sets,
etc.) can override `configure_text_line(text_line)` — it's called once
for each `TextLine` the translator creates.

### Built-in modules

`ListModule`, `AnnotationModule`, `DividerModule`, `SoftBreakModule`,
`TableQuill2Module`, `BetterTableModule`, `TableBetterModule`.

## LaTeX output

### Required packages

Add these to your document preamble for the full feature set:

```latex
\usepackage{hyperref}            % \href, \hyperlink, \hypertarget
\usepackage[normalem]{ulem}      % \sout (strikethrough)
\usepackage{longtable}           % paginated tables
\usepackage{changes}             % \added, \deleted, \highlight (diff markup)
\usepackage[utf8]{inputenc}      % unicode text
```

`pylatexenc` is the recommended Unicode-to-LaTeX encoder:

```bash
pip install ncdeltaprocess[latex]
```

Without it, the renderer falls back to a minimal escaper that handles
the standard LaTeX special characters but doesn't know about
characters like smart quotes, em-dashes, currency symbols or the
non-breaking space.

### Aligned headings

A heading with an `align` attribute (`center` / `left` / `right`)
renders inside the matching flush environment with an explicit font
size + `\bfseries`, *not* as a sectioning command. Aligned `\section`
fights the alignment env with its own large vertical spacing; using
font-sizing keeps the visual alignment clean:

```python
ops = [
    {'insert': 'CHAPTER ONE'},
    {'insert': '\n', 'attributes': {'header': 1, 'align': 'center'}},
]
# → \begin{center}{\Large\bfseries CHAPTER ONE}\end{center}
```

Unaligned headings still use the regular `\section{...}` chain.

### Diff markup

If a run carries an `ncquill_diff` or `quill_diff` attribute, it gets
wrapped in a `changes`-package command:

| Attribute value | LaTeX command |
| --------------- | ------------- |
| `'new'` / `'insert'`      | `\added{...}` |
| `'removed'` / `'delete'`  | `\deleted{...}` |
| `'edited'`                | `\highlight{...}` |

The wrapping is applied last, so it sits outside any other inline
formatting (`\textbf`, `\href`, etc.). Requires `\usepackage{changes}`
in the preamble.

### Bracket protection

Square brackets in body text are wrapped `{[}` / `{]}` automatically.
This prevents LaTeX from misreading body-text `[...]` as an optional
argument to a preceding `\par`, `\\`, `\item`, `\noindent` etc.

## Security

All user-controlled values are sanitised before inclusion in output:

- **HTML:** text is entity-escaped; URLs are checked against a blocked-scheme
  list (`javascript:`, `vbscript:`, `data:` in link contexts); CSS values are
  validated against a safe-character whitelist; `data:` URIs are permitted in
  `<img src>` where they are safe.
- **LaTeX:** URLs are encoded for safe use in `\href`; labels are sanitised
  for `\hyperlink`/`\hypertarget`; text content is escaped via
  `unicode_to_latex`.

## License

BSD
