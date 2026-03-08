"""Tests for LaTeX rendering."""

import unittest
from ncdeltaprocess import TranslatorQuillJS


class TestLatexParagraph(unittest.TestCase):
    def test_simple_paragraph(self):
        ops = [{'insert': 'Hello world\n'}]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn('Hello world', latex)

    def test_blockquote(self):
        ops = [
            {'insert': 'Quote'},
            {'attributes': {'blockquote': True}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{quotation}', latex)
        self.assertIn(r'\end{quotation}', latex)


class TestLatexHeading(unittest.TestCase):
    def test_section(self):
        ops = [
            {'insert': 'Title'},
            {'attributes': {'header': 1}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\section{', latex)

    def test_subsection(self):
        ops = [
            {'insert': 'Subtitle'},
            {'attributes': {'header': 2}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\subsection{', latex)


class TestLatexInline(unittest.TestCase):
    def test_bold(self):
        ops = [
            {'attributes': {'bold': True}, 'insert': 'Bold'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\textbf{', latex)

    def test_italic(self):
        ops = [
            {'attributes': {'italic': True}, 'insert': 'Italic'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\emph{', latex)

    def test_underline(self):
        ops = [
            {'attributes': {'underline': True}, 'insert': 'Underlined'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\underline{', latex)

    def test_strike(self):
        ops = [
            {'attributes': {'strike': True}, 'insert': 'Struck'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\sout{', latex)

    def test_superscript(self):
        ops = [
            {'attributes': {'script': 'super'}, 'insert': '2'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\textsuperscript{', latex)

    def test_subscript(self):
        ops = [
            {'attributes': {'script': 'sub'}, 'insert': '2'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\textsubscript{', latex)

    def test_inline_code(self):
        ops = [
            {'attributes': {'code': True}, 'insert': 'code'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\texttt{', latex)

    def test_link(self):
        ops = [
            {'attributes': {'link': 'https://example.com'}, 'insert': 'Link'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\href{', latex)

    def test_internal_link(self):
        ops = [
            {'attributes': {'link': '#section1'}, 'insert': 'Link'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\hyperlink{section1}', latex)

    def test_anchor(self):
        ops = [
            {'attributes': {'anchor': 'target1'}, 'insert': 'Anchor'},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\hypertarget{target1}', latex)


class TestLatexCodeBlock(unittest.TestCase):
    def test_verbatim(self):
        ops = [
            {'insert': 'code here'},
            {'attributes': {'code-block': True}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{verbatim}', latex)
        self.assertIn(r'\end{verbatim}', latex)


class TestLatexList(unittest.TestCase):
    def test_bullet_list(self):
        ops = [
            {'insert': 'Item'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{itemize}', latex)
        self.assertIn(r'\item', latex)

    def test_ordered_list(self):
        ops = [
            {'insert': 'Item'}, {'insert': '\n', 'attributes': {'list': 'ordered'}},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\begin{enumerate}', latex)
        self.assertIn(r'\item', latex)


class TestLatexDivider(unittest.TestCase):
    def test_divider(self):
        ops = [
            {'insert': 'Before\n'},
            {'insert': {'divider': True}},
            {'insert': 'After\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\noindent\rule{\textwidth}{0.4pt}', latex)


class TestLatexEscaping(unittest.TestCase):
    def test_special_chars(self):
        ops = [{'insert': 'Price: $100 & 50% off #1\n'}]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\$', latex)
        self.assertIn(r'\&', latex)
        self.assertIn(r'\%', latex)
        self.assertIn(r'\#', latex)


class TestLatexTable(unittest.TestCase):
    def test_better_table_latex(self):
        """Better table should render as tabular environment."""
        from ncdeltaprocess import block
        from ncdeltaprocess.document import QDocument

        doc = QDocument()
        table = block.BetterTableBlock(attributes=None)
        doc.add_block(table)
        col1 = table.add_column(attributes={'width': '50%'})
        col2 = table.add_column(attributes={'width': '50%'})
        row = block.TableRowBlock(row_id='r1')
        table.add_node(row)
        cell1 = row.add_cell(row_id='r1', cell_id='c1')
        cell1.add_node(block.TextBlockPlain())
        cell2 = row.add_cell(row_id='r1', cell_id='c2')
        cell2.add_node(block.TextBlockPlain())

        latex = doc.render_tree(mode='latex')
        self.assertIn(r'\begin{tabular}', latex)
        self.assertIn(r'\end{tabular}', latex)


class TestLatexImage(unittest.TestCase):
    def test_url_image(self):
        ops = [
            {'insert': {'image': 'https://example.com/photo.jpg'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\includegraphics', latex)
        self.assertIn('https://example.com/photo.jpg', latex)

    def test_data_uri_image(self):
        ops = [
            {'insert': {'image': 'data:image/png;base64,iVBOR'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\fbox', latex)
        self.assertIn('embedded image', latex)

    def test_linked_image(self):
        ops = [
            {'insert': {'image': 'https://example.com/photo.jpg'},
             'attributes': {'link': 'https://example.com'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        latex = t.translate_to_latex(ops)
        self.assertIn(r'\href{https://example.com}', latex)
        self.assertIn(r'\includegraphics', latex)


if __name__ == '__main__':
    unittest.main()
