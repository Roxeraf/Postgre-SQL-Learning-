const STORE_KEY = "flowapp-learn-v1";

function loadStore() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY)) || { lessons: {}, lastLesson: null };
  } catch {
    return { lessons: {}, lastLesson: null };
  }
}

function saveStore(store) {
  localStorage.setItem(STORE_KEY, JSON.stringify(store));
}

function lessonState(store, id) {
  if (!store.lessons[id]) {
    store.lessons[id] = { visited: false, sections: [], exercises: {}, quiz: {}, complete: false };
  }
  return store.lessons[id];
}

function lessonComplete(state, exerciseCount, quizCount) {
  const exDone = exerciseCount === 0 || Object.values(state.exercises || {}).filter(Boolean).length >= exerciseCount;
  const quizDone = quizCount === 0 || Object.keys(state.quiz || {}).length >= quizCount;
  return lessonStarted(state) && exDone && quizDone;
}

function lessonStarted(state) {
  if (!state) return false;
  if ((state.sections || []).length) return true;
  if (Object.values(state.exercises || {}).some(Boolean)) return true;
  if (Object.keys(state.quiz || {}).length) return true;
  return false;
}

function refreshChrome() {
  const store = loadStore();
  const items = [...document.querySelectorAll(".lesson-list li[data-lesson-id], .path-card[data-lesson-id]")];
  const ids = [...document.querySelectorAll(".lesson-list li[data-lesson-id]")].map((el) => el.dataset.lessonId);
  let done = 0;
  ids.forEach((id) => {
    const state = store.lessons[id];
    const complete = state?.complete;
    const started = lessonStarted(state);
    if (complete) done += 1;
    document.querySelectorAll(`[data-lesson-id="${id}"]`).forEach((el) => {
      el.classList.toggle("done", Boolean(complete));
      el.classList.toggle("started", started && !complete);
      const badge = el.querySelector(".path-state");
      if (badge) badge.textContent = complete ? "Fertig" : started ? "Begonnen" : "Offen";
    });
  });
  const pct = ids.length ? Math.round((done / ids.length) * 100) : 0;
  const ring = document.querySelector(".progress-ring");
  if (ring) {
    ring.style.setProperty("--p", String(pct));
    ring.querySelector("span").textContent = `${pct}%`;
  }
  const meta = document.getElementById("progress-meta");
  if (meta) {
    const startedCount = ids.filter((id) => lessonStarted(store.lessons[id])).length;
    meta.textContent = done
      ? `${done} von ${ids.length} Lektionen`
      : startedCount
        ? `${startedCount} begonnen`
        : "Noch nicht gestartet";
  }
  const stat = document.getElementById("stat-done");
  if (stat) stat.textContent = `${done}/${ids.length}`;
  const cont = document.getElementById("continue-btn");
  if (cont) {
    const incomplete = ids.find((id) => !store.lessons[id]?.complete);
    const last = store.lastLesson;
    const stay = last && ids.includes(last) && !store.lessons[last]?.complete ? last : null;
    const next = done === ids.length ? ids[0] : stay || incomplete || ids[0];
    if (next) {
      cont.href = `/lesson/${next}`;
      cont.textContent = done === ids.length
        ? "Nochmal von vorn"
        : lessonStarted(store.lessons[next])
          ? `Weiter mit Teil ${next.toUpperCase()}`
          : next === "sql"
            ? "Mit SQL-Grundlagen beginnen"
        : next === ids[0]
            ? "Mit der ersten Lektion beginnen"
            : `Teil ${(next || "").toUpperCase()} öffnen`;
    }
  }
  return store;
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function colorizeSql(text) {
  const esc = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return esc
    .replace(/(--[^\n]*)/g, '<span class="cm">$1</span>')
    .replace(/('(?:\\'|[^'])*')/g, '<span class="str">$1</span>')
    .replace(
      /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|NULL|AS|WITH|INSERT|UPDATE|DELETE|BEGIN|COMMIT|ROLLBACK|LIMIT|ORDER|BY|GROUP|HAVING|DISTINCT|CASE|WHEN|THEN|ELSE|END|OVER|PARTITION|ROW_NUMBER|COALESCE|NULLIF|CAST|INTERVAL|UNION|ALL|IN|IS|BETWEEN|EXISTS|MATERIALIZED|FILTER|STRING_AGG|COUNT|MD5)\b/gi,
      '<span class="kw">$1</span>'
    );
}

function renderTable(columns, rows) {
  if (!columns || columns.length === 0) return '<p class="muted">Keine Spalten im Ergebnis.</p>';
  if (!rows || rows.length === 0) return '<p class="muted">Abfrage erfolgreich, aber keine Zeilen zurückgegeben.</p>';
  let html = '<div class="table-wrap"><table class="result-table"><thead><tr>';
  columns.forEach((c) => (html += `<th>${esc(c)}</th>`));
  html += "</tr></thead><tbody>";
  rows.forEach((row) => {
    html += "<tr>";
    columns.forEach((c) => {
      const v = row[c];
      html += `<td>${v === null || v === undefined ? "<em>NULL</em>" : esc(v)}</td>`;
    });
    html += "</tr>";
  });
  html += "</tbody></table></div>";
  return html;
}

function renderSqlResult(data) {
  const parts = [];
  (data.messages || []).forEach((m) => parts.push(`<p class="muted">${esc(m)}</p>`));
  if (data.columns && data.columns.length) {
    parts.push(renderTable(data.columns, data.rows));
  } else if (!parts.length) {
    parts.push('<p class="muted">Ausgeführt — keine Ergebnistabelle.</p>');
  }
  if (data.note) parts.push(`<p class="muted">${esc(data.note)}</p>`);
  return parts.join("");
}

function splitSections(markdown) {
  const lines = markdown.split("\n");
  const sections = [];
  let title = "Überblick";
  let body = [];
  const push = () => {
    const text = body.join("\n").trim();
    if (text) sections.push({ title, body: text });
  };
  lines.forEach((line) => {
    const match = line.match(/^##\s+(.+)/);
    if (match) {
      push();
      title = match[1];
      body = [];
    } else {
      body.push(line);
    }
  });
  push();
  return sections.length ? sections : [{ title: "Inhalt", body: markdown }];
}

let lastEditor = null;
document.addEventListener("focusin", (e) => {
  if (e.target.classList?.contains("sql-editor")) lastEditor = e.target;
});

function activeSqlEditor(preferred) {
  if (preferred && preferred.classList?.contains("sql-editor")) return preferred;
  return (
    document.querySelector(".exercise.is-active .sql-editor") ||
    lastEditor ||
    document.querySelector(".sql-editor")
  );
}

function flashEditor(editor) {
  editor.classList.remove("just-inserted");
  void editor.offsetWidth;
  editor.classList.add("just-inserted");
  window.setTimeout(() => editor.classList.remove("just-inserted"), 800);
}

function isSqlIdent(text) {
  return /^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)*$/.test(text);
}

function isInsideSqlCommentOrString(sql, index) {
  let i = 0;
  let inSingle = false;
  while (i < index) {
    const ch = sql[i];
    if (!inSingle && ch === "-" && sql[i + 1] === "-") {
      const nl = sql.indexOf("\n", i);
      if (nl < 0 || nl >= index) return true;
      i = nl + 1;
      continue;
    }
    if (ch === "'") {
      if (inSingle && sql[i + 1] === "'") {
        i += 2;
        continue;
      }
      inSingle = !inSingle;
    }
    i += 1;
  }
  return inSingle;
}

function sqlKeywordSpans(sql, keyword) {
  const re = new RegExp(`\\b${keyword}\\b`, "gi");
  const spans = [];
  let match;
  while ((match = re.exec(sql))) {
    if (isInsideSqlCommentOrString(sql, match.index)) continue;
    spans.push({ index: match.index, length: match[0].length });
  }
  return spans;
}

function selectListIsEmpty(text) {
  return !String(text || "").replace(/--[^\n]*/g, "").replace(/\s+/g, "");
}

function selectLists(sql) {
  const selects = sqlKeywordSpans(sql, "SELECT");
  const froms = sqlKeywordSpans(sql, "FROM");
  const lists = [];
  selects.forEach((sel) => {
    const from = froms.find((item) => item.index > sel.index);
    if (!from) return;
    let start = sel.index + sel.length;
    const after = sql.slice(start, from.index);
    const distinct = after.match(/^\s*(DISTINCT|ALL)\b/i);
    if (distinct) start += distinct[0].length;
    lists.push({
      start,
      end: from.index,
      text: sql.slice(start, from.index),
    });
  });
  return lists;
}

function namesInSelectList(text) {
  return String(text || "")
    .replace(/--[^\n]*/g, " ")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

function selectItemBare(name) {
  return String(name || "")
    .replace(/--[^\n]*/g, " ")
    .trim()
    .split(/\s+as\s+/i)[0]
    .trim()
    .replace(/[(),]/g, " ")
    .trim()
    .split(/\s+/)
    .pop()
    .split(".")
    .pop()
    .toLowerCase();
}

function selectListHasColumn(text, col) {
  const want = selectItemBare(col);
  if (!want) return false;
  return namesInSelectList(text).some((n) => selectItemBare(n) === want);
}

const SQL_ALIAS_STOP = /^(on|where|left|right|inner|outer|full|cross|join|select|group|order|limit|having|union|except|intersect|set|and|or|natural|using|returning|window|fetch|offset|for|when|then|else|end|distinct|all|as|with|from)$/i;

function tableShortFromQualified(name) {
  let short = String(name || "").split(".").pop().toLowerCase();
  for (const prefix of ["flowapp_demo_", "flowapp_13d663_"]) {
    if (short.startsWith(prefix)) {
      short = short.slice(prefix.length);
      break;
    }
  }
  return short;
}

function fromSegmentForSelectList(sql, list) {
  const start = list.end;
  let depth = 0;
  let end = sql.length;
  for (let i = start; i < sql.length; i += 1) {
    const ch = sql[i];
    if (ch === "(") depth += 1;
    else if (ch === ")") {
      if (depth === 0) {
        end = i;
        break;
      }
      depth -= 1;
    }
  }
  const stops = sqlKeywordSpans(sql, "WHERE")
    .concat(sqlKeywordSpans(sql, "GROUP"))
    .concat(sqlKeywordSpans(sql, "ORDER"))
    .concat(sqlKeywordSpans(sql, "LIMIT"))
    .concat(sqlKeywordSpans(sql, "HAVING"))
    .concat(sqlKeywordSpans(sql, "UNION"))
    .filter((item) => item.index > start && item.index < end)
    .sort((a, b) => a.index - b.index);
  if (stops.length) end = Math.min(end, stops[0].index);
  return { start, end, text: sql.slice(start, end) };
}

function aliasesInFromSegment(sql, list) {
  const map = {};
  if (!list) return map;
  const segment = fromSegmentForSelectList(sql, list).text.replace(/--[^\n]*/g, " ");
  const re = /\b(?:FROM|JOIN)\s+((?:[A-Za-z_][\w]*\.)?[A-Za-z_][\w]*)\s+(?:AS\s+)?([A-Za-z_][\w]*)/gi;
  let match;
  while ((match = re.exec(segment))) {
    const alias = match[2];
    if (SQL_ALIAS_STOP.test(alias)) continue;
    const short = tableShortFromQualified(match[1]);
    if (!map[short]) map[short] = [];
    if (!map[short].includes(alias)) map[short].push(alias);
  }
  return map;
}

function qualifyColumn(col, tableShort, sql, list) {
  if (!tableShort || !isSqlIdent(col)) return col;
  const aliases = aliasesInFromSegment(sql, list);
  const hits = aliases[String(tableShort).toLowerCase()] || [];
  if (hits.length === 1) return `${hits[0]}.${col}`;
  return col;
}

function showSchemaInsert(text) {
  const rail = document.getElementById("schema-rail");
  if (!rail) return;
  let status = rail.querySelector(".schema-insert-status");
  if (!status) {
    status = document.createElement("p");
    status.className = "schema-insert-status";
    const head = rail.querySelector(".schema-rail-head");
    (head || rail).insertAdjacentElement("afterend", status);
  }
  status.textContent = `Eingefügt: ${text}`;
}

function insertIntoSelectList(editor, list, col) {
  if (selectListHasColumn(list.text, col)) {
    editor.focus();
    flashEditor(editor);
    showSchemaInsert(col);
    return;
  }
  const names = namesInSelectList(list.text);
  let body = list.text.replace(/\s+$/, "");
  if (names.length) {
    const codeTail = body.replace(/--[^\n]*$/, "").replace(/\s+$/, "");
    if (!/,\s*$/.test(codeTail)) body += ",";
  }
  const newList = `${body}\n  ${col}\n`;
  editor.value = editor.value.slice(0, list.start) + newList + editor.value.slice(list.end);
  const pos = list.start + newList.length;
  lastEditor = editor;
  editor.focus();
  editor.selectionStart = editor.selectionEnd = pos;
  flashEditor(editor);
  showSchemaInsert(col);
}

function placeCaretInEmptySelect(editor) {
  if (!editor) return;
  const empty = selectLists(editor.value).find((list) => selectListIsEmpty(list.text));
  if (!empty) return;
  const pos = empty.start + empty.text.replace(/\s+$/, "").length;
  editor.selectionStart = editor.selectionEnd = pos;
}

function insertAtCursor(text, editorEl, tableShort) {
  const editor = activeSqlEditor(editorEl);
  if (!editor) {
    navigator.clipboard?.writeText(text);
    return;
  }
  lastEditor = editor;
  const lists = selectLists(editor.value);
  let start = editor.selectionStart ?? 0;
  let end = editor.selectionEnd ?? start;
  const focused = document.activeElement === editor;
  const caretParked = start === 0 && end === 0;
  const useDefaultSlot = !focused || caretParked;
  const ident = isSqlIdent(text);
  const inList = lists.find((list) => start >= list.start && start <= list.end);
  const empty = lists.find((list) => selectListIsEmpty(list.text));
  const qualifyAgainst = inList || empty || (lists.length === 1 ? lists[0] : null);
  const insertText = ident ? qualifyColumn(text, tableShort, editor.value, qualifyAgainst) : String(text);

  if (ident && lists.length) {
    if (inList && (selectListIsEmpty(inList.text) || useDefaultSlot)) {
      insertIntoSelectList(editor, inList, insertText);
      return;
    }
    if (empty && useDefaultSlot) {
      insertIntoSelectList(editor, empty, insertText);
      return;
    }
    if (useDefaultSlot && lists.length === 1) {
      insertIntoSelectList(editor, lists[0], insertText);
      return;
    }
  }

  if (useDefaultSlot) {
    start = end = editor.value.length;
  }

  let insert = insertText;
  const before = editor.value.slice(0, start);
  if (ident && /[A-Za-z0-9_]$/.test(before.replace(/\s+$/, "")) && !/,\s*$/.test(before) && !/\($/.test(before.replace(/\s+$/, ""))) {
    insert = `, ${insertText}`;
  }
  editor.value = editor.value.slice(0, start) + insert + editor.value.slice(end);
  editor.focus();
  editor.selectionStart = editor.selectionEnd = start + insert.length;
  flashEditor(editor);
  showSchemaInsert(insertText);
}

async function postJson(url, body, timeoutMs = 15000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    return await res.json();
  } catch (err) {
    if (err.name === "AbortError") {
      return {
        ok: false,
        error: "Die Abfrage dauert zu lange oder der Server antwortet nicht. Läuft die App / Datenbank?",
      };
    }
    return { ok: false, error: "Keine Verbindung zum Server. Läuft die App auf Port 8080?" };
  } finally {
    clearTimeout(timer);
  }
}

function initResetDb() {
  const run = async (btn) => {
    const ok = window.confirm(
      "Lern-Datenbank auf den Ausgangszustand zurücksetzen?\nDeine bisherigen UPDATE/DELETE-Übungen gehen verloren."
    );
    if (!ok) return;
    if (btn) btn.disabled = true;
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      const data = await res.json();
      window.alert(data.ok ? data.message : `Zurücksetzen fehlgeschlagen: ${data.error}`);
    } catch {
      window.alert("Zurücksetzen fehlgeschlagen.");
    } finally {
      if (btn) btn.disabled = false;
    }
  };
  document.querySelectorAll("#reset-db, .js-reset-db").forEach((btn) => {
    btn.addEventListener("click", () => run(btn));
  });
}

function initNav() {
  const toggle = document.getElementById("nav-toggle");
  const backdrop = document.getElementById("nav-backdrop");
  const close = () => document.body.classList.remove("nav-open");
  toggle?.addEventListener("click", () => document.body.classList.toggle("nav-open"));
  backdrop?.addEventListener("click", close);
  document.getElementById("conn-toggle")?.addEventListener("click", (e) => {
    const btn = e.currentTarget;
    const body = document.querySelector(".conn-body");
    const open = body.hasAttribute("hidden");
    body.toggleAttribute("hidden", !open);
    btn.setAttribute("aria-expanded", String(open));
  });
}

function initSchema() {
  const drawer = document.getElementById("schema-drawer");
  const list = document.getElementById("schema-list");
  const search = document.getElementById("schema-search");
  const railList = document.getElementById("schema-rail-list");
  const railMeta = document.getElementById("schema-rail-meta");
  let tables = [];
  let railShorts = null;
  let railShowAll = false;

  const ensure = async () => {
    if (tables.length) return tables;
    try {
      const res = await fetch("/api/schema");
      const data = await res.json();
      tables = data.tables || [];
    } catch {
      tables = [];
    }
    return tables;
  };

  const tableCard = (t, { open = false, insertable = true } = {}) => `
      <details class="schema-table" data-short="${esc(t.short)}"${open ? " open" : ""}>
        <summary>
          <span class="insert-name">${esc(t.label || t.short)}</span>
          <span class="schema-type">${esc(t.short)}${t.kind ? " · " + esc(t.kind) : ""}</span>
        </summary>
        ${t.parent ? `<p class="schema-parent">hängt an: ${esc(t.parent)}</p>` : ""}
        <div class="schema-cols">
          ${t.columns
            .map((c) =>
              insertable
                ? `<button class="schema-col" type="button" data-insert="${esc(c.name)}" data-table="${esc(t.short)}">
              <span>${esc(c.name)}</span><span class="schema-type">${esc(c.type)}</span>
            </button>`
                : `<div class="schema-col is-static">
              <span>${esc(c.name)}</span><span class="schema-type">${esc(c.type)}</span>
            </div>`
            )
            .join("")}
          <button class="btn ghost schema-preview" type="button" data-preview-schema="${t.schema}" data-preview-table="${t.name}">Vorschau (8 Zeilen)</button>
        </div>
      </details>`;

  const matchesQuery = (t, q) => {
    if (!q) return true;
    const blob = `${t.qualified} ${t.short} ${t.label || ""} ${t.parent || ""} ${t.columns.map((c) => c.name).join(" ")}`.toLowerCase();
    return blob.includes(q);
  };

  const renderDrawer = () => {
    if (!list) return;
    const q = (search?.value || "").toLowerCase();
    const filtered = tables.filter((t) => matchesQuery(t, q));
    list.innerHTML = filtered.map((t) => tableCard(t, { open: false, insertable: true })).join("") || '<p class="muted">Kein Treffer.</p>';
  };

  const renderRail = () => {
    if (!railList) return;
    const shorts = !railShowAll && railShorts ? new Set(railShorts) : null;
    const filtered = shorts ? tables.filter((t) => shorts.has(t.short)) : tables;
    railList.innerHTML = filtered.map((t) => tableCard(t, { open: Boolean(shorts), insertable: true })).join("") || '<p class="muted">Keine Tabellen zu dieser Übung.</p>';
    const need = document.getElementById("schema-rail-need");
    if (need) {
      const needTables = railShorts ? tables.filter((t) => railShorts.includes(t.short)) : [];
      need.innerHTML = needTables
        .map((t) => `<li><strong>${esc(t.label || t.short)}</strong> <span class="chip-tech">${esc(t.short)}</span></li>`)
        .join("");
    }
    if (railMeta) {
      railMeta.textContent = shorts
        ? `Tabellen zu dieser Übung (${filtered.length}) — deutsche Namen aus dem Datenprofil.`
        : `Alle Tabellen (${filtered.length}). Suche im Schema-Explorer links in der Navigation.`;
    }
  };

  window.focusExerciseSchema = async (shorts) => {
    railShorts = shorts && shorts.length ? shorts : null;
    railShowAll = false;
    await ensure();
    renderRail();
  };

  window.highlightSchemaTable = (short) => {
    if (!railList || !short) return;
    railList.querySelectorAll(".schema-table").forEach((el) => {
      const match = el.dataset.short === short;
      el.classList.toggle("is-flash", match);
      if (match) {
        el.open = true;
        el.scrollIntoView({ block: "nearest" });
      }
    });
  };

  const open = async () => {
    if (!drawer) return;
    drawer.hidden = false;
    await ensure();
    renderDrawer();
  };
  const close = () => {
    if (!drawer) return;
    drawer.hidden = true;
  };

  document.getElementById("open-schema")?.addEventListener("click", open);
  document.querySelectorAll("[data-open-schema]").forEach((btn) => btn.addEventListener("click", open));
  document.getElementById("close-schema")?.addEventListener("click", close);
  search?.addEventListener("input", renderDrawer);
  document.getElementById("schema-rail-all")?.addEventListener("click", async () => {
    railShowAll = true;
    await ensure();
    renderRail();
  });

  const onSchemaClick = async (e) => {
    const insert = e.target.closest("[data-insert]");
    if (insert) {
      e.preventDefault();
      e.stopPropagation();
      insertAtCursor(insert.dataset.insert, null, insert.dataset.table);
      return;
    }
    const preview = e.target.closest("[data-preview-table]");
    if (!preview) return;
    const res = await fetch("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ schema: preview.dataset.previewSchema, table: preview.dataset.previewTable }),
    });
    const data = await res.json();
    const host = preview.parentElement.querySelector(".preview-result") || document.createElement("div");
    host.className = "preview-result";
    host.innerHTML = data.ok ? renderTable(data.columns, data.rows) : `<p class="error">${data.error}</p>`;
    preview.after(host);
  };
  list?.addEventListener("click", onSchemaClick);
  railList?.addEventListener("click", onSchemaClick);
  if (railList) ensure();
}

