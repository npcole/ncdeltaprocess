

# A note on sanitization. https://pypi.org/project/html-sanitizer/
# can clean up the whole document at the end, including rearranging tags.

from .render import *

class QDocument(RenderMixin):
    def __init__(self):
        self.contents = []
    
    @property
    def depth(self):
        return -1
    
    def add_block(self, block):
        if self.contents:
            block.previous_block = self.contents[-1]
        block.parent = self
        self.contents.append(block)
        return block
    