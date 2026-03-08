"""Tests for table rendering — adapted from quill deltaprocess tests."""

import unittest
import json
from ncdeltaprocess import TranslatorQuillJS


class TestSimpleTable(unittest.TestCase):
    """Tests for standard Quill 2.x table format (row-id based)."""

    def test_basic_table(self):
        ops = [
            {'insert': '1'}, {'attributes': {'table': 'row-1'}, 'insert': '\n'},
            {'insert': '2'}, {'attributes': {'table': 'row-1'}, 'insert': '\n'},
            {'insert': '3'}, {'attributes': {'table': 'row-2'}, 'insert': '\n'},
            {'insert': '4'}, {'attributes': {'table': 'row-2'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<table>', html)
        self.assertIn('</table>', html)
        self.assertIn('<tr>', html)
        self.assertIn('<td>', html)
        self.assertEqual(html.count('<tr>'), 2)
        self.assertEqual(html.count('<td>'), 4)


class TestBetterTable(unittest.TestCase):
    """Tests for quill-better-table format (column defs + table-cell-line)."""

    def test_parse_table_with_text(self):
        """Adapted from quill test_tables.py test_parse_table."""
        test_data = '{"ops":[{"insert":"Root Document.\\n\\n"},{"attributes":{"table-col":{"width":"100"}},"insert":"\\n\\n\\n"},{"insert":"test 1"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-bzd1","cell":"cell-tezr"},"row":"row-bzd1","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"test 2"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-bzd1","cell":"cell-vwzr"},"row":"row-bzd1","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"test 3"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-bzd1","cell":"cell-fdcn"},"row":"row-bzd1","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-xonl","cell":"cell-r2a1"},"row":"row-xonl","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-xonl","cell":"cell-6jeu"},"row":"row-xonl","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-xonl","cell":"cell-c851"},"row":"row-xonl","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-5chd","cell":"cell-mobr"},"row":"row-5chd","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-5chd","cell":"cell-hob7"},"row":"row-5chd","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-5chd","cell":"cell-6pmp"},"row":"row-5chd","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"\\n1.\\n\\n2.\\n"}]}'
        test_json = json.loads(test_data)
        t = TranslatorQuillJS()
        html = t.translate_to_html(test_json['ops'])
        # Should have the root text before the table
        self.assertIn('Root Document.', html)
        # Should have a table with column descriptors
        self.assertIn('<table>', html)
        self.assertIn('<col style="width: 100">', html)
        # Should have 3 rows x 3 cells
        self.assertEqual(html.count('<tr>'), 3, f"Expected 3 rows, got {html.count('<tr>')} in {html}")
        self.assertEqual(html.count('<td>'), 9, f"Expected 9 cells, got {html.count('<td>')} in {html}")
        # Cell content
        self.assertIn('test 1', html)
        self.assertIn('test 2', html)
        self.assertIn('test 3', html)
        # Trailing text
        self.assertIn('1.', html)
        self.assertIn('2.', html)

    def test_parse_table_as_first_block(self):
        """Adapted from quill test_tables.py test_parse_table3 — table as first block."""
        test_data = '{"ops":[{"attributes":{"table-col":{"width":"100"}},"insert":"\\n\\n\\n"},{"insert":"t1"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-m9cp","cell":"cell-u4mk"},"row":"row-m9cp","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"t2"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-m9cp","cell":"cell-7dd6"},"row":"row-m9cp","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"t3"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-m9cp","cell":"cell-wuo5"},"row":"row-m9cp","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-iru2","cell":"cell-cljx"},"row":"row-iru2","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-iru2","cell":"cell-zvdc"},"row":"row-iru2","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-iru2","cell":"cell-27fn"},"row":"row-iru2","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-vwi0","cell":"cell-hqje"},"row":"row-vwi0","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-vwi0","cell":"cell-tjgk"},"row":"row-vwi0","rowspan":"1","colspan":"1"},"insert":"\\n"},{"attributes":{"table-cell-line":{"rowspan":"1","colspan":"1","row":"row-vwi0","cell":"cell-7k70"},"row":"row-vwi0","rowspan":"1","colspan":"1"},"insert":"\\n"},{"insert":"\\n"}]}'
        test_json = json.loads(test_data)
        t = TranslatorQuillJS()
        html = t.translate_to_html(test_json['ops'])
        self.assertIn('<table>', html)
        self.assertEqual(html.count('<col'), 3)
        self.assertEqual(html.count('<tr>'), 3)
        self.assertIn('t1', html)
        self.assertIn('t2', html)
        self.assertIn('t3', html)


class TestTableStructure(unittest.TestCase):
    def test_table_tree_structure(self):
        """Verify the internal tree for a simple 2x2 table."""
        from ncdeltaprocess.block import TableBlock, TableRowBlock, TableCellBlock
        ops = [
            {'insert': 'a'}, {'attributes': {'table': 'r1'}, 'insert': '\n'},
            {'insert': 'b'}, {'attributes': {'table': 'r1'}, 'insert': '\n'},
            {'insert': 'c'}, {'attributes': {'table': 'r2'}, 'insert': '\n'},
            {'insert': 'd'}, {'attributes': {'table': 'r2'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        doc = t.ops_to_internal_representation(ops)
        # Should have one table block
        self.assertEqual(len(doc.contents), 1)
        table = doc.contents[0]
        self.assertIsInstance(table, TableBlock)
        # Two rows
        self.assertEqual(len(table.contents), 2)
        self.assertIsInstance(table.contents[0], TableRowBlock)
        self.assertIsInstance(table.contents[1], TableRowBlock)
        # Two cells per row
        for row in table.contents:
            self.assertEqual(len(row.contents), 2)
            for cell in row.contents:
                self.assertIsInstance(cell, TableCellBlock)


if __name__ == '__main__':
    unittest.main()
