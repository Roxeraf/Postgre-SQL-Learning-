const STORE_KEY = "learnsql-v3";
const STORE_KEY_V1 = "flowapp-learn-v1";
const STORE_KEY_V2 = "flowapp-learn-v2";

function emptyStore() {
  return {
    version: 3,
    onboarded: false,
    lessons: {},
    lastLesson: null,
    lastAcademy: null,
    academy: { lessons: {} },
    mastery: {},
    xp: 0,
    streak: 0,
    lastActivity: null,
  };
}

function loadStore() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      return { ...emptyStore(), ...JSON.parse(raw) };
    }
  } catch {
    /* fall through */
  }
  try {
    const v2 = JSON.parse(localStorage.getItem(STORE_KEY_V2) || "null");
    if (v2) {
      return { ...emptyStore(), ...v2, version: 3 };
    }
  } catch {
    /* ignore */
  }
  try {
    const v1 = JSON.parse(localStorage.getItem(STORE_KEY_V1) || "null");
    if (v1) {
      return {
        ...emptyStore(),
        onboarded: Boolean(v1.lastLesson || Object.keys(v1.lessons || {}).length),
        lessons: v1.lessons || {},
        lastLesson: v1.lastLesson || null,
      };
    }
  } catch {
    /* ignore */
  }
  return emptyStore();
}

function saveStore(store) {
  localStorage.setItem(STORE_KEY, JSON.stringify(store));
}

function academyState(store, id) {
  if (!store.academy) store.academy = { lessons: {} };
  if (!store.academy.lessons[id]) {
    store.academy.lessons[id] = { steps: {}, quiz: {}, complete: false, current: 0 };
  }
  return store.academy.lessons[id];
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
  const academyItems = [...document.querySelectorAll("[data-academy-id]")];
  const academyIds = [...document.querySelectorAll(".lesson-list li[data-academy-id]")].map((el) => el.dataset.academyId);
  let sqlDone = 0;
  academyIds.forEach((id) => {
    const state = store.academy?.lessons?.[id];
    const complete = Boolean(state?.complete);
    const started = Boolean(state && (state.complete || Object.keys(state.steps || {}).length));
    if (complete) sqlDone += 1;
    document.querySelectorAll(`[data-academy-id="${id}"]`).forEach((el) => {
      el.classList.toggle("done", complete);
      el.classList.toggle("started", started && !complete);
      const badge = el.querySelector(".path-state");
      if (badge) badge.textContent = complete ? "Fertig" : started ? "Begonnen" : "Offen";
    });
  });
  const sqlPct = academyIds.length ? Math.round((sqlDone / academyIds.length) * 100) : 0;

  const ring = document.querySelector(".progress-ring");
  if (ring) {
    ring.style.setProperty("--p", String(sqlPct));
    ring.querySelector("span").textContent = `${sqlPct}%`;
  }
  const meta = document.getElementById("progress-meta");
  if (meta) {
    meta.textContent = sqlDone
      ? `${sqlDone} von ${academyIds.length} Kapitel`
      : academyIds.some((id) => store.academy?.lessons?.[id] && Object.keys(store.academy.lessons[id].steps || {}).length)
        ? "In Bearbeitung"
        : "Noch nicht gestartet";
  }
  const barSql = document.getElementById("bar-sql");
  const pctSql = document.getElementById("pct-sql");
  if (barSql) barSql.style.width = `${sqlPct}%`;
  if (pctSql) pctSql.textContent = `${sqlPct}%`;

  const statSql = document.getElementById("stat-sql");
  if (statSql) statSql.textContent = `${sqlDone}/${academyIds.length || document.querySelectorAll(".path-academy [data-academy-id]").length}`;
  let doneStepsAll = 0;
  Object.values(store.academy?.lessons || {}).forEach((lesson) => {
    doneStepsAll += Object.keys(lesson.steps || {}).length;
  });
  const statSteps = document.getElementById("stat-steps");
  if (statSteps) statSteps.textContent = String(doneStepsAll);

  const cont = document.getElementById("continue-btn");
  const nextAcademy = nextAcademyLesson(store, academyIds);
  if (cont && nextAcademy) {
    const started = Boolean(store.academy?.lessons?.[nextAcademy] && Object.keys(store.academy.lessons[nextAcademy].steps || {}).length);
    cont.href = `/learn/${nextAcademy}`;
    cont.textContent = store.onboarded || started ? "Weiterlernen" : "Lernen starten";
  }
  return store;
}

function nextAcademyLesson(store, ids) {
  if (!ids.length) {
    ids = [...document.querySelectorAll(".lesson-list li[data-academy-id]")].map((el) => el.dataset.academyId);
  }
  const last = store.lastAcademy;
  if (last && ids.includes(last) && !store.academy?.lessons?.[last]?.complete) return last;
  return ids.find((id) => !store.academy?.lessons?.[id]?.complete) || ids[0];
}