function initLesson() {
  const article = document.querySelector(".lesson");
  const contentEl = document.getElementById("lesson-content");
  if (!article || !contentEl) return;

  const lessonId = article.dataset.lessonId;
  const exerciseCount = Number(article.dataset.exerciseCount || 0);
  const quizCount = Number(article.dataset.quizCount || 0);
  const store = loadStore();
  const state = lessonState(store, lessonId);
  state.visited = true;
  store.lastLesson = lessonId;
  saveStore(store);

  let markdown = "";
  try {
    markdown = JSON.parse(contentEl.getAttribute("data-markdown"));
  } catch {
    contentEl.textContent = "Inhalt konnte nicht geladen werden.";
    return;
  }

  const sections = splitSections(markdown);
  const nav = document.getElementById("section-nav");
  contentEl.innerHTML = sections
    .map(
      (s, i) =>
        `<section class="lesson-section${i === 0 ? " active" : ""}" data-section="${i}">
          <h2>${s.title}</h2>
          ${marked.parse(s.body)}
        </section>`
    )
    .join("");
  contentEl.querySelectorAll("pre code").forEach((el) => {
    el.innerHTML = colorizeSql(el.textContent);
  });
  contentEl.querySelectorAll("pre").forEach((pre) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-sql";
    btn.textContent = "Kopieren";
    btn.addEventListener("click", async () => {
      const text = pre.querySelector("code")?.textContent || "";
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Kopiert";
        window.setTimeout(() => { btn.textContent = "Kopieren"; }, 1200);
      } catch {
        btn.textContent = "Kopieren";
      }
    });
    pre.appendChild(btn);
  });

  nav.innerHTML = sections
    .map(
      (s, i) =>
        `<button type="button" class="section-chip${i === 0 ? " active" : ""}" data-section="${i}">${i + 1}. ${s.title.replace(/^([A-Z]\.\d+\s)/, "")}</button>`
    )
    .join("");

  let current = 0;
  let primed = false;
  const show = (idx) => {
    current = Math.max(0, Math.min(idx, sections.length - 1));
    contentEl.querySelectorAll(".lesson-section").forEach((el, i) => el.classList.toggle("active", i === current));
    nav.querySelectorAll(".section-chip").forEach((el, i) => {
      el.classList.toggle("active", i === current);
      if (state.sections.includes(i)) el.classList.add("read");
    });
    document.getElementById("prev-section").hidden = current === 0;
    const next = document.getElementById("next-section");
    const prog = document.getElementById("section-progress");
    if (prog) prog.textContent = `Abschnitt ${current + 1} von ${sections.length}`;
    if (current === sections.length - 1) {
      next.textContent = exerciseCount ? "Zu den SQL-Aufgaben →" : quizCount ? "Zum Kurzcheck →" : "Abschnitt gelesen";
    } else {
      next.textContent = "Weiter →";
    }
    if (!state.sections.includes(current) && primed) {
      state.sections.push(current);
      saveStore(store);
    }
  };
  nav.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-section]");
    if (chip) show(Number(chip.dataset.section));
  });
  document.getElementById("prev-section")?.addEventListener("click", () => show(current - 1));
  document.getElementById("next-section")?.addEventListener("click", () => {
    if (current < sections.length - 1) {
      show(current + 1);
      return;
    }
    if (!state.sections.includes(current)) {
      state.sections.push(current);
      saveStore(store);
    }
    if (exerciseCount) switchTab("practice");
    else if (quizCount) switchTab("quiz");
  });
  show(0);
  primed = true;

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });

  initExercises(lessonId, exerciseCount, quizCount);
  initQuiz(lessonId, exerciseCount, quizCount);

  const hash = (location.hash || "").replace("#", "");
  if (hash === "practice" || hash === "quiz") switchTab(hash);
}

