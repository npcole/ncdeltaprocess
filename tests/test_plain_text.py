"""TranslatorBase.translate_to_plain_text — delta ops -> readable plain text.

The plain-text projection of a Quill delta is the concatenation of its string
``insert`` values (the same as Quill's own ``getText()``): block-level
attributes ride on ``"\\n"`` inserts whose newline is already in the string, so
line breaks are preserved without a tree walk, and embeds (images and other
non-string inserts) contribute nothing. Used for previews, truncation and search
indexing — none of which should ever see the raw ``[{"insert": …}]`` JSON.
"""
import unittest

import ncdeltaprocess


class TestPlainText(unittest.TestCase):
    def _plain(self, ops):
        return ncdeltaprocess.TranslatorQuillJS().translate_to_plain_text(ops)

    def test_concatenates_inserts_and_keeps_newlines(self):
        ops = [
            {'insert': 'Randolph proposed '},
            {'insert': 'fifteen', 'attributes': {'bold': True}},
            {'insert': ' resolutions\n'},
            {'insert': 'second line\n'},
        ]
        self.assertEqual(
            self._plain(ops),
            'Randolph proposed fifteen resolutions\nsecond line\n')

    def test_block_attributes_preserve_line_breaks(self):
        # header / list attributes ride on '\n' inserts; the newline is kept.
        ops = [
            {'insert': 'Title'}, {'insert': '\n', 'attributes': {'header': 1}},
            {'insert': 'item'}, {'insert': '\n', 'attributes': {'list': 'bullet'}},
        ]
        self.assertEqual(self._plain(ops), 'Title\nitem\n')

    def test_embeds_contribute_nothing(self):
        ops = [{'insert': 'before '},
               {'insert': {'image': 'data:image/png;base64,AAAA'}},
               {'insert': ' after\n'}]
        self.assertEqual(self._plain(ops), 'before  after\n')

    def test_no_json_or_attribute_keys_leak(self):
        out = self._plain([{'insert': 'x', 'attributes': {'bold': True}},
                           {'insert': '\n'}])
        self.assertNotIn('insert', out)
        self.assertNotIn('attributes', out)

    def test_empty_ops(self):
        self.assertEqual(self._plain([]), '')

    def test_robust_to_malformed_ops(self):
        # Non-dict items and non-string inserts are skipped, not fatal.
        out = self._plain([
            {'insert': 'keep '},
            'a bare string',                 # not a dict
            {'attributes': {'bold': True}},  # no insert key
            {'insert': None},                # non-string insert
            {'insert': 42},                  # non-string insert
            {'insert': 'and this\n'},
        ])
        self.assertEqual(out, 'keep and this\n')

    def test_diff_runs_keep_both_added_and_deleted_text(self):
        # Plain-text extraction is the raw text content; diff markup (carried in
        # attributes) does not drop the deleted run's text.
        ops = [
            {'insert': 'new', 'attributes': {'ncquill_diff': 'insert'}},
            {'insert': 'old', 'attributes': {'ncquill_diff': 'removed'}},
            {'insert': '\n'},
        ]
        self.assertEqual(self._plain(ops), 'newold\n')

    def test_unicode_preserved(self):
        self.assertEqual(self._plain([{'insert': 'café — résumé ✓\n'}]),
                         'café — résumé ✓\n')


if __name__ == '__main__':
    unittest.main()