function initDashboard() {
  const startHero = document.getElementById("hero-start");
  if (!startHero) return;
  const store = loadStore();
  const ids = [...document.querySelectorAll(".path-academy [data-academy-id]")].map((el) => el.dataset.academyId);
  const next = nextAcademyLesson(store, ids);
  const nextCard = document.querySelector(`.path-card[data-academy-id="${next}"]`);
  const nextTitle = nextCard?.querySelector("h3")?.textContent || "SQL Grundlagen";
  const started = Boolean(store.onboarded || Object.keys(store.academy?.lessons || {}).length);
  document.getElementById("hero-back").hidden = !started;
  startHero.hidden = started;
  document.getElementById("continue-title").textContent = nextTitle;
  const astate = store.academy?.lessons?.[next];
  const doneSteps = astate ? Object.keys(astate.steps || {}).length : 0;
  const total = nextCard ? Number((nextCard.querySelector(".path-meta span")?.textContent || "").split(" ")[0]) : 0;
  document.getElementById("continue-meta").textContent = doneSteps
    ? `Schritte ${doneSteps}${total ? ` / ${total}` : ""}`
    : (nextCard?.querySelector(".path-goals")?.textContent || "");
  document.getElementById("continue-card-btn").href = `/learn/${next}`;
  document.getElementById("continue-card-btn").textContent = doneSteps ? "Weiter" : "Start";
  if (started) {
    document.getElementById("back-title").textContent = nextTitle;
    document.getElementById("back-copy").textContent = doneSteps
      ? "Dort bist du stehen geblieben. Kurze Session, direkt weiterklicken."
      : "Als Nächstes kommt das nächste Kapitel — wieder verstehen, vorhersagen, bauen.";
    const backBtn = document.getElementById("continue-btn");
    if (backBtn) {
      backBtn.href = `/learn/${next}`;
      backBtn.textContent = "Weiter";
    }
  }

  const standTitle = document.getElementById("path-stand-title");
  if (standTitle) {
    const doneChapters = ids.filter((id) => store.academy?.lessons?.[id]?.complete).length;
    standTitle.textContent = doneChapters
      ? `${doneChapters} von ${ids.length} Kapitel fertig`
      : "Noch nicht gestartet";
  }

  const recId = next;
  const recWhy = nextCard?.querySelector(".path-goals")?.textContent || "Der nächste Schritt im Lernpfad.";
  const recCard = document.querySelector(`.path-card[data-academy-id="${recId}"]`);
  document.getElementById("rec-title").textContent = recCard?.querySelector("h3")?.textContent || "Nächstes Kapitel";
  document.getElementById("rec-copy").textContent = recWhy;
  document.getElementById("rec-btn").href = `/learn/${recId}`;
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
  return String(name || "").split(".").pop().toLowerCase();
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
    if (inList) {
      const beforeCaret = editor.value.slice(inList.start, start);
      const intoFn = /\(\s*$/.test(beforeCaret.replace(/--[^\n]*$/, "").replace(/\s+$/, ""));
      if (!intoFn) {
        insertIntoSelectList(editor, inList, insertText);
        return;
      }
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

async function copyText(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    throw new Error("clipboard");
  } catch {
    const hold = document.createElement("textarea");
    hold.value = text;
    hold.setAttribute("readonly", "");
    hold.style.position = "fixed";
    hold.style.left = "-9999px";
    document.body.appendChild(hold);
    hold.select();
    document.execCommand("copy");
    hold.remove();
  }
}

function initPromptChips() {
  document.querySelectorAll(".js-prompt-chip").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = btn.getAttribute("data-prompt") || btn.textContent.trim();
      if (document.getElementById("buddy-panel")) {
        openBuddy({ ask: text });
        if (buddyIsReady()) buddySend(text);
        return;
      }
      await copyText(text);
      const label = btn.textContent;
      btn.classList.add("is-copied", "active");
      btn.textContent = "Kopiert";
      window.setTimeout(() => {
        btn.classList.remove("is-copied", "active");
        btn.textContent = label;
      }, 1200);
    });
  });
}

function currentPageKind() {
  const path = location.pathname;
  if (path.startsWith("/learn/")) return "learn";
  if (path.startsWith("/playground")) return "playground";
  if (path.startsWith("/wissen")) return "wissen";
  if (path.startsWith("/cards")) return "cards";
  return "home";
}

function buddyProgress() {
  const store = loadStore();
  const ids = [...document.querySelectorAll(".lesson-list li[data-academy-id]")].map((el) => el.dataset.academyId);
  const completed = ids.filter((id) => store.academy?.lessons?.[id]?.complete);
  return {
    completed,
    current: store.lastAcademy || null,
    chapters_done: completed.length,
    chapters_total: ids.length,
  };
}

let buddyState = {};

function pageBuddyDefaults() {
  const root = document.getElementById("academy-root");
  const hold = document.getElementById("academy-data");
  let lesson = null;
  if (hold) {
    try {
      lesson = JSON.parse(hold.textContent);
    } catch {
      lesson = null;
    }
  }
  const heading = document.querySelector(".wissen-article h1, .content h1");
  return {
    page: currentPageKind(),
    url: location.pathname,
    lesson_id: (root && root.dataset.lessonId) || (lesson && lesson.id) || "",
    lesson_title: (lesson && lesson.title) || (heading ? heading.textContent.trim() : ""),
    chapter: lesson ? lesson.chapter : undefined,
    workshop: Boolean(root && root.dataset.workshop),
    progress: buddyProgress(),
  };
}

function formatBuddyHere(state) {
  if (state.lesson_title && (state.step_title || state.step_type)) {
    const where = state.workshop ? "Playground" : `Kapitel ${state.chapter ?? ""}`.trim();
    const stepNo = Number.isFinite(Number(state.step)) ? Number(state.step) + 1 : "";
    return `${where} · ${state.lesson_title} · Schritt ${stepNo} · ${state.step_title || state.step_type}`;
  }
  if (state.page === "wissen") return `Wissensbasis · ${state.lesson_title || "Nachschlagen"}`;
  if (state.page === "cards") return "Karteikarten";
  if (state.page === "playground") {
    if (state.workshop && state.lesson_title) return `Playground · ${state.lesson_title}`;
    return "SQL-Playground · Übersicht — Claude legt hier Übungen an.";
  }
  if (state.page === "learn") return state.lesson_title || "Lernpfad";
  return "Übersicht — du kannst fragen oder eine Übung anlegen.";
}