const PHASE_HINTS = {
  learn: "Lies den Abschnitt. Unten auf Weiter — nicht die ganze Lektion auf einmal.",
  practice: "Rechts Tabelle aufklappen, Spalte klicken, Ausführen, dann Stimmt das?.",
  quiz: "Eine Antwort wählen — danach kommt die Erklärung. Falsch ist ok.",
};

let practiceIndex = 0;

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.dataset.panel === name));
  document.querySelector(".content")?.classList.toggle("content-wide", name === "practice");
  const hint = document.getElementById("phase-hint");
  if (hint && PHASE_HINTS[name]) hint.textContent = PHASE_HINTS[name];
  if (name === "practice") showExercise(practiceIndex, { focus: true });
}

function showExercise(idx, opts = {}) {
  const all = [...document.querySelectorAll(".exercise")];
  if (!all.length) return;
  practiceIndex = Math.max(0, Math.min(idx, all.length - 1));
  all.forEach((el, i) => el.classList.toggle("is-current", i === practiceIndex));
  focusExercise(all[practiceIndex]);
  const stepper = document.getElementById("ex-stepper");
  if (stepper) {
    stepper.innerHTML = all
      .map((el, i) => {
        const current = i === practiceIndex;
        const done = el.classList.contains("is-ok");
        return `<button type="button" class="ex-dot${current ? " current" : ""}${done ? " done" : ""}" data-ex-index="${i}">Aufgabe ${i + 1}</button>`;
      })
      .join("");
  }
  if (opts.focus) {
    const editor = all[practiceIndex].querySelector(".sql-editor");
    if (editor) {
      editor.focus();
      placeCaretInEmptySelect(editor);
    }
  }
}

