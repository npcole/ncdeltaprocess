__all__ = ['RenderMixin', 'RenderOpenCloseMixin']

class RenderMixin(object):
    def render_html(self):
        if hasattr(self, 'open_tag'):
            return self.open_tag() + self.render_contents_html() + self.close_tag()
        else:
            return self.render_contents_html()
    
    def render_contents_html(self):
        these_contents = []
        for c in self.contents:
            these_contents.append(c.render_html())
        return(''.join(these_contents))

class RenderOpenCloseMixin(RenderMixin):
    def open_tag(self):
        return('')
    
    def close_tag(self):
        return('')
    