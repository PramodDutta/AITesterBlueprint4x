"""TestSkill Finder MCP: server wiring and the `tsf-mcp` command line.

    tsf-mcp                         serve over stdio (default)
    tsf-mcp --transport http        serve streamable HTTP at http://127.0.0.1:8110/mcp
    tsf-mcp sync [--ref main]       download the upstream skills into the skills folder
    tsf-mcp validate                check every SKILL.md against the catalog format
    tsf-mcp catalog                 regenerate skills/CATALOG.md
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from fastmcp import FastMCP

from tsf_mcp import config, prompts, resources
from tsf_mcp.catalog import Catalog
from tsf_mcp.state import State
from tsf_mcp.tools import authoring, finder, workflow


def build_instructions(catalog: Catalog, writes_enabled: bool) -> str:
    groups = catalog.categories()
    packs = ", ".join(label for label, items in groups.items() if items and items[0].kind == "pack")
    return (
        f"TestSkill Finder serves {len(catalog.skills)} QA agent skills: the 7 STLC phases plus packs for {packs}.\n"
        "- Need a skill for a task? find_skill_for_task (plain English) or search_skills (keywords).\n"
        "- Browse: list_categories, list_skills, get_stlc_pipeline. Read one: get_skill, get_skill_file.\n"
        "- Bigger goals: suggest_skill_chain. Pick between similar skills: compare_skills, get_related_skills.\n"
        "- Use a skill: the prompt with the skill's name, the use_skill prompt, or export_skill for Claude Code, Copilot or Cursor.\n"
        + ("Writes are ON: create_skill and sync_skills_from_github are available (dry_run first)." if writes_enabled else "This server is read-only.")
    )


def create_server(catalog: Catalog | None = None, *, allow_write: bool | None = None, auth: Any = None) -> FastMCP:
    catalog = catalog or Catalog()
    for problem in catalog.load_problems[:20]:
        print(f"[tsf-mcp] {problem}", file=sys.stderr)
    writes_enabled = config.allow_write() if allow_write is None else allow_write
    shared = State(catalog)

    def state() -> State:
        return shared.fresh()

    mcp = FastMCP(
        name="TestSkill Finder MCP",
        instructions=build_instructions(catalog, writes_enabled),
        version="0.1.0",
        mask_error_details=False,
        auth=auth,
    )
    finder.register(mcp, state)
    workflow.register(mcp, state)
    resources.register(mcp, state)
    refresh_prompts = prompts.register(mcp, state)
    shared.on_reload.append(refresh_prompts)
    authoring.register(mcp, state, refresh_prompts)
    if not writes_enabled:
        mcp.disable(tags={"write"})
    return mcp


def _cmd_sync(args: argparse.Namespace) -> None:
    from tsf_mcp.sync import sync_from_github

    report = sync_from_github(config.skills_dir(), ref=args.ref, dry_run=args.dry_run).as_dict()
    print(json.dumps({k: report[k] for k in ("repo", "ref", "commit", "dry_run", "counts")}, indent=2))


def _cmd_validate(_: argparse.Namespace) -> None:
    from tsf_mcp.validation import validate_text

    catalog = Catalog()
    failed = 0
    for skill in catalog.skills.values():
        report = validate_text(skill.raw, skill.rel_dir.rsplit("/", 1)[-1], skill.rel_dir)
        if report["errors"] or report["warnings"]:
            status = "FAIL" if report["errors"] else "warn"
            failed += bool(report["errors"])
            print(f"{status}  {skill.rel_dir}: {'; '.join(report['errors'] + report['warnings'])}")
    for problem in catalog.load_problems:
        print(f"FAIL  {problem}")
    print(f"{len(catalog.skills)} skills checked, {failed + len(catalog.load_problems)} with errors.")
    sys.exit(1 if failed or catalog.load_problems else 0)


def _cmd_catalog(_: argparse.Namespace) -> None:
    catalog = Catalog()
    path = catalog.root / "CATALOG.md"
    path.write_text(resources.catalog_markdown(catalog) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(catalog.skills)} skills)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tsf-mcp", description="TestSkill Finder MCP server")
    parser.add_argument("--transport", choices=["stdio", "http"], default=config.transport())
    parser.add_argument("--host", default=config.host())
    parser.add_argument("--port", type=int, default=config.port())
    parser.add_argument("--allow-write", action="store_true", default=config.allow_write(), help="Enable create_skill and sync_skills_from_github")
    sub = parser.add_subparsers(dest="command")
    sync_parser = sub.add_parser("sync", help="Download upstream skills into the skills folder")
    sync_parser.add_argument("--ref", default=config.UPSTREAM_REF)
    sync_parser.add_argument("--dry-run", action="store_true")
    sub.add_parser("validate", help="Check every SKILL.md against the catalog format")
    sub.add_parser("catalog", help="Regenerate skills/CATALOG.md")
    args = parser.parse_args()

    if args.command == "sync":
        return _cmd_sync(args)
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "catalog":
        return _cmd_catalog(args)

    if args.transport == "stdio":
        create_server(allow_write=args.allow_write).run(transport="stdio", show_banner=False)
        return

    from starlette.middleware import Middleware

    from tsf_mcp.landing import BrowserLandingPage

    auth = None
    token = config.auth_token()
    if token:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        auth = StaticTokenVerifier(tokens={token: {"client_id": "tsf-team", "scopes": []}})
    elif args.host not in ("127.0.0.1", "localhost"):
        print("[tsf-mcp] WARNING: serving on a non-local host without TSF_AUTH_TOKEN; anyone who can reach it can use it.", file=sys.stderr)
    mcp = create_server(allow_write=args.allow_write, auth=auth)
    # Stateless: no per-session state, so proxies and tunnels never hit "Missing session ID".
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
