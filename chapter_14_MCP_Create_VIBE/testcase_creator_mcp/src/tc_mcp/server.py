"""TestCreator MCP server: wires the repository, tools, resources and prompts into FastMCP."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from fastmcp import FastMCP

from tc_mcp import config, prompts, resources
from tc_mcp.repository import Repository
from tc_mcp.tools import authoring, discovery, export, planning, quality, search


def build_instructions(r: Repository, writes_enabled: bool) -> str:
    live = len(r.live_rows())
    mode = "Writes are ON: add_test_cases and update_test_case are available (always dry_run first)." if writes_enabled else "This server is read-only."
    return (
        f"TestCreator MCP serves the VWO test case catalog: {len(r.rows)} tests ({live} live) across "
        f"{len(r.modules)} modules and {sum(len(f) for f in r.features_by_module.values())} features.\n"
        "- Unsure of a module, feature or value? Call list_modules or get_filter_options.\n"
        "- Exact filters (module, priority, min/max priority, type, browser, device, status): search_test_cases.\n"
        "- Free text: search_by_keyword. Full detail for known keys: get_test_case.\n"
        "- 'What should I run first?': get_top_tests_for_module. Smoke/sanity/regression runs: build_test_suite.\n"
        "- Counts and breakdowns: get_test_stats. Coverage holes: find_coverage_gaps. Cleanup: find_duplicate_tests.\n"
        "- Writing tests: get_test_case_template -> validate_test_case -> add_test_cases.\n"
        "Deprecated tests are hidden unless asked for. Module names are case-insensitive and aliases like 'ab', 'sdk', 'billing' work.\n"
        + mode
    )


def create_server(
    repository: Repository | None = None,
    *,
    allow_write: bool | None = None,
    inline_exports: bool | None = None,
    auth: Any = None,
) -> FastMCP:
    repo_instance = repository or Repository()
    for warning in repo_instance.load_warnings[:20]:
        print(f"[tc-mcp] {warning}", file=sys.stderr)
    writes_enabled = config.allow_write() if allow_write is None else allow_write
    inline_only = (config.transport() != "stdio") if inline_exports is None else inline_exports

    def repo() -> Repository:
        repo_instance.ensure_fresh()
        return repo_instance

    mcp = FastMCP(
        name="TestCreator MCP",
        instructions=build_instructions(repo_instance, writes_enabled),
        version="0.1.0",
        mask_error_details=False,
        auth=auth,
    )
    discovery.register(mcp, repo)
    search.register(mcp, repo)
    planning.register(mcp, repo)
    quality.register(mcp, repo)
    authoring.register(mcp, repo, writes_enabled)
    export.register(mcp, repo, inline_only)
    resources.register(mcp, repo)
    prompts.register(mcp, writes_enabled)
    if not writes_enabled:
        mcp.disable(tags={"write"})
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="tc-mcp", description="TestCreator MCP server")
    parser.add_argument("--transport", choices=["stdio", "http"], default=config.transport(), help="stdio (default) or http (streamable HTTP at /mcp)")
    parser.add_argument("--host", default=config.host())
    parser.add_argument("--port", type=int, default=config.port())
    parser.add_argument("--allow-write", action="store_true", default=config.allow_write(), help="Enable add_test_cases and update_test_case")
    args = parser.parse_args()

    if args.transport == "stdio":
        create_server(allow_write=args.allow_write, inline_exports=False).run(transport="stdio", show_banner=False)
        return

    auth = None
    token = config.auth_token()
    if token:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        auth = StaticTokenVerifier(tokens={token: {"client_id": "tc-mcp-team", "scopes": []}})
    elif args.host not in ("127.0.0.1", "localhost"):
        print("[tc-mcp] WARNING: serving on a non-local host without TC_MCP_AUTH_TOKEN; anyone who can reach it can use it.", file=sys.stderr)
    from starlette.middleware import Middleware

    from tc_mcp.landing import BrowserLandingPage

    mcp = create_server(allow_write=args.allow_write, inline_exports=True, auth=auth)
    # Stateless: the tools keep no per-session state, so clients behind proxies or tunnels
    # never hit "Missing session ID". The middleware answers browsers with a help page.
    mcp.run(
        transport="http",
        host=args.host,
        port=args.port,
        show_banner=True,
        stateless_http=True,
        middleware=[Middleware(BrowserLandingPage)],
    )


if __name__ == "__main__":
    main()