function buddyChipSets(state) {
  const atStep = Boolean(state.lesson_title && (state.step_title || state.step_type));
  if (atStep) {
    return [
      ["Erklär mir diesen Schritt, ohne die Lösung zu verraten.", "Diesen Schritt erklären"],
      ["Meine Query passt noch nicht. Was übersehe ich?", "Meine Query verstehen"],
      ["Erklär das Konzept nochmal an der Auftragstabelle.", "Konzept nochmal"],
      ["Welche Stelle in der Wissensbasis sollte ich dazu lesen?", "Zur Wissensbasis"],
    ];
  }
  if (state.page === "wissen") {
    return [
      ["Erklär mir diesen Artikel an der Auftragstabelle.", "Artikel erklären"],
      ["Bau mir eine Playground-Übung zu diesem Thema — mit explain-Schritt und teach.", "Übung dazu anlegen"],
      ["Welche Stelle sollte ich als Nächstes lesen?", "Weiterlesen"],
    ];
  }
  if (state.page === "cards") {
    return [
      ["Welche Karten sollte ich jetzt wiederholen?", "Karten wählen"],
      ["Erklär das Konzept auf der Karte an der Auftragstabelle.", "Konzept erklären"],
    ];
  }
  const chips = [
    ["Bau mir eine Playground-Übung zu offenen Aufträgen mit WHERE — mit explain-Schritt und teach.", "Übung anlegen"],
    ["Was kann ich hier mit dir machen?", "Was kann ich hier machen?"],
  ];
  if (state.progress && state.progress.current) {
    chips.push([
      "Ich bin im Lernpfad. Lies buddy_context und erklär mir, wo ich stehe, ohne die Lösung zu verraten.",
      "Zum aktuellen Kapitel",
    ]);
  }
  return chips;
}

function renderBuddyChips() {
  const row = document.getElementById("buddy-chips");
  if (!row) return;
  const state = { ...pageBuddyDefaults(), ...buddyState };
  row.innerHTML = buddyChipSets(state).map(([ask, label]) => (
    `<button type="button" class="section-chip js-buddy-chip" data-ask="${esc(ask)}">${esc(label)}</button>`
  )).join("");
}

function syncBuddyAskPlaceholder(state) {
  const box = document.getElementById("buddy-ask");
  if (!box) return;
  if (state.lesson_title && (state.step_title || state.step_type)) {
    box.placeholder = "Was ist unklar? z. B. Warum braucht WHERE Anführungszeichen?";
  } else if (state.page === "playground" || state.page === "home") {
    box.placeholder = "Welche Übung soll Claude anlegen? Oder frag einfach.";
  } else {
    box.placeholder = "Was ist unklar?";
  }
}

const BUDDY_TOOL_LABELS = {
  buddy_context: "schaut, wo du gerade bist",
  help_with: "sucht die passende Erklärung",
  coach_sql: "sieht sich deine Query an",
  search_path: "durchsucht den Lernpfad",
  search_wissen: "blättert in der Wissensbasis",
  get_article: "liest einen Artikel",
  get_lesson: "liest ein Kapitel",
  list_lessons: "sieht sich den Lernpfad an",
  list_cards: "sieht sich die Karteikarten an",
  schema: "sieht sich die Tabellen an",
  sample_rows: "holt Beispielzeilen",
  table_rows: "holt Zeilen aus einer Tabelle",
  run_sql: "probiert SQL in der Sandbox",
  exercise_context: "bereitet eine Übung vor",
  step_schema: "prüft den Aufbau der Übung",
  draft_exercise: "entwirft eine Übung",
  load_dataset: "lädt Extra-Tabellen in die Übung",
  validate_exercise: "prüft die Übung",
  save_practice: "legt eine Übung im Playground an",
  list_workshop: "sieht sich die Playground-Übungen an",
  delete_practice: "löscht eine Übung",
};

// First turn carries the full situation; later turns ride on the resumed
// session and only mention where the learner has moved to.
function buildBuddyMessage(ask, firstTurn) {
  const state = { ...pageBuddyDefaults(), ...buddyState };
  const question = (ask || document.getElementById("buddy-ask")?.value || "").trim();
  const lines = [];
  if (firstTurn) {
    lines.push(`Wo ich bin: ${formatBuddyHere(state)}`);
    if (state.prompt) lines.push(`Aufgabe: ${state.prompt}`);
    if (state.last_sql) {
      lines.push("Meine letzte Query:");
      lines.push(state.last_sql);
    }
    if (state.last_coach) lines.push(`Letzter Hinweis der App: ${state.last_coach}`);
    lines.push("");
  } else {
    lines.push(`(Ich bin jetzt bei: ${formatBuddyHere(state)})`);
    lines.push("");
  }
  lines.push(`Frage: ${question || "Erklär mir, wo ich stehe, ohne die Lösung zu verraten."}`);
  return lines.join("\n");
}

let buddyTimer = null;
function syncBuddyContext(extra = {}) {
  buddyState = {
    ...pageBuddyDefaults(),
    ...buddyState,
    ...extra,
    url: location.pathname,
    page: currentPageKind(),
    progress: buddyProgress(),
  };
  const here = document.getElementById("buddy-here");
  if (here) here.textContent = formatBuddyHere(buddyState);
  renderBuddyChips();
  syncBuddyAskPlaceholder(buddyState);
  window.clearTimeout(buddyTimer);
  buddyTimer = window.setTimeout(() => {
    postJson("/api/buddy/context", buddyState);
  }, 280);
}

const BUDDY_OPEN_KEY = "learnsql-buddy-open";