function focusExercise(exerciseEl) {
  document.querySelectorAll(".exercise").forEach((el) => el.classList.toggle("is-active", el === exerciseEl));
  const editor = exerciseEl.querySelector(".sql-editor");
  if (editor) lastEditor = editor;
  let shorts = [];
  try {
    shorts = JSON.parse(exerciseEl.getAttribute("data-tables") || "[]");
  } catch {
    shorts = [];
  }
  window.focusExerciseSchema?.(shorts);
}

function markLessonProgress(lessonId, exerciseCount, quizCount) {
  const store = loadStore();
  const state = lessonState(store, lessonId);
  state.complete = lessonComplete(state, exerciseCount, quizCount);
  saveStore(store);
  refreshChrome();
}

function initExercises(lessonId, exerciseCount, quizCount) {
  const store = loadStore();
  const state = lessonState(store, lessonId);

  document.querySelectorAll(".exercise").forEach((exerciseEl) => {
    const exerciseId = exerciseEl.getAttribute("data-exercise-id");
    const editor = exerciseEl.querySelector(".sql-editor");
    const resultEl = exerciseEl.querySelector(".exercise-result");
    const hintBtn = exerciseEl.querySelector('[data-action="hint"]');
    const badge = exerciseEl.querySelector("[data-ex-badge]");
    let hintLevel = 0;
    lastEditor = lastEditor || editor;

    const guide = exerciseEl.querySelector(".exercise-guide");
    if (state.exercises[exerciseId]) {
      exerciseEl.classList.add("is-ok");
      if (badge) badge.textContent = "Gelöst";
      if (guide) guide.open = false;
    } else if (guide) {
      guide.open = true;
    }

    const runAction = async (action) => {
      const sql = editor.value;
      const actionBtns = [...exerciseEl.querySelectorAll("button[data-action]")];
      if (action === "hint") {
        hintLevel += 1;
        const res = await fetch(`/api/hint/${exerciseId}?level=${hintLevel}`);
        const data = await res.json();
        if (!data.ok) {
          resultEl.innerHTML = `<p class="error">${data.error}</p>`;
          return;
        }
        if (data.kind === "hint") {
          resultEl.innerHTML = `<div class="hint-box"><strong>Hinweis ${data.level} / ${data.total - 1}</strong><p>${data.text}</p></div>`;
          if (hintBtn) hintBtn.textContent = hintLevel >= data.total - 1 ? "Lösung zeigen" : `Hinweis ${hintLevel + 1}`;
        } else {
          resultEl.innerHTML = `<div class="solution-box"><strong>Musterlösung</strong><pre>${colorizeSql(data.solution)}</pre></div>`;
          if (hintBtn) hintBtn.textContent = "Lösung";
        }
        return;
      }

      resultEl.innerHTML = '<p class="muted">Führe Abfrage aus…</p>';
      actionBtns.forEach((btn) => { btn.disabled = true; });
      try {
        if (action === "run") {
          const data = await postJson("/api/run", { sql });
          if (!data.ok) {
            resultEl.innerHTML = data.empty_select
              ? `<div class="hint-box"><strong>Noch nicht ausgeführt</strong><p>${esc(data.error)}</p></div>`
              : `<p class="error">${esc(data.error)}</p>`;
            return;
          }
          resultEl.innerHTML = renderSqlResult(data);
        }

        if (action === "check") {
          const data = await postJson("/api/check", { sql, exercise_id: exerciseId });
          if (!data.ok) {
            resultEl.innerHTML = `<p class="error">Fehler: ${esc(data.error)}</p>`;
            return;
          }
          const verdict = data.correct
            ? '<p class="verdict verdict-ok">Stimmt. Dein Ergebnis passt zur Musterlösung.</p>'
            : `<p class="verdict verdict-fail">Noch nicht. ${esc(data.coach || "")}</p>`;
          const hasTable = data.columns && data.columns.length;
          const hasMsg = data.messages && data.messages.length;
          resultEl.innerHTML = verdict + (hasTable || hasMsg ? renderSqlResult(data) : "");
          if (data.correct) {
            exerciseEl.classList.add("is-ok");
            if (badge) badge.textContent = "Gelöst";
            if (guide) guide.open = false;
            const s = loadStore();
            lessonState(s, lessonId).exercises[exerciseId] = true;
            saveStore(s);
            markLessonProgress(lessonId, exerciseCount, quizCount);
            const all = [...document.querySelectorAll(".exercise")];
            const idx = all.indexOf(exerciseEl);
            const hasNext = idx >= 0 && idx < all.length - 1;
            const quizBtn = exerciseEl.querySelector("[data-goto-quiz]");
            if (hasNext) {
              resultEl.insertAdjacentHTML(
                "beforeend",
                '<p class="next-after-ok"><button class="btn btn-primary" type="button" data-ex-advance>Nächste Aufgabe →</button></p>'
              );
            } else if (quizBtn) {
              quizBtn.hidden = false;
            }
            showExercise(idx >= 0 ? idx : practiceIndex);
          }
        }
      } finally {
        actionBtns.forEach((btn) => { btn.disabled = false; });
      }
    };

    exerciseEl.querySelectorAll("button[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => runAction(btn.getAttribute("data-action")));
    });
    exerciseEl.querySelector("[data-ex-prev]")?.addEventListener("click", () => {
      showExercise(Math.max(0, practiceIndex - 1), { focus: true });
    });
    exerciseEl.querySelector("[data-ex-next]")?.addEventListener("click", () => {
      showExercise(practiceIndex + 1, { focus: true });
    });
    exerciseEl.querySelector("[data-goto-quiz]")?.addEventListener("click", () => switchTab("quiz"));
    exerciseEl.addEventListener("click", (e) => {
      if (e.target.closest("[data-ex-advance]")) {
        showExercise(practiceIndex + 1, { focus: true });
        return;
      }
      if (e.target.closest("[data-ex-prev], [data-ex-next], [data-goto-quiz], .ex-dot")) return;
      focusExercise(exerciseEl);
    });
    exerciseEl.addEventListener("focusin", () => focusExercise(exerciseEl));
    editor.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runAction("run");
      }
    });
  });

  document.getElementById("ex-stepper")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-ex-index]");
    if (btn) showExercise(Number(btn.dataset.exIndex), { focus: true });
  });

  const all = [...document.querySelectorAll(".exercise")];
  const firstOpen = all.findIndex((el) => !el.classList.contains("is-ok"));
  practiceIndex = firstOpen >= 0 ? firstOpen : 0;
  if (all.length) showExercise(practiceIndex);
}

