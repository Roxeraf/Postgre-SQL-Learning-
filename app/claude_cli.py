"""Talk to the local Claude Code CLI from the app.

The app is an MCP *server* — Claude pulls context through `mcp/learnsql_mcp.py`.
That direction cannot carry a question from the app to Claude, so the buddy chat
turns the app into a *client* instead: it runs the installed `claude` binary in
headless mode (`claude -p`). That reuses the machine's own Claude Code login, so
no API key and no extra Anthropic dependency are needed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import uuid
from pathlib import Path

SERVER_NAME = "learnsql"

# Minimum CLI version that understands --permission-prompts.
PERMISSION_PROMPTS_SINCE = (2, 1, 259)

# learnsql tools the buddy may call. Everything else — including every built-in
# shell/file tool — stays out of reach.
ALLOWED_TOOLS = [
    "buddy_context",
    "help_with",
    "coach_sql",
    "search_wissen",
    "get_article",
    "list_cards",
    "search_path",
    "list_lessons",
    "get_lesson",
    "schema",
    "sample_rows",
    "table_rows",
    "run_sql",
    "exercise_context",
    "step_schema",
    "draft_exercise",
    "validate_exercise",
    "save_practice",
    "list_workshop",
    "delete_practice",
]

BLOCKED_TOOLS = [
    "Bash",
    "Edit",
    "Write",
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
]

BUDDY_PERSONA = """Du bist der Lern-Buddy in plx.learnSQL, einer deutschen Lern-App für PostgreSQL.
Die Person lernt gerade und sitzt in der App — sie sieht deine Antwort in einem schmalen Seitenfenster.

Lies als Erstes `buddy_context`. Darin steht, wo die Person gerade ist: Kapitel, Schritt, Aufgabe,
letzte Query und letzter Hinweis der App. Frag nicht nach, was da schon drinsteht.

So antwortest du:
- Deutsch, per du, ruhig und ohne Fachjargon-Nebel.
- Erklär am Lager der App: den Tabellen `orders`, `clients`, `stock`, `order_items`.
- Gib den nächsten Denkschritt, nicht die fertige Musterlösung — außer die Person verlangt die
  Lösung ausdrücklich.
- Kurz halten: ein paar Sätze, höchstens ein kleines SQL-Beispiel. Keine Überschriften-Kaskaden.
- Bei einer Frage zu SQL, das die Person geschrieben hat: `coach_sql` benutzen.
- Bei einer Verständnisfrage: `help_with`, und `search_wissen` / `get_article`, wenn eine Stelle aus
  der Bibel passt — dann nenn sie beim Namen.