function buddyKeepOpen(on) {
  try {
    if (on) window.sessionStorage.setItem(BUDDY_OPEN_KEY, "1");
    else window.sessionStorage.removeItem(BUDDY_OPEN_KEY);
  } catch {
    /* private mode */
  }
}

function buddyWasOpen() {
  try {
    return window.sessionStorage.getItem(BUDDY_OPEN_KEY) === "1";
  } catch {
    return false;
  }
}

function buddyIsReady() {
  return document.getElementById("buddy-panel")?.dataset.buddyState === "ready";
}

function buddySetupMsg(text) {
  const el = document.getElementById("buddy-setup-msg");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
}

function applyBuddyStatus(status) {
  if (!status) return;
  const state = status.state
    || (status.ready ? "ready" : status.available ? "not_logged_in" : "not_found");
  const panel = document.getElementById("buddy-panel");
  if (panel) panel.dataset.buddyState = state;
  const chat = document.getElementById("buddy-chat-ui");
  const missing = document.getElementById("buddy-missing");
  const setupMissing = document.getElementById("buddy-setup-missing");
  const setupLogin = document.getElementById("buddy-setup-login");
  const copy = document.getElementById("buddy-mcp-copy");
  const nav = document.getElementById("nav-buddy-status");
  if (chat) chat.hidden = state !== "ready";
  if (missing) missing.hidden = state === "ready";
  if (setupMissing) setupMissing.hidden = state !== "not_found";
  if (setupLogin) setupLogin.hidden = state !== "not_logged_in";
  if (copy) {
    if (state === "ready") {
      copy.textContent = "Claude antwortet hier direkt — über Claude Code auf diesem Rechner.";
    } else if (state === "not_logged_in") {
      copy.textContent = "Einmal bei Claude anmelden — es zählt dein normales Abo, ein API-Key ist nicht nötig.";
    } else {
      copy.textContent = "Der Buddy richtet Claude Code auf diesem Rechner ein, falls es fehlt.";
    }
  }
  if (nav) {
    nav.classList.toggle("is-on", state === "ready");
    nav.classList.toggle("is-off", state !== "ready");
    nav.textContent = state === "ready"
      ? "fragt und erklärt"
      : state === "not_logged_in"
        ? "einmal anmelden"
        : "Claude Code fehlt";
  }
  if (state === "ready") {
    stopBuddyStatusPoll();
    buddySetupMsg("");
    renderBuddyChips();
  }
}

let buddyStatusTimer = null;
function stopBuddyStatusPoll() {
  window.clearInterval(buddyStatusTimer);
  buddyStatusTimer = null;
}

async function refreshBuddyStatus() {
  const res = await fetch("/api/buddy/status?refresh=1");
  const data = await res.json();
  applyBuddyStatus(data);
  return data;
}

function startBuddyStatusPoll() {
  stopBuddyStatusPoll();
  buddyStatusTimer = window.setInterval(() => {
    refreshBuddyStatus().catch(() => {});
  }, 2000);
}

