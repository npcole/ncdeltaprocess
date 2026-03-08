"""Shared pytest fixtures for ncdeltaprocess tests."""

import pytest
import ncdeltaprocess


@pytest.fixture
def translator():
    """Return a fresh TranslatorQuillJS instance."""
    return ncdeltaprocess.TranslatorQuillJS()


@pytest.fixture
def translator_diff():
    """Return a TranslatorQuillJS instance in diff mode."""
    return ncdeltaprocess.TranslatorQuillJS(diff_mode=True)
