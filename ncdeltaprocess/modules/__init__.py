"""Module system for ncdeltaprocess.

Modules extend the translator with additional block/node handlers
and/or text-run post-processors. All modules inherit from ModuleBase.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..delta_process import TranslatorBase
    from ..node import Node


class ModuleBase:
    """Base class for translator modules.

    Subclasses may define:
        block_registry: dict mapping test method names to factory method names
        node_registry:  dict mapping test method names to factory method names
        settings:       dict of default settings the module provides
        html_text_post_processors / latex_text_post_processors:
            method names on the module that take ``(node, current_output)``
            and return a new ``current_output`` string. These are appended
            to every ``TextLine``'s rendering pipeline so multiple modules
            can compose their wrapping behaviour.

    Method names in registries are resolved via getattr on the module instance
    during add_module().
    """
    block_registry: dict[str, str] = {}
    node_registry: dict[str, str] = {}
    settings: dict[str, Any] = {}
    html_text_post_processors: list[str] = []
    latex_text_post_processors: list[str] = []

    def __init__(self, parent: TranslatorBase) -> None:
        import weakref
        self.parent: TranslatorBase = weakref.proxy(parent)

    def is_block_embed(self, insert_instruction: str | dict[str, Any]) -> bool:
        """Return True if this non-string insert is a block-level embed.

        Override in subclasses that handle block-level embeds.
        """
        return False

    def configure_text_line(self, text_line: Node) -> None:
        """Optional hook called once for each TextLine the translator creates.

        Override to attach per-node state (e.g. cached event ids) that the
        module's post-processors will need at render time.
        """
        return None