function initQuiz(lessonId, exerciseCount, quizCount) {
  const scoreEl = document.getElementById("quiz-score");
  const questions = [...document.querySelectorAll(".quiz-question")];
  const updateScore = () => {
    const answered = questions.filter((q) => q.dataset.answered === "1").length;
    const correct = questions.filter((q) => q.dataset.wasCorrect === "1").length;
    if (scoreEl) scoreEl.textContent = answered ? `${correct} / ${questions.length} richtig` : "";
  };

  questions.forEach((q, qi) => {
    const correctIndex = parseInt(q.getAttribute("data-correct"), 10);
    let explain = q.getAttribute("data-explain") || "";
    try {
      explain = JSON.parse(explain);
    } catch {
      /* plain string */
    }
    const feedback = q.querySelector(".quiz-feedback");
    const options = q.querySelectorAll(".quiz-option");
    options.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (q.dataset.answered === "1") return;
        const chosen = parseInt(btn.getAttribute("data-index"), 10);
        const ok = chosen === correctIndex;
        q.dataset.answered = "1";
        q.dataset.wasCorrect = ok ? "1" : "0";
        options.forEach((b, i) => {
          b.disabled = true;
          if (i === correctIndex) b.classList.add("correct");
        });
        if (!ok) btn.classList.add("wrong");
        feedback.innerHTML = ok
          ? `<p class="verdict verdict-ok">Richtig.</p><p class="muted">${explain || ""}</p>`
          : `<p class="verdict verdict-fail">Nicht ganz.</p><p class="muted">${explain || "Schau nochmal in den Lerntext."}</p>`;
        const s = loadStore();
        lessonState(s, lessonId).quiz[qi] = ok;
        saveStore(s);
        markLessonProgress(lessonId, exerciseCount, quizCount);
        updateScore();
      });
    });
  });
}

