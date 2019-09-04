import unittest
import ncdeltaprocess

class TestTableAndList(unittest.Unittest):
    def test_table_and_list(self):
        """Test a table and nested list"""
        these_things = ncdeltaprocess.Translator().ops_to_internal_representation([
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
        self.assertEqual(these_things.render_html(),
"""<table><tr><td>1</td><td>2</td><td>3</td><tr><td>b1</td><td>b2</td><td>b3</td></tr></tr></table><p></p><ol><li><ol><li><ol><li><p style=text-align: center>This is a test</p></li></ol></li></ol></li><li><p><strong>and so is this</strong></p></li></ol><p></p>""")
        