# ncdeltaprocess: An Extensible Processor for Quilljs Delta Formats

## About the Quilljs Delta Format
        
The Quilljs project invented a linar (rather than tree-based) format for document exchange, which is documented at the following
websites:

    - https://github.com/quilljs/delta
    - https://quilljs.com/docs/delta/
    
This format can be used to both describe documents and changes to those documents.  This is a JSON-based format, designed to be
both human-readable and easily parsable.  Each delta consists of an ordered array of operations, and when used as a document-format
all of these operations are 'insert' operations.  These insert operations either consist of a string and (optional) related attributes
or else an object describing some non-text-based object that should be treated by the processor as a single, atomic feature of the
document (such as embedding a break, an image, or a video).

The Quilljs delta format consists of block-level elements and elements within a block.  Each block is ended with a newline character,
and any attributes that should be applied to the whole block are, in the delta format, attached to that new-line only.

Blocks are not nested within this format, but the nesting of blocks can be inferred from the attributes attached to a block.  Thus,
in the Quilljs standard format, list-items are marked by a 'list' attribute describing the type of list (numbered or bullet) and
an 'indent' attribute if the list is nested within another list.

Although the Quilljs Delta format is liniar, therefore, it is capable of representing the tree-based internal format that is used
by the Quilljs editor internally, and which is documented here:

     https://github.com/quilljs/parchment
             
## Using the ncquilldeltaprocess Formatter

The basic operation of the formatter is:

    import ncdeltaprocess
    t = ncdeltaprocess.Translator()
    t.ops_to_internal_representation([
        { 'insert': 'Gandalf', 'attributes': { 'bold': True } },
        { 'insert': ' the ' },
        { 'insert': 'Grey', 'attributes': { 'italic': True } },
        { 'insert': '\n' },
    ]).to_html()
    
A single-step `t.translate_to_html` combines these two steps.

## Extending the Processor

The Processor works by:

1. De-normalizing (i.e. de-compressing) the Quilljs Delta block format.
2. Processing each of the Delta `blocks` and their content into an internal representation of Blocks and Nodes (which, unlike the
    Delta format itself, may be nested).
3. Converting that tree of Blocks and Nodes into an HTML format.
    
The Translator object itself maintains a registery of functions that can recognize a particular type of block, and then translate the 
Delta 'block' into the internal block type.  So, for example, the function `header_test` examines a Delta block to see if it is a header, 
while the function `make_header_block` creates the internal representation.  The actual formatting of header blocks is controlled by the 
`ncdeltaprocess.block.TextBlockHeading` class.  

Nodes within each block likewise have formatters that are responsible for converting them to html, and the translator class 
mantains a registry of tests and formatters for nodes that is the equivilent of the one for blocks.

Every internal representation also has a single QDocument object that serves as the root of the tree.  Currently the functionality is
limited, but this also provides an opportunity for extension.

