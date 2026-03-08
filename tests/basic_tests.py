import unittest
import ncdeltaprocess


class TestTableAndList(unittest.TestCase):
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
        # Verify it produces valid output without errors
        html = these_things.render_tree()
        self.assertIn('<ol>', html)
        self.assertIn('<li>', html)


if __name__ == '__main__':
    unittest.main()
