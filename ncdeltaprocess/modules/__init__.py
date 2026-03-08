"""Module system for ncdeltaprocess.

Modules extend the translator with additional block/node handlers.
All modules should inherit from ModuleBase.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..delta_process import TranslatorBase


class ModuleBase:
    """Base class for translator modules.

    Subclasses must define:
        block_registry: dict mapping test method names to factory method names
        node_registry:  dict mapping test method names to factory method names
        settings:       dict of default settings the module provides

    Method names in registries are resolved via getattr on the module instance
    during add_module().
    """
    block_registry: dict[str, str] = {}
    node_registry: dict[str, str] = {}
    settings: dict[str, Any] = {}

    def __init__(self, parent: TranslatorBase) -> None:
        import weakref
        self.parent: TranslatorBase = weakref.proxy(parent)

    def is_block_embed(self, insert_instruction: Any) -> bool:
        """Return True if this non-string insert is a block-level embed.

        Override in subclasses that handle block-level embeds.
        """
        return False
