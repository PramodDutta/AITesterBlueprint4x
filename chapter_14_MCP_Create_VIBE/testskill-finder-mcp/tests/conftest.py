from __future__ import annotations

import shutil

import pytest
from fastmcp import Client

from tsf_mcp import config
from tsf_mcp.catalog import Catalog
from tsf_mcp.server import create_server


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    return Catalog(config.REPO_SKILLS_DIR)


@pytest.fixture
async def client(catalog):
    async with Client(create_server(catalog, allow_write=False)) as c:
        yield c


@pytest.fixture
def skills_copy(tmp_path):
    """A throwaway copy of the skills folder for tests that write."""
    target = tmp_path / "skills"
    shutil.copytree(config.REPO_SKILLS_DIR, target)
    return target


@pytest.fixture
async def write_client(skills_copy):
    async with Client(create_server(Catalog(skills_copy), allow_write=True)) as c:
        yield c


async def call(client: Client, name: str, args: dict | None = None):
    return (await client.call_tool(name, args or {})).data


async def call_error(client: Client, name: str, args: dict | None = None) -> str:
    result = await client.call_tool(name, args or {}, raise_on_error=False)
    assert result.is_error, f"{name} should have failed"
    return result.content[0].text
