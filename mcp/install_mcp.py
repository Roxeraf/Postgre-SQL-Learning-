#!/usr/bin/env python3
"""Merge LearnSQL MCP into Claude Desktop config. Used by the Windows installer."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


SERVER_NAME = "learnsql"
STATUS_NAME = "mcp-status.json"


def resolve_home(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("LEARN_SQL_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def is_install_home(home: Path) -> bool:
    return (home / "python" / "python.exe").is_file() or (home / "runtime.json").is_file()


def apply_runtime_env(home: Path | None = None) -> dict:
    """Set DB_PORT from runtime.json and WORKSHOP_DIR for the installed app."""
    home = home or resolve_home()
    applied = {"home": str(home), "db_port": None, "workshop": None}
    runtime_path = home / "runtime.json"
    if runtime_path.is_file():
        try:
            data = json.loads(runtime_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        port = data.get("dbPort") or data.get("db_port")
        if port and not os.environ.get("DB_PORT"):
            os.environ["DB_PORT"] = str(port)
            applied["db_port"] = str(port)
    if os.environ.get("LEARN_SQL_HOME") or is_install_home(home):
        workshop = home / "workshop"
        os.environ.setdefault("WORKSHOP_DIR", str(workshop))
        os.environ.setdefault("DB_HOST", "127.0.0.1")
        os.environ.setdefault("DB_NAME", "learnsql")
        os.environ.setdefault("DB_USER", "lernuser")
        os.environ.setdefault("DB_PASSWORD", "lernuser")
        applied["workshop"] = os.environ.get("WORKSHOP_DIR")
    return applied


def learnsql_server_entry(home: Path) -> dict:
    bundled = home / "python" / "python.exe"
    command = str(bundled if bundled.is_file() else Path(sys.executable).resolve())
    return {
        "command": command,
        "args": [str(home / "mcp" / "learnsql_mcp.py")],
        "env": {
            "DB_HOST": "127.0.0.1",
            "DB_NAME": "learnsql",
            "DB_USER": "lernuser",
            "DB_PASSWORD": "lernuser",
            "LEARN_SQL_HOME": str(home),
            "WORKSHOP_DIR": str(home / "workshop"),
        },
    }


def merge_mcp_config(existing: dict, name: str, entry: dict) -> dict:
    data = dict(existing) if isinstance(existing, dict) else {}
    servers = dict(data.get("mcpServers") or {})
    servers[name] = entry
    data["mcpServers"] = servers
    return data


def write_json_with_backup(path: Path, data: dict) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.is_file():
        backup = path.with_name(path.name + ".bak")
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return backup


def claude_is_installed() -> bool:
    appdata = os.environ.get("APPDATA") or ""
    local = os.environ.get("LOCALAPPDATA") or ""
    if appdata and (Path(appdata) / "Claude").is_dir():
        return True
    if local:
        packages = Path(local) / "Packages"
        if packages.is_dir() and any(packages.glob("Claude_*")):
            return True
        for cand in (Path(local) / "Programs" / "Claude", Path(local) / "AnthropicClaude"):
            if cand.exists():
                return True
    return False


def claude_config_paths(*, include_standard: bool = True) -> list[Path]:
    paths: list[Path] = []
    appdata = os.environ.get("APPDATA") or ""
    local = os.environ.get("LOCALAPPDATA") or ""
    if include_standard and appdata:
        paths.append(Path(appdata) / "Claude" / "claude_desktop_config.json")
    if local:
        packages = Path(local) / "Packages"
        if packages.is_dir():
            for pkg in sorted(packages.glob("Claude_*")):
                paths.append(
                    pkg / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"
                )
    # unique, keep order
    seen = set()
    unique = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _read_config(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_status(home: Path, status: dict) -> Path:
    path = home / STATUS_NAME
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_status(home: Path | None = None) -> dict | None:
    candidates = []
    if home:
        candidates.append(Path(home) / STATUS_NAME)
    env = os.environ.get("LEARN_SQL_HOME")
    if env:
        candidates.append(Path(env) / STATUS_NAME)
    candidates.append(Path(__file__).resolve().parents[1] / STATUS_NAME)
    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                return data
    return None


def install(home: Path) -> dict:
    home = home.resolve()
    (home / "workshop").mkdir(parents=True, exist_ok=True)
    entry = learnsql_server_entry(home)
    written = []
    backups = []
    for path in claude_config_paths(include_standard=True):
        merged = merge_mcp_config(_read_config(path), SERVER_NAME, entry)
        backup = write_json_with_backup(path, merged)
        written.append(str(path))
        if backup:
            backups.append(str(backup))
    status = {
        "installed": bool(written),
        "detected": claude_is_installed(),
        "targets": written,
        "backups": backups,
        "home": str(home),
    }
    write_status(home, status)
    return status


def uninstall(home: Path) -> dict:
    removed = []
    for path in claude_config_paths(include_standard=True):
        if not path.is_file():
            continue
        data = _read_config(path)
        servers = data.get("mcpServers")
        if not isinstance(servers, dict) or SERVER_NAME not in servers:
            continue
        servers = dict(servers)
        del servers[SERVER_NAME]
        data["mcpServers"] = servers
        write_json_with_backup(path, data)
        removed.append(str(path))
    status = {
        "installed": False,
        "removed": removed,
        "home": str(home.resolve()),
    }
    write_status(home, status)
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LearnSQL MCP in Claude Desktop eintragen.")
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--home", default="", help="Installationsverzeichnis von plx.learnSQL")
    args = parser.parse_args(argv)
    home = resolve_home(args.home or None)
    if args.action == "install":
        result = install(home)
    elif args.action == "uninstall":
        result = uninstall(home)
    else:
        result = load_status(home) or {"installed": False, "detected": claude_is_installed()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
