"""Tests for the module system: ModuleBase, add_module, settings, validation."""

import unittest
from ncdeltaprocess import TranslatorBase, TranslatorQuillJS
from ncdeltaprocess.modules import ModuleBase


class TestModuleBase(unittest.TestCase):
    def test_module_base_has_empty_registries(self):
        t = TranslatorBase()
        m = ModuleBase(parent=t)
        self.assertEqual(m.block_registry, {})
        self.assertEqual(m.node_registry, {})
        self.assertEqual(m.settings, {})

    def test_module_base_stores_parent(self):
        t = TranslatorBase()
        m = ModuleBase(parent=t)
        # weakref.proxy — attribute access should work through the proxy
        self.assertTrue(hasattr(m.parent, 'block_registry'))

    def test_is_block_embed_default_false(self):
        t = TranslatorBase()
        m = ModuleBase(parent=t)
        self.assertFalse(m.is_block_embed({'divider': True}))
        self.assertFalse(m.is_block_embed({'image': 'test.png'}))


class TestAddModule(unittest.TestCase):
    def test_add_module_registers_block_handlers(self):
        class TestModule(ModuleBase):
            block_registry = {
                'my_test': 'my_factory',
            }

            def my_test(self, qblock, this_document, previous_block):
                return False

            def my_factory(self, qblock, this_document, previous_block):
                pass

        t = TranslatorBase()
        t.add_module(TestModule)
        # The test function should be in the registry
        self.assertEqual(len(t.block_registry), 1)

    def test_add_module_registers_node_handlers(self):
        class TestModule(ModuleBase):
            node_registry = {
                'node_test': 'node_factory',
            }

            def node_test(self, block, contents, attributes):
                return False

            def node_factory(self, block, contents, attributes):
                pass

        t = TranslatorBase()
        t.add_module(TestModule)
        self.assertEqual(len(t.node_registry), 1)

    def test_add_module_merges_settings(self):
        class TestModule(ModuleBase):
            settings = {'my_setting': True}

        t = TranslatorBase()
        t.add_module(TestModule)
        self.assertTrue(t.settings['my_setting'])

    def test_add_module_validates_missing_test_method(self):
        class BadModule(ModuleBase):
            block_registry = {
                'nonexistent_test': 'some_factory',
            }

            def some_factory(self, *args):
                pass

        t = TranslatorBase()
        with self.assertRaises(AttributeError) as ctx:
            t.add_module(BadModule)
        self.assertIn('nonexistent_test', str(ctx.exception))

    def test_add_module_validates_missing_factory_method(self):
        class BadModule(ModuleBase):
            block_registry = {
                'my_test': 'nonexistent_factory',
            }

            def my_test(self, *args):
                return False

        t = TranslatorBase()
        with self.assertRaises(AttributeError) as ctx:
            t.add_module(BadModule)
        self.assertIn('nonexistent_factory', str(ctx.exception))

    def test_multiple_modules_coexist(self):
        class ModA(ModuleBase):
            block_registry = {'test_a': 'factory_a'}

            def test_a(self, *args):
                return False

            def factory_a(self, *args):
                pass

        class ModB(ModuleBase):
            block_registry = {'test_b': 'factory_b'}

            def test_b(self, *args):
                return False

            def factory_b(self, *args):
                pass

        t = TranslatorBase()
        t.add_module(ModA)
        t.add_module(ModB)
        self.assertEqual(len(t.block_registry), 2)
        self.assertEqual(len(t._modules), 2)


class TestIsBlockDelegation(unittest.TestCase):
    def test_is_block_delegates_to_modules(self):
        """is_block should check all registered modules."""
        t = TranslatorQuillJS()
        # Divider module should make this True
        self.assertTrue(t.is_block({'divider': True}))
        # Unknown embeds should be False
        self.assertFalse(t.is_block({'unknown': True}))

    def test_is_block_with_no_modules(self):
        t = TranslatorBase()
        self.assertFalse(t.is_block({'divider': True}))


class TestSettings(unittest.TestCase):
    def test_default_settings(self):
        t = TranslatorQuillJS()
        self.assertIn('list_text_blocks_are_p', t.settings)
        self.assertIn('list_better_table_cells_are_p', t.settings)

    def test_settings_override(self):
        """Module settings should override translator defaults."""
        class OverrideModule(ModuleBase):
            settings = {'list_text_blocks_are_p': False}

        t = TranslatorBase()
        t.settings['list_text_blocks_are_p'] = True
        t.add_module(OverrideModule)
        self.assertFalse(t.settings['list_text_blocks_are_p'])


class TestListTextBlockSetting(unittest.TestCase):
    def test_list_with_p_tags(self):
        """Default: list items should contain <p> tags."""
        ops = [
            {'insert': 'Item 1'},
            {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        html = t.translate_to_html(ops)
        self.assertIn('<li><p>', html)

    def test_list_without_p_tags(self):
        """With list_text_blocks_are_p=False, list items should not contain <p>."""
        ops = [
            {'insert': 'Item 1'},
            {'attributes': {'list': 'bullet'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        t.settings['list_text_blocks_are_p'] = False
        html = t.translate_to_html(ops)
        self.assertIn('<li>', html)
        self.assertNotIn('<li><p>', html)

    def test_nested_list_without_p_tags(self):
        """Nested list items should also respect list_text_blocks_are_p=False."""
        ops = [
            {'insert': 'Parent'},
            {'attributes': {'list': 'bullet'}, 'insert': '\n'},
            {'insert': 'Child'},
            {'attributes': {'list': 'bullet', 'indent': 1}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS()
        t.settings['list_text_blocks_are_p'] = False
        html = t.translate_to_html(ops)
        self.assertNotIn('<p>', html)


class TestDiffMode(unittest.TestCase):
    def test_diff_mode_skips_blank_blocks(self):
        ops = [
            {'insert': 'Content\n'},
            {'insert': '\n'},
            {'insert': 'More\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('Content', html)
        self.assertIn('More', html)
        # The blank paragraph should be skipped
        self.assertEqual(html.count('<p>'), 2)

    def test_diff_mode_css_classes_insert(self):
        ops = [
            {'insert': 'New text', 'attributes': {'ncquill_diff': 'insert'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('quill-diff-insert', html)

    def test_diff_mode_css_classes_delete(self):
        ops = [
            {'insert': 'Old text', 'attributes': {'ncquill_diff': 'delete'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('quill-diff-delete', html)

    def test_diff_mode_css_classes_edited(self):
        ops = [
            {'insert': 'Changed text', 'attributes': {'ncquill_diff': 'edited'}},
            {'insert': '\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('quill-diff-edit', html)

    def test_diff_mode_paragraph_classes(self):
        ops = [
            {'insert': 'Changed para'},
            {'attributes': {'ncquill_para_diff': 'changed'}, 'insert': '\n'},
        ]
        t = TranslatorQuillJS(diff_mode=True)
        html = t.translate_to_html(ops)
        self.assertIn('quill-diff-para-changed', html)

    def test_normal_mode_keeps_blanks(self):
        ops = [
            {'insert': 'Content\n'},
            {'insert': '\n'},
            {'insert': 'More\n'},
        ]
        t = TranslatorQuillJS(diff_mode=False)
        html = t.translate_to_html(ops)
        # Normal mode should keep all 3 paragraphs
        self.assertEqual(html.count('<p>'), 3)


if __name__ == '__main__':
    unittest.main()