Wenn die Person um Zusatzübungen bittet: `exercise_context` lesen, mit `draft_exercise` bauen,
mit `validate_exercise` prüfen und erst dann `save_practice`. Übungen brauchen einen `explain`-Schritt
(Alltagssprache plus antippbare SQL-Teile) und `teach` an den Schreib-Schritten.
"""

_STATUS_CACHE: dict | None = None


def _install_mcp():
    """Import mcp/install_mcp.py — app.py already put the folder on sys.path."""
    try:
        import install_mcp
    except ImportError:
        return None
    return install_mcp


def user_home() -> Path:
    helper = _install_mcp()
    if helper:
        return helper.user_home()
    for key in ("USERPROFILE", "HOME"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            return Path(raw).expanduser()
    return Path.home()


def _candidates() -> list[Path]:
    """Places the CLI hides when it is not on PATH."""
    home = user_home()
    out = [
        home / ".claude" / "local" / "claude",
        home / ".local" / "bin" / "claude",
        home / "bin" / "claude",
    ]
    local = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local:
        out.append(Path(local) / "Programs" / "claude" / "claude.exe")
        out.append(Path(local) / "Programs" / "claude" / "claude.cmd")
    appdata = (os.environ.get("APPDATA") or "").strip()
    if appdata:
        out.append(Path(appdata) / "npm" / "claude.cmd")
        out.append(Path(appdata) / "npm" / "claude.exe")
    return out


def find_claude() -> Path | None:
    """Locate the claude binary: env override, PATH, then the usual install spots."""
    override = (os.environ.get("CLAUDE_CLI") or "").strip()
    if override:
        path = Path(override).expanduser()
        return path if path.exists() else None
    found = shutil.which("claude")
    if found:
        return Path(found)
    if os.name == "nt":
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which("claude" + suffix)
            if found:
                return Path(found)
    for cand in _candidates():
        if cand.is_file():
            return cand
    return None


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def probe_claude() -> dict:
    """Ask the CLI for its version. Used for the badge and for feature gating."""
    path = find_claude()
    if not path:
        return {"available": False, "path": None, "version": None, "error": "not_found"}
    try:
        proc = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            env=build_env(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "path": str(path), "version": None, "error": str(exc)}
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:200]
        return {"available": False, "path": str(path), "version": None, "error": detail or "exit"}
    raw = (proc.stdout or "").strip()
    return {
        "available": True,
        "path": str(path),
        "version": raw.split()[0] if raw else None,
        "parsed": parse_version(raw),
        "error": None,
    }


def claude_status(refresh: bool = False) -> dict:
    """Cached probe — spawning the CLI on every page render would be silly."""
    global _STATUS_CACHE
    if refresh or _STATUS_CACHE is None:
        _STATUS_CACHE = probe_claude()
    return _STATUS_CACHE


def build_env() -> dict:
    """A clean environment for the child.

    When the app itself is started from inside a Claude Code session, the
    process inherits a pile of CLAUDE_* variables — including the parent's
    session id, which the child would then adopt as its own. Strip them and
    hand over only the database settings the learnsql MCP server needs.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    env.pop("CLAUDECODE", None)
    # The whole point is to spend the machine's Claude Code subscription. An
    # exported API key would silently win and bill an API account instead.
    if os.environ.get("BUDDY_ALLOW_API_KEY") != "1":
        for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
            env.pop(key, None)
    for key, value in (server_env() or {}).items():
        env.setdefault(key, str(value))
    # learnsql_mcp.py imports psycopg2 and every lesson module before it answers
    # `initialize`. On a cold disk that beats the 30 s default, and Claude then
    # reports the server as failed and answers with no tools at all.
    env.setdefault("MCP_TIMEOUT", "60000")
    env.setdefault("MCP_TOOL_TIMEOUT", "60000")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def server_env() -> dict:
    """Database settings for the learnsql MCP server, as install_mcp defines them.

    WORKSHOP_DIR is overridden with the folder the running app actually uses.
    install_mcp derives it from the Windows install layout ({app}\\workshop);
    in a checkout the app reads data/workshop instead. If the two disagree, the
    buddy reads a stale .learner-context.json and answers about the wrong step.
    """
    helper = _install_mcp()
    env: dict = {}
    if helper:
        try:
            entry = helper.learnsql_server_entry(helper.resolve_home())
        except Exception:
            entry = {}
        env = dict(entry.get("env") or {})
    # learnsql_server_entry hardcodes DB_HOST/DB_NAME/DB_USER and reads DB_PORT
    # only from runtime.json. When Flask runs against its own database (local
    # dev against `docker compose up db`), the app's environment is the truth —
    # otherwise the MCP child queries a different database than the Playground.
    for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "LEARN_SQL_HOME"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    try:
        from lessons.workshop import workshop_dir

        env["WORKSHOP_DIR"] = str(workshop_dir())
    except Exception:
        pass
    return env


def mcp_config_path(target_dir: Path) -> Path | None:
    """Write {"mcpServers": {"learnsql": ...}} for --mcp-config.

    A file rather than inline JSON: the entry carries Windows paths full of
    backslashes, and quoting that through cmd.exe is a good way to lose an
    evening.
    """
    helper = _install_mcp()
    if not helper:
        return None
    try:
        entry = helper.learnsql_server_entry(helper.resolve_home())
    except Exception:
        return None
    entry = dict(entry)
    entry["env"] = {**(entry.get("env") or {}), **server_env()}
    # learnsql_server_entry falls back to Path(sys.executable).resolve(), and
    # resolve() follows a virtualenv's symlink out to the system interpreter —
    # which has none of the app's dependencies, so every run_sql would die with
    # "psycopg2 ist nicht installiert". Run the child on the very interpreter
    # serving this request. The Windows package ships its own python; that one
    # is a real file, not a symlink, so it is left alone.
    command = str(entry.get("command") or "")
    if not command.lower().endswith("python.exe"):
        entry["command"] = sys.executable

    payload = {"mcpServers": {SERVER_NAME: entry}}
    path = Path(target_dir) / ".claude-buddy-mcp.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def new_session_id() -> str:
    return str(uuid.uuid4())


def build_argv(
    prompt: str,
    mcp_path: Path | None = None,
    session_id: str | None = None,
    cli_path: Path | str | None = None,
    version: tuple[int, ...] | None = None,
) -> list[str]:
    """The exact command line for one buddy turn."""
    binary = str(cli_path or find_claude() or "claude")
    argv = [
        binary,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--permission-mode",
        "dontAsk",
        "--disable-slash-commands",
        # No user/project settings, hooks or CLAUDE.md. The buddy answers SQL
        # questions; it has no business inheriting a coding setup.
        "--setting-sources",
        "",
    ]
    # Older CLIs reject the flag outright and never start.
    if version is None or version >= PERMISSION_PROMPTS_SINCE:
        argv += ["--permission-prompts", "none"]
    if mcp_path:
        argv += ["--mcp-config", str(mcp_path), "--strict-mcp-config"]
        argv.append("--allowedTools")
        argv += [f"mcp__{SERVER_NAME}__{name}" for name in ALLOWED_TOOLS]
    argv.append("--disallowedTools")
    argv += list(BLOCKED_TOOLS)
    argv += ["--append-system-prompt", BUDDY_PERSONA]
    if session_id:
        argv += ["--resume", session_id]
    return argv


