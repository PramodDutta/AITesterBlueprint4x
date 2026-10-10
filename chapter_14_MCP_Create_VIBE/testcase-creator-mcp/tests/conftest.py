from __future__ import annotations

import pytest
from fastmcp import Client

from tc_mcp import config
from tc_mcp.repository import Repository
from tc_mcp.server import create_server


@pytest.fixture
def repo(tmp_path, monkeypatch) -> Repository:
    """Real source CSV, throwaway overlay and export folder."""
    monkeypatch.setenv("TC_MCP_EXPORT_DIR", str(tmp_path / "exports"))
    return Repository(data_path=config.data_path(), overlay_path=tmp_path / "overlay.csv")


@pytest.fixture
async def client(repo):
    async with Client(create_server(repo, allow_write=False, inline_exports=False)) as c:
        yield c


@pytest.fixture
async def write_client(repo):
    async with Client(create_server(repo, allow_write=True, inline_exports=False)) as c:
        yield c


async def call(client: Client, name: str, args: dict | None = None):
    result = await client.call_tool(name, args or {})
    return result.data


async def call_error(client: Client, name: str, args: dict | None = None) -> str:
    result = await client.call_tool(name, args or {}, raise_on_error=False)
    assert result.is_error, f"{name} should have failed"
    return result.content[0].text
