"""Module for soft line-break support.

Handles softbreak embeds: ``{'insert': {'softbreak': True}}``.

These can be produced upstream (for example, by an editor merging
consecutive heading blocks with identical attributes into a single
block) when a visual line break within a block is wanted without
starting a new block or section. The softbreak renders as ``<br>`` in
HTML and ``\\\\`` in LaTeX.
"""

from __future__ import annotations

from typing import Any

from .. import block as bks
from .. import node
from . import ModuleBase


class SoftBreakModule(ModuleBase):
    """Module plugin for soft line-break embeds."""

    node_registry: dict[str, str] = {
        'softbreak_node_test': 'make_softbreak_node',
    }

    def softbreak_node_test(
        self,
        block: bks.Block,
        contents: str | dict[str, Any],
        attributes: dict[str, Any],
    ) -> bool:
        return isinstance(contents, dict) and 'softbreak' in contents

    def make_softbreak_node(
        self,
        block: bks.Block,
        contents: dict[str, Any],
        attributes: dict[str, Any],
    ) -> node.Node:
        return block.add_node(
            node.SoftBreakNode(contents=contents, attributes=attributes)
        )
