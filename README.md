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

**Annotations and footnotes:** annotation markers render inline content;
footnote markers generate numbered references with end-matter blocks.

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

### Built-in modules

`ListModule`, `AnnotationModule`, `DividerModule`, `TableQuill2Module`,
`BetterTableModule`, `TableBetterModule`.

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
