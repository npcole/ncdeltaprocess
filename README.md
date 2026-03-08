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

The translator uses a module/plugin system.  Each module registers test
functions (to recognise block or node types) and factory functions (to build
the internal representation).

```python
from ncdeltaprocess.modules import ModuleBase

class MyModule(ModuleBase):
    block_registry = {
        'my_test': 'my_factory',
    }

    def my_test(self, qblock, this_document, previous_block):
        return 'my-attribute' in qblock['attributes']

    def my_factory(self, qblock, this_document, previous_block):
        # Build and return a Block node
        ...

t = TranslatorQuillJS()
t.add_module(MyModule)
```

Built-in modules: `ListModule`, `AnnotationModule`, `DividerModule`,
`TableQuill2Module`, `BetterTableModule`, `TableBetterModule`.

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
