import unittest
import ncdeltaprocess

class TestTableAndList(unittest.TestCase):
    def disable_test_table_and_list(self):
        self.maxDiff=None
        """Test a table and nested list"""
        these_things = ncdeltaprocess.TranslatorQuillJS().ops_to_internal_representation([
        {'insert': "1"},
        {'attributes': {'table': "row-bxkq"}, 'insert': "\n"},
        {'insert': "2"},
        {'attributes': {'table': "row-bxkq"}, 'insert': "\n"},
        {'insert': "3"},
        {'attributes': {'table': "row-bxkq"}, 'insert': "\n"},
        {'insert': "b1"},
        {'attributes': {'table': "row-ssvc"}, 'insert': "\n"},
        {'insert': "b2"},
        {'attributes': {'table': "row-ssvc"}, 'insert': "\n"},
        {'insert': "b3"},
        {'attributes': {'table': "row-ssvc"}, 'insert': "\n"},
        {'insert': "\n"},
        {"insert":"This is a test"},
        {"attributes":{"list":"bullet", 'align': "center", "indent": 2},"insert":"\n"},
        {"insert":"and so is this", "attributes": {"bold": True}},
        {"attributes":{"list":"bullet"},"insert":"\n"},
        {"insert":"\n"},
        ])
        
        print(these_things.render_tree())
        
        self.assertEqual(these_things.render_tree(),
"""<table><tr><td>1</td><td>2</td><td>3</td><tr><td>b1</td><td>b2</td><td>b3</td></tr></tr></table><p></p><ol><li><ol><li><ol><li><p style=text-align: center>This is a test</p></li></ol></li></ol></li><li><p><strong>and so is this</strong></p></li></ol><p></p>""")
        
        #print(these_things.render_tree())
        
        #self.assertEqual(these_things.render_html(), these_things.render_tree())
        

    def test_more_complex(self):
        these_things = ncdeltaprocess.TranslatorQuillJS().ops_to_internal_representation([
            {'insert': "This is a test\n\nThis is a numbered list. "},
            {'insert': {'image': "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAB54A…f9St5VyI3+fDqh+f3h4f/Dw+9FHE8saMLAAAAAElFTkSuQmCC"}},
            {'attributes': {'list': "ordered"}, 'insert': "\n"},
            {'insert': "This is a second item."},
            {'attributes': {'list': "ordered"}, 'insert': "\n"},
            {'insert': "This is a sub list"},
            {'attributes': {'indent': 1, 'list': "ordered"}, 'insert': "\n"},
            {'insert': "and so is this."},
            {'attributes': {'indent': 1, 'list': "ordered"}, 'insert': "\n"},
        ])
        
        print(these_things.render_tree())
        
        

if __name__ == '__main__':
    unittest.main()
        