# --- running one turn ---------------------------------------------------------

def spawn(argv: list[str], cwd, env: dict | None = None) -> subprocess.Popen:
    """Start the CLI in its own process group.

    The group matters: `claude` spawns `python learnsql_mcp.py`, which holds a
    psycopg2 connection. Killing only the CLI orphans that child, and a handful
    of aborted answers leaks enough connections for Postgres to start refusing.
    """
    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=str(cwd),
        env=env if env is not None else build_env(),
        **kwargs,
    )


def terminate(proc: subprocess.Popen) -> None:
    """Take the whole process group down, not just the CLI."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=10,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:
        proc.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        else:
            proc.kill()
    except (OSError, ValueError):
        pass
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass


def tool_label(raw: str) -> str:
    """mcp__learnsql__coach_sql -> coach_sql"""
    text = str(raw or "")
    return text.rsplit("__", 1)[-1] or text


def iter_events(lines, state: dict | None = None):
    """Turn the CLI's NDJSON into the handful of events the drawer needs.

    Pure and line-based so tests can feed it a list. Anything unrecognised is
    dropped on purpose — the CLI emits a lot of housekeeping (`commands_changed`
    alone is ~25 KB) and none of it belongs in a browser.
    """
    state = state if state is not None else {}
    for raw in lines:
        raw = (raw or "").strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            state["bad"] = state.get("bad", 0) + 1
            continue
        if not isinstance(msg, dict):
            continue
        # Subagent chatter must never land in the learner's bubble.
        if msg.get("parent_tool_use_id"):
            continue
        kind = msg.get("type")
        subtype = msg.get("subtype")

        if kind == "system" and subtype == "init":
            state["init"] = True
            state["session_id"] = msg.get("session_id") or state.get("session_id")
            servers = [s for s in (msg.get("mcp_servers") or []) if isinstance(s, dict)]
            connected = [s for s in servers if s.get("status") == "connected"]
            yield "init", {
                "session_id": state.get("session_id"),
                "model": msg.get("model"),
                "mcp_ok": bool(connected),
            }
            continue

        if kind == "system" and subtype == "api_retry":
            yield "notice", {
                "kind": "retry",
                "text": f"Claude ist gerade ausgelastet — Versuch {msg.get('attempt')}…",
            }
            continue

        if kind == "stream_event":
            delta = (msg.get("event") or {}).get("delta") or {}
            if delta.get("type") == "text_delta":
                text = str(delta.get("text") or "")
                if text:
                    state["chars"] = state.get("chars", 0) + len(text)
                    yield "delta", {"text": text}
            continue

        if kind == "assistant":
            content = (msg.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                raw = str(block.get("name") or "")
                # Only our own tools get a line in the drawer. Claude Code's
                # built-ins (ToolSearch and friends) are plumbing, not progress.
                if not raw.startswith(f"mcp__{SERVER_NAME}__"):
                    continue
                name = tool_label(raw)
                state.setdefault("tools", set()).add(name)
                yield "tool", {"name": name}
            continue

        if kind == "user":
            content = (msg.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    if block.get("is_error"):
                        yield "notice", {
                            "kind": "tool_error",
                            "text": "Ein Werkzeug hat nicht geklappt — Claude versucht es anders.",
                        }
            continue

        if kind == "result":
            state["done"] = True
            state["session_id"] = msg.get("session_id") or state.get("session_id")
            yield "done", {
                "ok": not msg.get("is_error"),
                "text": str(msg.get("result") or ""),
                "session_id": state.get("session_id"),
                "cost": msg.get("total_cost_usd"),
                "tools_used": sorted(state.get("tools", [])),
            }
            continue


AUTH_HINTS = ("login", "log in", "authenticat", "oauth", "credential", "unauthorized", "api key")
QUOTA_HINTS = ("rate limit", "quota", "usage limit", "credit", "overloaded")
STALE_HINTS = ("no conversation found", "session id", "not found")


def explain_failure(returncode: int | None, stderr: str, resumed: bool) -> dict:
    """Turn a dead CLI into something a learner can act on."""
    text = (stderr or "").strip()
    low = text.lower()
    if resumed and any(h in low for h in STALE_HINTS):
        return {"code": "stale_session", "text": "Das alte Gespräch war weg — Claude fängt neu an."}
    if any(h in low for h in AUTH_HINTS):
        return {
            "code": "auth",
            "text": "Claude Code ist nicht angemeldet. Einmal `claude` im Terminal starten und anmelden.",
        }
    if any(h in low for h in QUOTA_HINTS):
        return {
            "code": "quota",
            "text": "Dein Claude-Kontingent ist gerade aufgebraucht. Später nochmal versuchen.",
        }
    if "unknown option" in low or "unknown argument" in low:
        return {
            "code": "old_cli",
            "text": "Claude Code ist zu alt. Bitte aktualisieren: npm update -g @anthropic-ai/claude-code",
        }
    return {
        "code": "failed",
        "text": f"Claude Code hat abgebrochen (Code {returncode}).",
    }