function initBuddySetup() {
  document.getElementById("buddy-install")?.addEventListener("click", async () => {
    const btn = document.getElementById("buddy-install");
    if (btn) btn.disabled = true;
    buddySetupMsg("Claude Code wird eingerichtet…");
    try {
      const res = await fetch("/api/buddy/install", { method: "POST" });
      const data = await res.json();
      applyBuddyStatus(data.status || data);
      if (data.ok && (data.status?.available || data.available)) {
        buddySetupMsg("CLI ist da. Als Nächstes einmal anmelden.");
      } else {
        buddySetupMsg(data.error || "Einrichten hat nicht geklappt. Später nochmal versuchen.");
      }
    } catch {
      buddySetupMsg("Einrichten hat nicht geklappt.");
    } finally {
      if (btn) btn.disabled = false;
    }
  });
  document.getElementById("buddy-login")?.addEventListener("click", async () => {
    const btn = document.getElementById("buddy-login");
    if (btn) btn.disabled = true;
    buddySetupMsg("Schwarzes Fenster und Browser sollten aufgehen. Einen Code ins Fenster einfügen, nicht hier.");
    try {
      const res = await fetch("/api/buddy/login", { method: "POST" });
      const data = await res.json();
      if (!data.ok) {
        buddySetupMsg(data.error || "Anmelden hat nicht geklappt.");
      } else {
        startBuddyStatusPoll();
      }
    } catch {
      buddySetupMsg("Anmelden hat nicht geklappt.");
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}

function openBuddy(opts = {}) {
  const panel = document.getElementById("buddy-panel");
  const fab = document.getElementById("buddy-fab");
  if (!panel) return;
  if (opts.ask) {
    const box = document.getElementById("buddy-ask");
    if (box) box.value = opts.ask;
  }
  panel.hidden = false;
  document.body.classList.add("buddy-open");
  fab?.setAttribute("aria-expanded", "true");
  buddyKeepOpen(true);
  if (!opts.quiet) {
    if (buddyIsReady()) document.getElementById("buddy-ask")?.focus();
    else if (document.getElementById("buddy-panel")?.dataset.buddyState === "not_logged_in") {
      document.getElementById("buddy-login")?.focus();
    } else {
      document.getElementById("buddy-install")?.focus();
    }
  }
  syncBuddyContext({ question: document.getElementById("buddy-ask")?.value || "" });
}

function closeBuddy() {
  const panel = document.getElementById("buddy-panel");
  const fab = document.getElementById("buddy-fab");
  if (!panel) return;
  panel.hidden = true;
  document.body.classList.remove("buddy-open");
  fab?.setAttribute("aria-expanded", "false");
  buddyKeepOpen(false);
}

// --- buddy chat over SSE ----------------------------------------------------
// The app runs the local `claude` CLI; these helpers drive one turn of it.

let buddyCtrl = null;
let buddyLog = [];
let buddyTurns = 0;

function buddyChatId() {
  let id = "";
  try {
    id = window.localStorage.getItem("learnsql-buddy-chat") || "";
  } catch {
    id = "";
  }
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(id)) {
    id = "c" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    try {
      window.localStorage.setItem("learnsql-buddy-chat", id);
    } catch {
      /* private mode — a per-tab id is fine */
    }
  }
  return id;
}

function buddyMarkdown(text) {
  if (!window.marked) return null;
  try {
    // marked does not sanitize and we assign to innerHTML, so drop raw HTML.
    const renderer = new window.marked.Renderer();
    renderer.html = () => "";
    return window.marked.parse(text, { mangle: false, headerIds: false, renderer });
  } catch {
    return null;
  }
}

function buddyScroll() {
  const box = document.getElementById("buddy-chat");
  if (box) box.scrollTop = box.scrollHeight;
}

function buddyBubble(role, text) {
  const box = document.getElementById("buddy-chat");
  if (!box) return null;
  const el = document.createElement("div");
  el.className = "buddy-msg buddy-msg-" + role;
  el.textContent = text;
  box.appendChild(el);
  buddyScroll();
  return el;
}

function buddyRender(el, text) {
  const html = buddyMarkdown(text);
  if (html === null) {
    el.textContent = text;
    return;
  }
  el.innerHTML = html;
  // Same treatment lesson bodies get (see renderSections).
  el.querySelectorAll("pre code").forEach((code) => {
    code.innerHTML = colorizeSql(code.textContent);
  });
}

function buddyNote(kind, text) {
  const box = document.getElementById("buddy-chat");
  if (!box) return;
  const el = document.createElement("p");
  el.className = "buddy-note buddy-note-" + kind;
  el.textContent = text;
  box.appendChild(el);
  buddyScroll();
}

function buddyPracticeCard(data) {
  const box = document.getElementById("buddy-chat");
  if (!box) return;
  const el = document.createElement("div");
  el.className = "buddy-practice";
  const title = data.title || data.id || "Übung";
  if (data.action === "delete") {
    const n = (data.ids && data.ids.length) || (data.id ? 1 : 0);
    el.innerHTML = `<p class="buddy-practice-kicker">Playground</p>
      <p>${n === 1 ? "Übung gelöscht." : `${n} Übungen gelöscht.`}</p>`;
  } else {
    const url = data.url || `/playground/${data.id || ""}`;
    el.innerHTML = `<p class="buddy-practice-kicker">Neue Übung</p>
      <p class="buddy-practice-title">${esc(title)}</p>
      <a class="btn btn-primary" href="${esc(url)}">Öffnen</a>`;
  }
  box.appendChild(el);
  buddyScroll();
}

function maybeLeaveDeletedPractice(data) {
  if (!data || data.action !== "delete") return;
  const ids = data.ids || (data.id ? [data.id] : []);
  const here = location.pathname.replace(/\/$/, "");
  if (ids.some((id) => here === `/playground/${id}`)) {
    buddyKeepOpen(true);
    window.location.href = "/playground";
  }
}

function buddyActivity(text) {
  const el = document.getElementById("buddy-activity");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
}

function buddyError(text) {
  const el = document.getElementById("buddy-error");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
}

function buddyBusy(busy) {
  const send = document.getElementById("buddy-send");
  const stop = document.getElementById("buddy-stop");
  const chat = document.getElementById("buddy-chat");
  if (send) send.disabled = busy;
  if (stop) stop.hidden = !busy;
  if (chat) chat.setAttribute("aria-busy", busy ? "true" : "false");
  if (!busy) buddyActivity("");
}

function buddyPersist() {
  try {
    window.sessionStorage.setItem(
      "learnsql-buddy-log",
      JSON.stringify(buddyLog.slice(-40)),
    );
  } catch {
    /* nothing worth failing a chat over */
  }
}

function buddyRestore() {
  let raw = "";
  try {
    raw = window.sessionStorage.getItem("learnsql-buddy-log") || "";
  } catch {
    raw = "";
  }
  if (!raw) return;
  try {
    buddyLog = JSON.parse(raw) || [];
  } catch {
    buddyLog = [];
    return;
  }
  buddyTurns = buddyLog.filter((m) => m.role === "user").length;
  buddyLog.forEach((msg) => {
    if (msg.role === "practice") {
      buddyPracticeCard(msg);
      return;
    }
    const el = buddyBubble(msg.role === "user" ? "user" : "claude", "");
    if (!el) return;
    if (msg.role === "user") el.textContent = msg.text;
    else buddyRender(el, msg.text);
  });
}

function buddyReset() {
  buddyStop();
  buddyLog = [];
  buddyTurns = 0;
  const box = document.getElementById("buddy-chat");
  if (box) box.innerHTML = "";
  buddyError("");
  try {
    window.sessionStorage.removeItem("learnsql-buddy-log");
  } catch {
    /* ignore */
  }
  postJson("/api/buddy/reset", { chat_id: buddyChatId() });
}

function buddyStop() {
  if (buddyCtrl) {
    buddyCtrl.abort();
    buddyCtrl = null;
  }
  buddyBusy(false);
}

function buddyHandle(block, ctx) {
  if (!block || block.startsWith(":")) return;
  let name = "";
  let raw = "";
  block.split("\n").forEach((line) => {
    if (line.startsWith("event:")) name = line.slice(6).trim();
    else if (line.startsWith("data:")) raw += line.slice(5).trim();
  });
  if (!name) return;
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    return;
  }

  if (name === "start") {
    buddyActivity("Claude startet …");
  } else if (name === "init") {
    buddyActivity("Claude denkt nach …");
    if (data.mcp_ok === false) {
      buddyNote("warn", "Claude sieht deinen Lernstand gerade nicht (learnsql nicht verbunden).");
    }
  } else if (name === "tool") {
    const label = BUDDY_TOOL_LABELS[data.name] || "benutzt " + data.name;
    buddyActivity("Claude " + label + " …");
    ctx.tools.add(data.name);
  } else if (name === "delta") {
    ctx.text += data.text || "";
    if (!ctx.bubble) ctx.bubble = buddyBubble("claude", "");
    if (ctx.bubble && !ctx.pending) {
      // One render per frame — re-parsing markdown per token is what makes
      // streaming UIs stutter.
      ctx.pending = true;
      window.requestAnimationFrame(() => {
        ctx.pending = false;
        buddyRender(ctx.bubble, ctx.text);
        buddyScroll();
      });
    }
  } else if (name === "notice") {
    buddyNote(data.kind || "info", data.text || "");
  } else if (name === "practice") {
    ctx.practices = (ctx.practices || 0) + 1;
    buddyPracticeCard(data);
    buddyLog.push({
      role: "practice",
      action: data.action,
      id: data.id,
      ids: data.ids,
      title: data.title,
      url: data.url,
    });
    buddyPersist();
    refreshPlaygroundCatalog();
    maybeLeaveDeletedPractice(data);
  } else if (name === "done") {
    ctx.done = true;
    const text = data.text || ctx.text;
    if (!ctx.bubble) ctx.bubble = buddyBubble("claude", "");
    if (ctx.bubble) buddyRender(ctx.bubble, text);
    buddyLog.push({ role: "claude", text });
    buddyPersist();
    if (!ctx.practices && (ctx.tools.has("save_practice") || ctx.tools.has("delete_practice"))) {
      refreshPlaygroundCatalog();
    }
  } else if (name === "error") {
    ctx.done = true;
    buddyError(data.text || "Etwas ist schiefgelaufen.");
  }
}

async function buddySend(ask) {
  if (!buddyIsReady()) {
    openBuddy({ ask: ask || "" });
    return;
  }
  if (buddyCtrl) return;
  const box = document.getElementById("buddy-ask");
  const question = (ask || box?.value || "").trim();
  if (!question) return;

  buddyError("");
  buddyBubble("user", question);
  buddyLog.push({ role: "user", text: question });
  buddyPersist();
  if (box) box.value = "";

  const firstTurn = buddyTurns === 0;
  buddyTurns += 1;
  const message = buildBuddyMessage(question, firstTurn);
  syncBuddyContext({ question });

  buddyCtrl = new AbortController();
  buddyBusy(true);
  const ctx = { text: "", bubble: null, tools: new Set(), done: false, pending: false, practices: 0 };

  try {
    const res = await fetch("/api/buddy/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: message,
        chat_id: buddyChatId(),
        context: { ...pageBuddyDefaults(), ...buddyState, question },
      }),
      signal: buddyCtrl.signal,
    });
    if (!res.ok) {
      let payload = {};
      try {
        payload = await res.json();
      } catch {
        payload = {};
      }
      buddyError(payload.error || `Fehler ${res.status}.`);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let cut;
      while ((cut = buffer.indexOf("\n\n")) >= 0) {
        buddyHandle(buffer.slice(0, cut), ctx);
        buffer = buffer.slice(cut + 2);
      }
    }
    if (!ctx.done) buddyError("Abgebrochen — die Antwort kam nicht zu Ende.");
  } catch (err) {
    if (err && err.name === "AbortError") buddyNote("info", "Abgebrochen.");
    else buddyError("Claude ist nicht erreichbar.");
  } finally {
    buddyCtrl = null;
    buddyBusy(false);
  }
}

