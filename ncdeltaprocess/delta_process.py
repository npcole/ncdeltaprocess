from .document import *
from . import block
from . import node

__all__ = ['Translator']

class Translator(object):
    def __init__(self):
        self.block_registry = {
            self.header_test: self.make_header_block,
            self.list_test: self.make_list_block,
            # text blocks will be handled by default
        }
        
        self.node_registry = {
            #self.string_node_test: self.make_string_node, # we will make the string the default
            self.image_node_test: self.make_image_node,
        }
        
        self.settings = {
            'list_text_blocks_are_p': True
        }
        
        
    def header_test(self, qblock, this_document, previous_block):
        if 'header' in qblock['attributes']:
            return True
        else:
            return False
        
    def list_test(self, qblock, this_document, previous_block):
        if 'list' in qblock['attributes']:
            return True
        else:
            return False
    
    def make_header_block(self, qblock, this_document, previous_block):
        this_block = this_document.add_block(
            block.TextBlockHeading(parent=this_document, last_block=previous_block, attributes=qblock['attributes'].copy())
        )
        return this_block
    
    def make_standard_text_block(self, qblock, this_document, previous_block):
        this_block = this_document.add_block(
            block.TextBlockParagraph(parent=this_document, 
            last_block=previous_block, 
            attributes=qblock['attributes'].copy())
            )
        return this_block
    
    def make_list_block(self, qblock, this_document, previous_block):
        container_block = None
        if previous_block and isinstance(previous_block.parent, block.ListBlock) and \
        previous_block.parent.depth == qblock['attributes'].get('indent', 0):
            # perfect, we can use this.
            container_block = previous_block.parent
        ## how about the previous block is a more nested list?
        elif previous_block and isinstance(previous_block.parent, block.ListBlock) and \
        previous_block.parent.depth > qblock['attributes'].get('indent', 0):
            working_block = previous_block.parent
            searching_for_depth = qblock['attributes'].get('indent', 0)
            while True:
                if not working_block or not isinstance(working_block, block.ListBlock):
                    break
                if isinstance(working_block, block.ListBlock) and working_block.depth == searching_for_depth:
                    container_block = working_block
                    break
                working_block = working_block.parent
        ## We are in a list block, but isn't deep enough
        elif previous_block and isinstance(previous_block.parent, block.ListBlock) and \
        previous_block.parent.depth < qblock['attributes'].get('indent', 0):
            container_block = previous_block
        ## we'd better use the base document
        else:
            container_block = this_document
        ## We aren't done yet. We might need to create nested lists
        while qblock['attributes'].get('indent', 0) > container_block.depth:
            fake_attributes = qblock['attributes'].copy()
            try:
                del fake_attributes['indent']
            except KeyError:
                pass
            container_block = container_block.add_block(
                block.ListBlock(parent=container_block, last_block=container_block, attributes=fake_attributes)
                )
        
        # finally, we should have a list block to add our current block to:
        if self.settings['list_text_blocks_are_p']:
            this_block = container_block.add_block(
                block.TextBlockParagraph(parent=this_document, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy())
            )
        else:
            this_block = container_block.add_block(
                block.TextBlockPlain(parent=this_document, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy())
            )
        return this_block
        
    def image_node_test(self, block, contents, attributes):
        if isinstance(contents, dict) and 'image' in attributes:
            return True
        else:
            return False
            
    def make_image_node(self, block, contents, attributes):
        return block.add_node(node.Image(contents=contents, attributes=attributes))
        
    def make_string_node(self, block, contents, attributes):
        block.add_node(node.TextLine(contents=contents, attributes=attributes))
    
    def ops_to_internal_representation(self, delta_ops):
        this_document = QDocument()
        previous_block = None
        for qblock in self.yield_blocks(delta_ops):
            # first do the block
            arguments = (qblock, this_document, previous_block)
            matched_tests = tuple(test for test in self.block_registry.keys() if test(*arguments))
            if len(matched_tests) == 1:
                this_block = self.block_registry[matched_tests[0]](*arguments)
            elif len(matched_tests) > 1:
                raise ValueError("More than one test matched")
            else:
                # assume it is a standard text block
                this_block = self.make_standard_text_block(*arguments)
            previous_block = this_block
            
            # now do the nodes
            for this_content in qblock['contents']:
                node_arguments = {'block': this_block, 'contents': this_content['insert'], 'attributes': this_content['attributes'].copy()}
                node_matched_tests = tuple(test for test in self.node_registry.keys() if test(**node_arguments))
                if len(node_matched_tests) == 1:
                    previous_node = self.node_registry[node_matched_tests[0]](**node_arguments)
                elif len(node_matched_tests) > 1:
                    raise ValueError("More than one test matched.")
                else:
                    if isinstance(this_content['insert'], str):
                        previous_node = self.make_string_node(**node_arguments)
                    else:
                        raise ValueError("I don't know how to add this node. Default string handler failed. Node contents is %s" % node_arguments['contents'])
        return this_document
      
    def is_block(insert_instruction):
        return False # For extension later. Currently assumed that blocks are only marked by \n
 
    
    def yield_blocks(self, delta_ops):
        """Yields each block-level chunk, though without nesting blocks, which will be the responsibility of another function.
        Has the effect of de-normalizing Quilljs's compact representation.
    
        Blocks are yielded as a dictionary, consisting of
        {'contents': [...] # a list of dictionaries containing the nodes for the block.
         'attributes': {}  # a dictionary containing the attributes for the block
        }
        """
        block_marker = '\n' # currently assumed that there is one, and one only type of block marker.
        raw_blocks = []
        temporary_nodes = [] # the block marker comes at the end of the block, so we may not have one yet.
        block_keys = ['attributes']
        for counter, instruction in enumerate(delta_ops):
            if 'insert' not in instruction:
                raise ValueError("This parser can only deal with documents.")
            insert_instruction = instruction['insert']
            if isinstance(insert_instruction, str):
                if not 'attributes' in instruction:
                    instruction['attributes'] = {}
                block_attributes = instruction['attributes']
                #if insert_instruction.endswith(block_marker):
                #    # then we have complete blocks.  
                #    last_node_completes_block = True
                #else:
                #    last_node_completes_block = False
                if block_marker not in insert_instruction:
                    temporary_nodes.append(instruction)
                elif insert_instruction == block_marker:
                    yield_this =  {'contents': temporary_nodes[:],}
                    for k in instruction.keys():
                        if k in block_keys:
                            yield_this[k] = instruction[k]
                        temporary_nodes = []
                    yield yield_this
                else:
                    sub_blocks = insert_instruction.split(block_marker)
                    sub_blocks_len = len(sub_blocks)
                    if sub_blocks[-1] == '':
                        sub_blocks.pop()
                        last_node_completes_block = True
                    else:
                        last_node_completes_block = False
                    for this_c, contents in enumerate(sub_blocks):
                        print("here!")
                        if last_node_completes_block or this_c < sub_blocks_len-1:
                            temporary_nodes.append({'insert': contents})
                            for k in instruction.keys():
                                if k in block_keys:
                                    temporary_nodes[-1][k] = instruction[k]
                            yield_this = {'contents': temporary_nodes[:]}
                            temporary_nodes = []
                            for k in instruction.keys():
                                if k in block_keys:
                                    yield_this[k] = instruction[k]
                            yield yield_this
                        else:
                            # on the last part of an insert statement but not a complete block
                            temporary_nodes.append({'insert': contents})
                            for k in instruction.keys():
                                if k in block_keys:
                                    temporary_nodes[-1][k] = instruction[k]
            else:
                if not self.is_block(insert_instruction):
                    temporary_nodes.append(instruction)
                else:
                    yield(instruction)