"""Data-driven test runner — adapted from quill deltaprocess tests.

Loads .delta JSON files from test_data/, converts to HTML (and LaTeX),
writes artifacts to test_artifacts/, and compares against known-good
output in test_good_output/.

To regenerate expected output, run with --regenerate flag or delete
the expected file and run the test to create the artifact, then
copy the artifact to test_good_output/.
"""

import unittest
import json
from pathlib import Path
from ncdeltaprocess import TranslatorQuillJS


class TestDataFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = Path(__file__).parent
        cls.input_dir = base_dir / 'test_data'
        cls.artifact_dir = base_dir / 'test_artifacts'
        cls.known_good_dir = base_dir / 'test_good_output'
        cls.artifact_dir.mkdir(exist_ok=True)
        cls.known_good_dir.mkdir(exist_ok=True)

    def _process_file(self, input_file, mode='html'):
        """Process a single delta file and return the output."""
        input_data = input_file.read_text(encoding='utf-8')
        data = json.loads(input_data)
        # Handle both {"ops": [...]} and bare [...] formats
        ops = data['ops'] if isinstance(data, dict) and 'ops' in data else data
        t = TranslatorQuillJS()
        if mode == 'html':
            return t.translate_to_html(ops)
        elif mode == 'latex':
            return t.translate_to_latex(ops)
        else:
            raise ValueError(f'Unknown mode: {mode}')

    def test_html_files(self):
        """Process each .delta file and compare HTML against known-good output."""
        for input_file in sorted(self.input_dir.iterdir()):
            if not input_file.is_file() or not input_file.suffix == '.delta':
                continue
            with self.subTest(file=input_file.name):
                self.maxDiff = None
                html = self._process_file(input_file, mode='html')

                # Write artifact
                artifact_path = (self.artifact_dir / input_file.stem).with_suffix('.html')
                artifact_path.write_text(html, encoding='utf-8')

                # Compare against expected
                expected_path = (self.known_good_dir / input_file.stem).with_suffix('.html')
                if expected_path.exists():
                    expected = expected_path.read_text(encoding='utf-8')
                    self.assertEqual(html, expected, f'Mismatch for {input_file.name}')

    def test_latex_files(self):
        """Process each .delta file and compare LaTeX against known-good output."""
        for input_file in sorted(self.input_dir.iterdir()):
            if not input_file.is_file() or not input_file.suffix == '.delta':
                continue
            with self.subTest(file=input_file.name):
                self.maxDiff = None
                try:
                    latex = self._process_file(input_file, mode='latex')
                except NotImplementedError:
                    # Some features (e.g. images) may not have LaTeX support yet
                    continue

                # Write artifact
                artifact_path = (self.artifact_dir / input_file.stem).with_suffix('.tex')
                artifact_path.write_text(latex, encoding='utf-8')

                # Compare against expected
                expected_path = (self.known_good_dir / input_file.stem).with_suffix('.tex')
                if expected_path.exists():
                    expected = expected_path.read_text(encoding='utf-8')
                    self.assertEqual(latex, expected, f'Mismatch for {input_file.name}')


if __name__ == '__main__':
    unittest.main()
