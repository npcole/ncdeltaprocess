from .document import *
from . import block
from . import node

__all__ = ['yield_blocks', 'ops_to_internal_representation']

def is_block(insert_instruction):
    return False # For extension later. Currently assumed that blocks are only marked by \n

    
def ops_to_internal_representation(delta_ops):
    this_document = QDocument()
    previous_block = None
    for qblock in yield_blocks(delta_ops):
        # First make the block
        if 'header' in qblock['attributes']:
            # it's a header block. We will put it on the base document
            this_block = this_document.add_block(
                block.TextBlockHeading(parent=this_document, last_block=previous_block, attributes=qblock['attributes'].copy())
            )
        elif 'list' in qblock['attributes']:
            print("Making a list")
            # we will eventually create a textblock on a list, but first we have to be sure that 
            # we have a containinng list.
            # ideally there is a current list -- and we can add to that.
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
            if True: #isinstance(qblock['insert'], str):
                this_block = container_block.add_block(
                    block.TextBlockPlain(parent=this_document, 
                    last_block=previous_block, 
                    attributes=qblock['attributes'].copy())
                )
            else:
                raise ValueError("I'm not sure what I'm supposed to be adding here.")
        
        else:
            # a text block of some kind, that is not embedded in some other block
            this_block = this_document.add_block(
                block.TextBlockParagraph(parent=this_document, 
                last_block=previous_block, 
                attributes=qblock['attributes'].copy())
                )
        previous_block = this_block
        
        # now do the conntents
        for this_content in qblock['contents']:
            if isinstance(this_content['insert'], str):
                this_block.add_node(node.TextLine(contents=this_content['insert'], attributes=this_content['attributes'].copy()))
            elif isinstance(this_content['insert'], dict):
                if 'image' in this_content['insert']:
                    this_block.add_node(node.Image(contents=this_content['insert'], attributes=this_content['attributes'].copy()))
    
    return this_document
                

    
    

def yield_blocks(delta_ops):
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
            if not is_block(insert_instruction):
                temporary_nodes.append(instruction)
            else:
                yield(instruction)
                         
            
             
         