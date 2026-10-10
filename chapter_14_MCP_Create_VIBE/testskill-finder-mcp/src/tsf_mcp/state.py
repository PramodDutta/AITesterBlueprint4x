"""Shared server state: the catalog plus a search index rebuilt whenever the folder changes."""

from __future__ import annotations

import difflib
from collections.abc import Callable

from fastmcp.exceptions import ToolError

from tsf_mcp.catalog import Catalog, Skill
from tsf_mcp.search import SearchIndex


class State:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self._index: SearchIndex | None = None
        self._index_signature: tuple | None = None
        self.on_reload: list[Callable[[], None]] = []

    def fresh(self) -> State:
        before = self.catalog._signature
        self.catalog.ensure_fresh()
        if self.catalog._signature != before:
            for callback in self.on_reload:
                callback()
        return self

    @property
    def index(self) -> SearchIndex:
        if self._index is None or self._index_signature != self.catalog._signature:
            self._index = SearchIndex(self.catalog)
            self._index_signature = self.catalog._signature
        return self._index

    def resolve(self, name: str) -> Skill:
        """Find a skill by exact name, title, or a close spelling; raise a helpful ToolError otherwise."""
        key = name.strip().lower().replace(" ", "-").replace("_", "-")
        skill = self.catalog.get(key)
        if skill:
            return skill
        by_title = {s.title.lower(): s for s in self.catalog.skills.values()}
        if name.strip().lower() in by_title:
            return by_title[name.strip().lower()]
        names = list(self.catalog.skills)
        partial = [n for n in names if key in n]
        if len(partial) == 1:
            return self.catalog.skills[partial[0]]
        close = difflib.get_close_matches(key, names, n=3, cutoff=0.6) or partial[:3]
        hint = f" Did you mean {', '.join(repr(c) for c in close)}?" if close else ""
        raise ToolError(f"No skill named {name!r}.{hint} Use search_skills to find skills by keyword.")


StateProvider = Callable[[], State]