function initPlayground() {
  const editor = document.getElementById("pg-editor");
  const resultEl = document.getElementById("pg-result");
  const runBtn = document.getElementById("pg-run");
  if (!editor || !runBtn) return;
  lastEditor = editor;
  const run = async () => {
    resultEl.innerHTML = '<p class="muted">Führe Abfrage aus…</p>';
    runBtn.disabled = true;
    try {
      const data = await postJson("/api/run", { sql: editor.value });
      if (!data.ok) {
        resultEl.innerHTML = `<p class="error">Fehler: ${esc(data.error)}</p>`;
        return;
      }
      resultEl.innerHTML = renderSqlResult(data);
    } finally {
      runBtn.disabled = false;
    }
  };
  runBtn.addEventListener("click", run);
  editor.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      run();
    }
  });
}

function initCards() {
  const cardEl = document.getElementById("flashcard");
  if (!cardEl) return;
  const frontEl = document.getElementById("card-front");
  const backEl = document.getElementById("card-back");
  const kickerEl = document.getElementById("card-kicker");
  const progressEl = document.getElementById("card-progress");
  const filterEl = document.getElementById("card-filter");
  let all = [];
  let deck = [];
  let i = 0;

  const show = () => {
    cardEl.classList.remove("flipped");
    if (!deck.length) {
      frontEl.textContent = "Keine Karten in diesem Filter.";
      backEl.textContent = "";
      progressEl.textContent = "0 / 0";
      return;
    }
    const card = deck[i % deck.length];
    kickerEl.textContent = card.lesson || "Karteikarte";
    frontEl.textContent = card.front;
    backEl.textContent = card.back;
    progressEl.textContent = `${(i % deck.length) + 1} / ${deck.length}`;
  };
  const rebuild = () => {
    const f = filterEl.value;
    deck = all.filter((c) => !f || c.lesson_id === f);
    i = 0;
    show();
  };

  fetch("/api/cards")
    .then((r) => r.json())
    .then((data) => {
      all = data.cards || [];
      rebuild();
    });

  cardEl.addEventListener("click", () => cardEl.classList.toggle("flipped"));
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement === cardEl) {
      e.preventDefault();
      cardEl.classList.toggle("flipped");
    }
  });
  document.getElementById("card-again")?.addEventListener("click", () => {
    if (!deck.length) return;
    const [card] = deck.splice(i % deck.length, 1);
    deck.push(card);
    show();
  });
  document.getElementById("card-got-it")?.addEventListener("click", () => {
    if (!deck.length) return;
    deck.splice(i % deck.length, 1);
    if (i >= deck.length) i = 0;
    show();
  });
  filterEl?.addEventListener("change", rebuild);
}

