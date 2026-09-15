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
    "load_dataset",
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
  der Wissensbasis passt — dann nenn den Artikel beim Namen. Sage nicht „Bibel“.

Wenn die Person um Zusatzübungen bittet: `exercise_context` lesen, mit `load_dataset`
eigene Tabellen anlegen falls nötig, mit `draft_exercise` bauen,
mit `validate_exercise` prüfen und erst dann `save_practice`. Übungen brauchen einen `explain`-Schritt
(Alltagssprache plus antippbare SQL-Teile) und `teach` an den Schreib-Schritten.
Nach `save_practice`: nenn Titel und den Pfad `/playground/{id}`. Sag nicht, die Person solle neu
laden, und erwähne `reachable` nicht — die App aktualisiert den Playground selbst.
"""

_STATUS_CACHE: dict | None = None

CLI_NAMES = ("claude.exe", "claude.cmd", "claude.bat", "claude")
NATIVE_INSTALL_SH = "https://claude.ai/install.sh"


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


def native_bin_dir() -> Path:
    return user_home() / ".local" / "bin"


def package_home() -> Path:
    env_home = (os.environ.get("LEARN_SQL_HOME") or "").strip()
    if env_home:
        return Path(env_home)
    return Path(__file__).resolve().parent.parent


def _candidate_dirs() -> list[Path]:
    """Folders where a native, npm, or WinGet install may land."""
    home = user_home()
    out = [
        native_bin_dir(),
        home / ".claude" / "local",
        home / "bin",
    ]
    local = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local:
        out.append(Path(local) / "Programs" / "claude")
    appdata = (os.environ.get("APPDATA") or "").strip()
    if appdata:
        out.append(Path(appdata) / "npm")
    return out


def _candidates() -> list[Path]:
    """Places the CLI hides when it is not on PATH."""
    out: list[Path] = []
    for folder in _candidate_dirs():
        for name in CLI_NAMES:
            out.append(folder / name)
    return out


def path_with_cli_dirs(path_value: str | None = None) -> str:
    """Put native install dirs first so Flask sees claude.exe without a reboot."""
    raw = path_value if path_value is not None else (os.environ.get("PATH") or "")
    parts = [p for p in raw.split(os.pathsep) if p]
    extras = [str(folder) for folder in _candidate_dirs() if folder.is_dir()]
    for extra in reversed(extras):
        if extra not in parts:
            parts.insert(0, extra)
    return os.pathsep.join(parts)


def find_claude() -> Path | None:
    """Locate the claude binary: env override, PATH, then the usual install spots."""
    override = (os.environ.get("CLAUDE_CLI") or "").strip()
    if override:
        path = Path(override).expanduser()
        return path if path.exists() else None
    search_path = path_with_cli_dirs()
    found = shutil.which("claude", path=search_path)
    if found:
        return Path(found)
    if os.name == "nt":
        for suffix in (".cmd", ".exe", ".bat"):
            found = shutil.which("claude" + suffix, path=search_path)
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


def probe_logged_in(path: Path) -> bool | None:
    """True / False from `claude auth status`. None if the CLI is too old to say."""
    try:
        proc = subprocess.run(
            [str(path), "auth", "status"],
            capture_output=True,
            text=True,
            timeout=20,
            env=build_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    combined = f"{proc.stdout or ''}{proc.stderr or ''}"
    low = combined.lower()
    if "unknown" in low or "unrecognized" in low or "unknown command" in low:
        return None
    raw = (proc.stdout or "").strip()
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and "loggedIn" in data:
            return bool(data.get("loggedIn"))
    if proc.returncode == 0:
        return True
    return False


def _status_payload(
    *,
    available: bool,
    path: str | None,
    version: str | None = None,
    parsed: tuple[int, ...] | None = None,
    logged_in: bool | None = None,
    error: str | None = None,
) -> dict:
    if not available:
        state = "not_found"
    elif logged_in is False:
        state = "not_logged_in"
    else:
        state = "ready"
    return {
        "available": available,
        "path": path,
        "version": version,
        "parsed": parsed,
        "logged_in": logged_in,
        "state": state,
        "ready": state == "ready",
        "error": error,
    }


def probe_claude() -> dict:
    """Ask the CLI for its version and whether a subscription login exists."""
    path = find_claude()
    if not path:
        return _status_payload(available=False, path=None, error="not_found")
    try:
        proc = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            env=build_env(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return _status_payload(available=False, path=str(path), error=str(exc))
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:200]
        return _status_payload(available=False, path=str(path), error=detail or "exit")
    raw = (proc.stdout or "").strip()
    logged_in = probe_logged_in(path)
    error = None if logged_in is not False else "not_logged_in"
    return _status_payload(
        available=True,
        path=str(path),
        version=raw.split()[0] if raw else None,
        parsed=parse_version(raw),
        logged_in=logged_in,
        error=error,
    )


def claude_status(refresh: bool = False) -> dict:
    """Cached probe — spawning the CLI on every page render would be silly."""
    global _STATUS_CACHE
    if refresh or _STATUS_CACHE is None:
        _STATUS_CACHE = probe_claude()
    return _STATUS_CACHE


def public_status(refresh: bool = False) -> dict:
    """JSON for the drawer — no filesystem paths."""
    status = claude_status(refresh=refresh)
    return {
        "state": status.get("state") or "not_found",
        "available": bool(status.get("available")),
        "logged_in": status.get("logged_in"),
        "ready": bool(status.get("ready")),
        "version": status.get("version"),
        "error": status.get("error"),
    }


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
    env["PATH"] = path_with_cli_dirs(env.get("PATH") or env.get("Path") or "")
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
    # So save_practice can confirm /playground/{id} without runtime.json
    # (local `python app/app.py`, Docker). 0.0.0.0 is bind-all, not a URL host.
    env["APP_URL"] = app_base_url()
    return env


def app_base_url() -> str:
    explicit = (os.environ.get("APP_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    host = (os.environ.get("APP_HOST") or "127.0.0.1").strip() or "127.0.0.1"
    if host in ("0.0.0.0", "::", "[::]"):
        host = "127.0.0.1"
    port = (os.environ.get("APP_PORT") or "8080").strip() or "8080"
    return f"http://{host}:{port}"


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


def playground_href(url: str | None, lid: str) -> str:
    """Turn an absolute save_practice URL into a same-origin path."""
    lid = str(lid or "").strip()
    default = f"/playground/{lid}" if lid else "/playground"
    raw = str(url or "").strip()
    if not raw:
        return default
    if "://" in raw:
        parts = raw.split("/", 3)
        raw = "/" + parts[3] if len(parts) > 3 else default
    path = raw.split("?")[0]
    return path if path.startswith("/playground") else default


def _tool_result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


def _parse_json_blob(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def practice_event(name: str | None, payload: dict) -> dict | None:
    """SSE payload when Claude saves or deletes a playground exercise."""
    tool = str(name or "")
    if not tool:
        if payload.get("saved") or (payload.get("id") and payload.get("url")):
            tool = "save_practice"
        elif "deleted" in payload:
            tool = "delete_practice"
    if tool == "save_practice":
        lid = str(payload.get("id") or "").strip()
        if not lid:
            return None
        return {
            "action": "save",
            "id": lid,
            "title": str(payload.get("title") or lid),
            "url": playground_href(payload.get("url"), lid),
        }
    if tool == "delete_practice":
        ids = payload.get("deleted") or payload.get("ids") or []
        if isinstance(ids, str):
            ids = [ids]
        if not ids and payload.get("id"):
            ids = [payload.get("id")]
        ids = [str(item).strip() for item in ids if str(item).strip()]
        if not ids:
            return None
        return {
            "action": "delete",
            "id": ids[0],
            "ids": ids,
            "title": str(payload.get("title") or ids[0]),
            "url": "/playground",
        }
    return None


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
                uid = block.get("id")
                if uid:
                    state.setdefault("tool_ids", {})[str(uid)] = name
                yield "tool", {"name": name}
            continue

        if kind == "user":
            content = (msg.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                if block.get("is_error"):
                    yield "notice", {
                        "kind": "tool_error",
                        "text": "Ein Werkzeug hat nicht geklappt — Claude versucht es anders.",
                    }
                    continue
                payload = _parse_json_blob(_tool_result_text(block))
                if not payload:
                    continue
                name = state.get("tool_ids", {}).get(str(block.get("tool_use_id") or ""))
                event = practice_event(name, payload)
                if event:
                    yield "practice", event
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
            "text": "Claude Code ist nicht angemeldet. Im Buddy auf Anmelden tippen.",
        }
    if any(h in low for h in QUOTA_HINTS):
        return {
            "code": "quota",
            "text": "Dein Claude-Kontingent ist gerade aufgebraucht. Später nochmal versuchen.",
        }
    if "unknown option" in low or "unknown argument" in low:
        return {
            "code": "old_cli",
            "text": "Claude Code ist zu alt. Im Buddy auf Claude Code einrichten tippen, oder den Native Installer von claude.ai nutzen.",
        }
    return {
        "code": "failed",
        "text": f"Claude Code hat abgebrochen (Code {returncode}).",
    }


def ensure_script_path() -> Path | None:
    home = package_home()
    for cand in (
        home / "Ensure-ClaudeCode.ps1",
        home / "installer" / "runtime" / "Ensure-ClaudeCode.ps1",
    ):
        if cand.is_file():
            return cand
    return None


def install_claude_code() -> dict:
    """Best-effort native CLI install. Never raises — the app must still start."""
    if find_claude():
        return {"ok": True, "status": public_status(refresh=True), "skipped": True}
    timeout = 300
    try:
        if os.name == "nt":
            script = ensure_script_path()
            if not script:
                return {
                    "ok": False,
                    "error": "Das Einrichten-Skript fehlt. Bitte plx.learnSQL neu installieren.",
                    "status": public_status(refresh=True),
                }
            proc = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-HomeDir",
                    str(package_home()),
                    "-Quiet",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip()[:400]
                return {
                    "ok": False,
                    "error": detail or "Claude Code konnte nicht eingerichtet werden.",
                    "status": public_status(refresh=True),
                }
        else:
            proc = subprocess.run(
                ["bash", "-lc", f"curl -fsSL {NATIVE_INSTALL_SH} | bash"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip()[:400]
                return {
                    "ok": False,
                    "error": detail or "Claude Code konnte nicht eingerichtet werden.",
                    "status": public_status(refresh=True),
                }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "ok": False,
            "error": str(exc)[:300],
            "status": public_status(refresh=True),
        }
    status = public_status(refresh=True)
    return {"ok": bool(status.get("available")), "status": status, "skipped": False}


def start_login() -> dict:
    """Open a real console for `claude auth login` so a paste-code prompt works."""
    path = find_claude()
    if not path:
        return {
            "ok": False,
            "code": "not_found",
            "error": "Claude Code wurde auf diesem Rechner nicht gefunden.",
            "status": public_status(refresh=True),
        }
    env = build_env()
    try:
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
            subprocess.Popen(
                [
                    "cmd.exe",
                    "/k",
                    f'title plx.learnSQL - Claude anmelden & "{path}" auth login',
                ],
                creationflags=flags,
                cwd=str(user_home()),
                env=env,
                close_fds=False,
            )
        else:
            launched = False
            for argv in (
                ["x-terminal-emulator", "-e", str(path), "auth", "login"],
                ["gnome-terminal", "--", str(path), "auth", "login"],
                ["xterm", "-T", "plx.learnSQL - Claude anmelden", "-e", str(path), "auth", "login"],
            ):
                try:
                    subprocess.Popen(
                        argv,
                        cwd=str(user_home()),
                        env=env,
                        start_new_session=True,
                    )
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            if not launched:
                return {
                    "ok": False,
                    "error": "Kein Terminal gefunden. Im Terminal ausführen: claude auth login",
                    "status": public_status(),
                }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc)[:300], "status": public_status()}
    return {"ok": True, "status": public_status()}