function initBuddy() {
  document.getElementById("buddy-close")?.addEventListener("click", closeBuddy);
  document.addEventListener("click", (e) => {
    const open = e.target.closest(".js-buddy-open");
    if (!open) return;
    e.preventDefault();
    openBuddy({ ask: open.getAttribute("data-ask") || "" });
  });
  document.getElementById("buddy-chips")?.addEventListener("click", (e) => {
    const chip = e.target.closest(".js-buddy-chip");
    if (!chip) return;
    const ask = chip.getAttribute("data-ask") || "";
    const box = document.getElementById("buddy-ask");
    if (box) box.value = ask;
    buddySend(ask);
  });
  document.getElementById("buddy-send")?.addEventListener("click", () => buddySend());
  document.getElementById("buddy-stop")?.addEventListener("click", buddyStop);
  document.getElementById("buddy-reset")?.addEventListener("click", buddyReset);
  document.getElementById("buddy-ask")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      buddySend();
    }
  });
  document.getElementById("buddy-chat")?.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a) return;
    const href = a.getAttribute("href") || "";
    let path = href;
    try {
      if (/^https?:/i.test(href)) {
        const u = new URL(href, location.origin);
        if (u.origin !== location.origin) return;
        path = u.pathname;
      }
    } catch {
      return;
    }
    if (path.startsWith("/playground") || path.startsWith("/learn/")) {
      buddyKeepOpen(true);
    }
  });
  window.addEventListener("beforeunload", () => {
    if (buddyCtrl) buddyCtrl.abort();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && document.body.classList.contains("buddy-open")) closeBuddy();
  });
  buddyRestore();
  initBuddySetup();
  if (buddyWasOpen()) openBuddy({ quiet: true });
  else syncBuddyContext();
}