function initWissen() {
  const input = document.getElementById("wissen-q");
  const resultsEl = document.getElementById("wissen-results");
  const meta = document.getElementById("wissen-meta");
  if (!input || !resultsEl) return;

  const typeLabel = {
    lektion: "Lektion",
    abschnitt: "Abschnitt",
    karte: "Karte",
    übung: "Übung",
  };

  const render = (data, query) => {
    if (!query || query.length < 2) {
      resultsEl.innerHTML = "";
      if (meta) meta.textContent = "Mindestens zwei Zeichen — Suche läuft über alle Lektionen.";
      return;
    }
    const rows = data.results || [];
    if (meta) {
      meta.textContent = rows.length
        ? `${rows.length} Treffer in der Einarbeitung`
        : "Kein Treffer — anderen Begriff versuchen (Tabellenname, Statuscode, Alias).";
    }
    resultsEl.innerHTML = rows
      .map(
        (r) => `
      <a class="wissen-hit" href="${r.url}">
        <span class="wissen-kicker">Teil ${esc(r.letter)} · ${esc(typeLabel[r.type] || r.type)}</span>
        <strong>${esc(r.title)}</strong>
        <span class="muted">${esc(r.snippet || "")}</span>
      </a>`
      )
      .join("");
  };

  let timer = null;
  const run = async (value) => {
    const q = (value ?? input.value).trim();
    if (q.length < 2) {
      render({ results: [] }, q);
      return;
    }
    resultsEl.innerHTML = '<p class="muted">Suche…</p>';
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    render(data, q);
  };

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => run(), 180);
  });
  document.getElementById("wissen-chips")?.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-q]");
    if (!chip) return;
    input.value = chip.dataset.q;
    run(chip.dataset.q);
  });

  const params = new URLSearchParams(window.location.search);
  if (params.get("q")) {
    input.value = params.get("q");
    run(input.value);
  } else {
    input.focus();
  }
}

initNav();
initSchema();
initLesson();
initPlayground();
initCards();
initWissen();
initResetDb();
refreshChrome();