function initMcpConnect() {
  const btn = document.getElementById("mcp-connect-btn");
  if (!btn) return;
  const msg = document.getElementById("mcp-connect-msg");
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    if (msg) {
      msg.hidden = true;
      msg.textContent = "";
    }
    try {
      const res = await fetch("/api/mcp/connect", { method: "POST" });
      const data = await res.json();
      if (data.ok && data.status && data.status.installed) {
        window.location.href = "/playground?verbunden=1";
        return;
      }
      if (msg) {
        msg.hidden = false;
        msg.textContent = data.error || "Verbinden fehlgeschlagen.";
      }
    } catch {
      if (msg) {
        msg.hidden = false;
        msg.textContent = "Verbinden fehlgeschlagen.";
      }
    } finally {
      btn.disabled = false;
    }
  });
}

function initResetDb() {
  const run = async (btn) => {
    const ok = window.confirm(
      "Lern-Datenbank auf den Ausgangszustand zurücksetzen?\nDeine bisherigen UPDATE/DELETE-Übungen gehen verloren."
    );
    if (!ok) return;
    if (btn) btn.disabled = true;
    try {
      const root = document.getElementById("academy-root");
      const lessonId = root && root.dataset.lessonId;
      const res = await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lessonId ? { lesson_id: lessonId } : {}),
      });
      const data = await res.json();
      window.alert(data.ok ? data.message : `Zurücksetzen fehlgeschlagen: ${data.error}`);
    } catch {
      window.alert("Zurücksetzen fehlgeschlagen.");
    } finally {
      if (btn) btn.disabled = false;
    }
  };
  document.querySelectorAll("#reset-db, #reset-db-pg, .js-reset-db").forEach((btn) => {
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
            ? '<p class="verdict verdict-ok">Richtig. Die Abfrage gibt die erwarteten Daten zurück.</p>'
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

function playgroundEls() {
  return {
    grid: document.querySelector(".path-playground"),
    countEl: document.getElementById("playground-count"),
    mainEl: document.getElementById("playground-main"),
    promptsEl: document.getElementById("playground-prompts"),
    emptyEl: document.getElementById("playground-empty"),
  };
}

function playgroundCardHtml(p) {
  const id = p.id || "";
  const title = p.title || id;
  const concept = p.concept ? `<span>${esc(p.concept)}</span>` : "";
  const steps = Number(p.step_count) || 0;
  const minutes = p.minutes || 8;
  return `<article class="path-card playground-card" data-practice-id="${esc(id)}">
    <a class="path-card-body" href="/playground/${esc(id)}">
      <div class="path-top">
        <span class="path-letter">P</span>
        <span class="path-mins">${esc(minutes)} Min</span>
      </div>
      <h3>${esc(title)}</h3>
      <p class="path-goals">${esc(p.goal || "")}</p>
      <div class="path-meta">
        <span>${steps} Schritte</span>
        ${concept}
      </div>
    </a>
    <button class="path-card-delete" type="button" data-id="${esc(id)}" data-title="${esc(title)}">Löschen</button>
  </article>`;
}

function setPlaygroundEmpty(hasCards) {
  const { grid, countEl, mainEl, promptsEl, emptyEl } = playgroundEls();
  const left = hasCards && grid ? grid.querySelectorAll(".playground-card").length : 0;
  if (countEl) {
    countEl.textContent = left === 1
      ? "1 Übung · wie ein normales Kapitel lösen"
      : `${left} Übungen · wie ein normales Kapitel lösen`;
  }
  if (mainEl) mainEl.hidden = left === 0;
  if (promptsEl) promptsEl.hidden = left === 0;
  if (emptyEl) emptyEl.hidden = left > 0;
}

function renderPlaygroundCatalog(practices) {
  const { grid } = playgroundEls();
  if (!grid) return;
  const list = practices || [];
  grid.innerHTML = list.map(playgroundCardHtml).join("");
  setPlaygroundEmpty(list.length > 0);
}

async function refreshPlaygroundCatalog() {
  if (!document.getElementById("playground-main") && !document.getElementById("playground-empty")) return;
  try {
    const res = await fetch("/api/playground");
    const data = await res.json();
    if (!data.ok) return;
    renderPlaygroundCatalog(data.practices || []);
  } catch {
    /* listing can wait for the next visit */
  }
}

function initPlaygroundDelete() {
  const { grid } = playgroundEls();
  if (!grid) return;

  grid.addEventListener("click", async (e) => {
    const btn = e.target.closest(".path-card-delete");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const id = btn.dataset.id;
    const title = btn.dataset.title || id;
    if (!id || !window.confirm(`Übung „${title}“ löschen?`)) return;
    btn.disabled = true;
    try {
      const res = await fetch(`/api/playground/${encodeURIComponent(id)}/delete`, { method: "POST" });
      const data = await res.json();
      if (!data.ok) {
        window.alert(data.error || "Löschen fehlgeschlagen.");
        return;
      }
      btn.closest(".playground-card")?.remove();
      setPlaygroundEmpty(grid.querySelectorAll(".playground-card").length > 0);
    } catch {
      window.alert("Löschen fehlgeschlagen.");
    } finally {
      btn.disabled = false;
    }
  });

  window.addEventListener("focus", () => {
    const path = location.pathname.replace(/\/$/, "") || "/";
    if (path === "/playground") refreshPlaygroundCatalog();
  });
}

const CARD_STORE = "learnsql-cards-v1";
const CARD_BOX_MS = { 1: 0, 2: 24 * 60 * 60 * 1000, 3: 4 * 24 * 60 * 60 * 1000 };

function loadCardState() {
  try {
    return JSON.parse(localStorage.getItem(CARD_STORE) || "{}") || {};
  } catch {
    return {};
  }
}

function saveCardState(state) {
  localStorage.setItem(CARD_STORE, JSON.stringify(state));
}

function cardMeta(state, id) {
  const row = state[id] || {};
  return { box: Number(row.box) || 1, due: Number(row.due) || 0 };
}

function initCards() {
  const cardEl = document.getElementById("flashcard");
  if (!cardEl) return;
  const frontEl = document.getElementById("card-front");
  const backEl = document.getElementById("card-back");
  const sqlEl = document.getElementById("card-sql");
  const kickerEl = document.getElementById("card-kicker");
  const progressEl = document.getElementById("card-progress");
  const boxEl = document.getElementById("card-box-meta");
  const filterEl = document.getElementById("card-filter");
  const topicEl = document.getElementById("card-topic");
  const dueEl = document.getElementById("card-due");
  let all = [];
  let deck = [];
  let i = 0;
  const state = loadCardState();
  const params = new URLSearchParams(window.location.search);
  if (topicEl && params.get("topic")) topicEl.value = params.get("topic");

  const current = () => (deck.length ? deck[i % deck.length] : null);

  const show = () => {
    cardEl.classList.remove("flipped");
    if (sqlEl) {
      sqlEl.hidden = true;
      sqlEl.textContent = "";
    }
    if (!deck.length) {
      frontEl.textContent = "Keine Karten in diesem Filter.";
      backEl.textContent = "";
      progressEl.textContent = "0 / 0";
      if (boxEl) boxEl.textContent = dueEl?.checked
        ? "Nichts Fälliges — Filter lösen oder später wiederkommen."
        : "";
      return;
    }
    const card = current();
    const meta = cardMeta(state, card.id);
    kickerEl.textContent = [card.topic_label || card.lesson, card.kind].filter(Boolean).join(" · ");
    frontEl.textContent = card.front;
    backEl.textContent = card.back;
    if (sqlEl && card.sql) {
      sqlEl.hidden = false;
      sqlEl.textContent = card.sql;
    }
    progressEl.textContent = `${(i % deck.length) + 1} / ${deck.length}`;
    if (boxEl) boxEl.textContent = `Fach ${meta.box} von 3`;
  };

  const rebuild = () => {
    const lesson = filterEl?.value || "";
    const topic = topicEl?.value || "";
    const onlyDue = Boolean(dueEl?.checked);
    const now = Date.now();
    deck = all.filter((c) => {
      if (lesson && c.lesson_id !== lesson) return false;
      if (topic === "quiz" && c.source !== "quiz") return false;
      if (topic && topic !== "quiz" && c.topic !== topic) return false;
      if (onlyDue) {
        const meta = cardMeta(state, c.id);
        if (meta.due && meta.due > now) return false;
      }
      return true;
    });
    i = 0;
    show();
  };

  const rate = (action) => {
    const card = current();
    if (!card) return;
    const prev = cardMeta(state, card.id);
    let box = prev.box;
    if (action === "again") box = 1;
    else if (action === "hard") box = 1;
    else box = Math.min(3, box + 1);
    const wait = CARD_BOX_MS[box] || 0;
    state[card.id] = { box, due: Date.now() + wait };
    saveCardState(state);
    deck.splice(i % deck.length, 1);
    if (action !== "got" && wait === 0) deck.push(card);
    if (i >= deck.length) i = 0;
    show();
  };

  fetch("/api/cards")
    .then((r) => r.json())
    .then((data) => {
      all = data.cards || [];
      rebuild();
    });

  cardEl.addEventListener("click", (e) => {
    if (e.target.closest("pre")) return;
    cardEl.classList.toggle("flipped");
  });
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement === cardEl) {
      e.preventDefault();
      cardEl.classList.toggle("flipped");
    }
  });
  document.getElementById("card-again")?.addEventListener("click", () => rate("again"));
  document.getElementById("card-hard")?.addEventListener("click", () => rate("hard"));
  document.getElementById("card-got-it")?.addEventListener("click", () => rate("got"));
  filterEl?.addEventListener("change", rebuild);
  topicEl?.addEventListener("change", rebuild);
  dueEl?.addEventListener("change", rebuild);
}

function initWissen() {
  const input = document.getElementById("wissen-q");
  const resultsEl = document.getElementById("wissen-results");
  const meta = document.getElementById("wissen-meta");
  if (!input || !resultsEl) return;

  const typeLabel = {
    lektion: "Kapitel",
    schritt: "Schritt",
    karte: "Karte",
    check: "Kurzcheck",
    konzept: "Konzept",
    artikel: "Artikel",
  };

  const render = (data, query) => {
    if (!query || query.length < 2) {
      resultsEl.innerHTML = "";
      if (meta) meta.textContent = "Mindestens zwei Zeichen — Artikel zuerst, dann Kapitel.";
      return;
    }
    const rows = data.results || [];
    if (meta) {
      meta.textContent = rows.length
        ? `${rows.length} Treffer — Artikel und Kapitel`
        : "Kein Treffer — anderen Begriff versuchen (SELECT, JOIN, NULL, Transaktion).";
    }
    resultsEl.innerHTML = rows
      .map(
        (r) => `
      <a class="wissen-hit" href="${r.url}">
        <span class="wissen-kicker">${esc(r.letter)} · ${esc(typeLabel[r.type] || r.type)}</span>
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
initPlaygroundDelete();
initCards();
initWissen();
initResetDb();
initMcpConnect();
initPromptChips();
initBuddy();
initDashboard();
refreshChrome();

window.LearnUI = {
  esc,
  colorizeSql,
  renderTable,
  renderSqlResult,
  postJson,
  loadStore,
  saveStore,
  academyState,
  refreshChrome,
  syncBuddyContext,
  openBuddy,
};

