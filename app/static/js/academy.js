const PHASE = {
  look: "Anschauen",
  inspect: "Daten",
  explain: "Verstehen",
  demo: "Ausführen",
  predict: "Vorhersagen",
  "predict-cols": "Vorhersagen",
  build: "Bauen",
  fill: "Ergänzen",
  write: "Schreiben",
  apply: "Anwenden",
  challenge: "Challenge",
  mcq: "Check",
};

const RESULT_OK = "Die Abfrage gibt die erwarteten Daten zurück.";

const MODEL = [
  { key: "SELECT", q: "Was möchte ich sehen?" },
  { key: "FROM", q: "Woher kommen die Daten?" },
  { key: "WHERE", q: "Welche Datensätze?" },
  { key: "JOIN", q: "Welche Infos extra?" },
  { key: "ON", q: "Wie gehören sie zusammen?" },
  { key: "GROUP BY", q: "Nach was zusammenfassen?" },
  { key: "HAVING", q: "Welche Gruppen?" },
  { key: "ORDER BY", q: "Wie sortieren?" },
  { key: "LIMIT", q: "Wie viele Zeilen?" },
  { key: "INSERT", q: "Welche neue Zeile?" },
  { key: "UPDATE", q: "Was soll sich ändern?" },
];

function ui() {
  return window.LearnUI || {};
}

function rich(text) {
  return ui().esc(text || "")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

function rowId(row, field) {
  const key = field || "id";
  return String(row[key]);
}

function renderDataTable(table, opts = {}) {
  const esc = ui().esc;
  const cols = table.columns || [];
  const idField = opts.idField || "id";
  const selected = opts.selectedIds || new Set();
  const selectedCols = opts.selectedCols || new Set();
  const dimmed = opts.dimmedIds || new Set();
  const keep = opts.keepColumns ? new Set(opts.keepColumns) : null;
  let html = `<div class="table-wrap"><table class="data-table result-table" data-id-field="${esc(idField)}"><thead><tr>`;
  cols.forEach((c) => {
    const on = selectedCols.has(c) || selectedCols.has(c.toLowerCase());
    const fade = keep && !keep.has(c);
    html += `<th class="${opts.clickColumns ? "is-click" : ""} ${on ? "is-on" : ""} ${fade ? "is-fade" : ""}" data-col="${esc(c)}">${esc(c)}</th>`;
  });
  html += "</tr></thead><tbody>";
  (table.rows || []).forEach((row) => {
    const id = rowId(row, idField);
    const on = selected.has(id);
    const dim = dimmed.has(id);
    html += `<tr class="${opts.clickRows ? "is-click" : ""} ${on ? "is-on" : ""} ${dim ? "is-out" : ""}" data-row-id="${esc(id)}">`;
    cols.forEach((c) => {
      const v = row[c];
      const fade = keep && !keep.has(c);
      html += `<td class="${opts.clickCells ? "is-click" : ""} ${fade ? "is-fade" : ""}" data-col="${esc(c)}" data-value="${esc(v)}">${v === null || v === undefined ? "<em>NULL</em>" : esc(v)}</td>`;
    });
    html += "</tr>";
  });
  html += "</tbody></table></div>";
  if (table.label || table.name) {
    html = `<p class="table-kicker">${esc(table.label || table.name)}</p>` + html;
  }
  return html;
}

function stepTables(s) {
  if (Array.isArray(s.tables) && s.tables.length) return s.tables;
  return s.table ? [s.table] : [];
}

function joinDimmed(table, s) {
  const dimmed = new Set();
  if (s.visualize === "where" && s.match_column) {
    (table.rows || []).forEach((row) => {
      if (!sameValue(row[s.match_column], s.match_value)) dimmed.add(rowId(row, s.id_field));
    });
    return dimmed;
  }
  if (s.visualize === "inner" && table.name === "orders") {
    (table.rows || []).forEach((row) => {
      if (row.client_id == null || row.client == null) dimmed.add(rowId(row, s.id_field || "id"));
    });
  }
  return dimmed;
}

function renderStepTables(s, opts = {}) {
  const tables = stepTables(s);
  if (!tables.length) return "";
  const html = tables.map((t) => {
    const dimmed = opts.dimmedIds || joinDimmed(t, s);
    return renderDataTable(t, { ...opts, dimmedIds: dimmed, idField: s.id_field || "id" });
  }).join("");
  if (tables.length > 1) return `<div class="split-tables">${html}</div>`;
  return html;
}

function sameValue(a, b) {
  return String(a) === String(b);
}

function initAcademy() {
  const root = document.getElementById("academy-root");
  const hold = document.getElementById("academy-data");
  if (!root || !hold) return;

  const lesson = JSON.parse(hold.textContent);
  const steps = lesson.steps || [];
  const store = ui().loadStore();
  store.onboarded = true;
  store.lastAcademy = lesson.id;
  const st = ui().academyState(store, lesson.id);
  saveQuiet(store);

  let index = 0;
  const firstOpen = steps.findIndex((_, i) => !st.steps[i]);
  index = firstOpen >= 0 ? firstOpen : Math.max(0, steps.length - 1);

  const local = {
    selectedIds: new Set(),
    selectedCols: new Set(),
    built: [],
    explainOpen: new Set(),
    hintLevel: 0,
    numberValue: "",
    fillValues: [],
    sqlDraft: "",
    lastRowId: "",
  };

  function saveQuiet(s) {
    ui().saveStore(s);
    ui().refreshChrome();
  }

  function quizCount() {
    return Number(root.dataset.quizCount || 0);
  }

  function quizFinished(a) {
    const n = quizCount();
    if (!n) return true;
    return Object.keys(a.quiz || {}).length >= n;
  }

  function markComplete(a) {
    a.complete = steps.every((_, i) => a.steps[i]) && quizFinished(a);
  }

  function switchAcademyTab(name) {
    document.querySelectorAll(".academy .tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.tab === name);
    });
    document.querySelectorAll(".academy .tab-panel").forEach((p) => {
      p.classList.toggle("active", p.dataset.panel === name);
    });
    const hint = document.getElementById("phase-hint");
    if (hint) {
      hint.textContent = name === "quiz"
        ? "Eine Antwort tippen — danach kommt die Erklärung. Falsch ist ok."
        : "Kurze Schritte: anschauen, vorhersagen, selbst schreiben.";
    }
  }

  function markStepDone() {
    const s = ui().loadStore();
    const a = ui().academyState(s, lesson.id);
    if (!a.quiz) a.quiz = {};
    a.steps[index] = true;
    a.current = Math.min(index + 1, steps.length);
    markComplete(a);
    s.lastAcademy = lesson.id;
    saveQuiet(s);
  }

  function step() {
    return steps[index];
  }

  function resetLocal(keepDraft) {
    local.selectedIds = new Set();
    local.selectedCols = new Set();
    local.built = [];
    local.explainOpen = new Set();
    local.hintLevel = 0;
    local.numberValue = "";
    local.fillValues = [];
    local.pool = null;
    local.lastRowId = "";
    if (!keepDraft) local.sqlDraft = step().starter || "";
  }

  function renderMeter() {
    const meter = document.getElementById("step-meter");
    const s = ui().loadStore();
    const a = ui().academyState(s, lesson.id);
    meter.innerHTML = steps
      .map((st, i) => {
        const done = Boolean(a.steps[i]);
        const current = i === index;
        return `<button type="button" class="ex-dot${current ? " current" : ""}${done ? " done" : ""}" data-go="${i}">${i + 1}. ${PHASE[st.type] || st.type}</button>`;
      })
      .join("");
  }

  function renderModel() {
    const rail = document.getElementById("model-rail");
    const active = new Set(lesson.model || []);
    const stepTokens = new Set((step().concepts || []).concat(step().parts?.map((p) => p.token) || []));
    rail.innerHTML = `<p class="nav-label">SQL als Fragen</p>` + MODEL.map((m) => {
      const on = active.has(m.key) || stepTokens.has(m.key);
      return `<div class="model-row${on ? " is-on" : ""}"><strong>${ui().esc(m.key)}</strong><span>${ui().esc(m.q)}</span></div>`;
    }).join("");
  }

  function sqlBlock(sql) {
    return `<pre class="sql-pre">${ui().colorizeSql(sql || "")}</pre>`;
  }

  function hintBox() {
    const hints = step().hints || [];
    if (!hints.length) return "";
    const shown = hints.slice(0, local.hintLevel);
    if (!shown.length) return "";
    return `<div class="hint-box"><strong>Hinweis ${Math.min(local.hintLevel, hints.length)} / ${hints.length}</strong><p>${rich(shown[shown.length - 1])}</p></div>`;
  }

  function footerHtml(extra = {}) {
    const hints = step().hints || [];
    const buttons = [];
    if (hints.length) {
      const label = local.hintLevel >= hints.length ? "Hinweise" : "Hinweis";
      buttons.push(`<button class="btn ghost" type="button" data-act="hint">${label}</button>`);
    }
    if (extra.check) buttons.push(`<button class="btn btn-check" type="button" data-act="check">${extra.check}</button>`);
    if (extra.run) buttons.push(`<button class="btn btn-primary" type="button" data-act="run">${extra.run}</button>`);
    if (extra.next) buttons.push(`<button class="btn btn-primary" type="button" data-act="next">${extra.next}</button>`);
    return `<div class="exercise-actions academy-actions">${buttons.join("")}</div>${hintBox()}<div id="step-feedback"></div>`;
  }

  function showFeedback(html) {
    const el = document.getElementById("step-feedback");
    if (el) el.innerHTML = html;
  }

  function failCard(body, extra = "") {
    return `<div class="fail-card"><p class="verdict verdict-fail">Noch nicht</p><p>${rich(body)}</p>${extra}</div>`;
  }

  function successCard(note) {
    const next = index < steps.length - 1;
    const nextLesson = root.dataset.nextId;
    let advance = "";
    if (next) {
      advance = `<button class="btn btn-primary" type="button" data-act="next">Weiter</button>`;
    } else if (quizCount()) {
      advance = `<button class="btn btn-primary" type="button" data-act="goto-quiz">Weiter zum Kurzcheck</button>`;
    } else if (nextLesson) {
      advance = `<a class="btn btn-primary" href="/learn/${nextLesson}">Nächstes Kapitel</a>`;
    } else {
      advance = `<a class="btn btn-primary" href="/">Zur Übersicht</a>`;
    }
    const why = note
      || step().feedback_ok
      || RESULT_OK;
    return `<div class="success-card">
      <p class="verdict verdict-ok">Richtig</p>
      <p>${rich(why)}</p>
      ${advance}
    </div>`;
  }

  function completeInteractive(note) {
    markStepDone();
    showFeedback(successCard(note));
    renderMeter();
  }

  function inspectCorrect(s) {
    if (s.interaction === "click_column") {
      return local.selectedCols.has(s.answer);
    }
    if (s.interaction === "click_row") {
      return local.selectedIds.has(String(s.answer));
    }
    if (s.interaction === "click_cell") {
      return local.selectedCols.has(`${s.answer.column}::${s.answer.value}`);
    }
    if (s.interaction === "number") {
      return Number(local.numberValue) === Number(s.answer);
    }
    return false;
  }

  function assembledSql() {
    const s = step();
    if (s.type === "build") return local.built.join(" ");
    if (s.type === "fill") {
      const parts = (s.template || "").split("___");
      let out = parts[0] || "";
      for (let i = 1; i < parts.length; i += 1) {
        out += (local.fillValues[i - 1] || "").trim();
        out += parts[i] || "";
      }
      return out;
    }
    return local.sqlDraft;
  }

  function renderStep() {
    const s = step();
    const host = document.getElementById("step-root");
    const foot = document.getElementById("step-footer");
    renderMeter();
    renderModel();
    document.querySelector(".content")?.classList.add("content-wide");

    const title = `<p class="exercise-num">Schritt ${index + 1} / ${steps.length} · ${PHASE[s.type] || ""}</p>
      <h2 class="step-title">${rich(s.title || "")}</h2>
      ${s.text ? `<p class="step-text">${rich(s.text)}</p>` : ""}
      ${s.prompt ? `<p class="exercise-prompt">${rich(s.prompt)}</p>` : ""}
      ${s.question ? `<p class="quiz-q">${rich(s.question)}</p>` : ""}`;

    if (s.type === "look") {
      host.innerHTML = title + renderStepTables(s) + (s.note ? `<p class="coach">${rich(s.note)}</p>` : "");
      foot.innerHTML = footerHtml({ next: s.cta || "Weiter" });
      return;
    }

    if (s.type === "explain") {
      const parts = (s.parts || []).map((p, i) => {
        const open = local.explainOpen.has(i);
        return `<button type="button" class="sql-part${open ? " is-open" : ""}" data-part="${i}">
          <span class="sql-part-k">${ui().esc(p.token || "SQL")}</span>
          <code>${ui().esc(p.match)}</code>
          ${open ? `<span class="sql-part-a"><strong>${ui().esc(p.question)}</strong> ${rich(p.answer)}</span>` : `<span class="muted">Tippen zum Erklären</span>`}
        </button>`;
      }).join("");
      host.innerHTML = title + sqlBlock(s.sql) + `<div class="sql-parts">${parts}</div>`
        + (s.plain ? `<p class="plain-sql">${rich(s.plain)}</p>` : "")
        + (s.before_table ? `<div class="split-tables"><div><p class="muted">Vorher</p>${renderDataTable(s.before_table)}</div><div><p class="muted">Nach der Query</p>${renderDataTable(s.after_table)}</div></div>` : "");
      const ready = local.explainOpen.size >= (s.parts || []).length;
      foot.innerHTML = footerHtml({ next: ready ? "Weiter" : "Alle Teile antippen" });
      foot.querySelector("[data-act=next]")?.toggleAttribute("disabled", !ready);
      return;
    }

    if (s.type === "inspect") {
      const opts = {
        idField: s.id_field || "id",
        selectedIds: local.selectedIds,
        selectedCols: new Set([...local.selectedCols].filter((x) => !x.includes("::"))),
        clickColumns: s.interaction === "click_column",
        clickRows: s.interaction === "click_row",
        clickCells: s.interaction === "click_cell",
      };
      let extra = "";
      if (s.interaction === "number") {
        extra = `<label class="num-ask">Anzahl <input type="number" id="inspect-num" value="${ui().esc(local.numberValue)}" min="0"></label>`;
      }
      host.innerHTML = title + renderDataTable(s.table, opts) + extra;
      foot.innerHTML = footerHtml({ check: "Prüfen" });
      return;
    }

    if (s.type === "mcq") {
      host.innerHTML = title + `<div class="quiz-options">${(s.options || []).map((o, i) =>
        `<button type="button" class="quiz-option" data-opt="${i}">${rich(o.text)}</button>`
      ).join("")}</div>`;
      foot.innerHTML = footerHtml();
      return;
    }

    if (s.type === "predict" || s.type === "demo") {
      const multiHint = (s.type === "predict" && !s.single)
        ? `<p class="muted table-select-hint">Klick wählt eine Zeile. Mit <kbd>Strg</kbd> weitere dazunehmen, mit <kbd>Umschalt</kbd> einen Bereich von oben nach unten.</p>`
        : "";
      host.innerHTML = title + (s.sql ? sqlBlock(s.sql) : "") + renderStepTables(s, {
        selectedIds: local.selectedIds,
        clickRows: s.type === "predict",
        keepColumns: s.keep_columns,
      }) + multiHint + `<div id="step-result"></div>`;
      if (s.type === "demo") foot.innerHTML = footerHtml({ run: "Ausführen" });
      else foot.innerHTML = footerHtml({ check: s.single ? "Diese Zeile?" : "Prüfen" });
      return;
    }

    if (s.type === "predict-cols") {
      host.innerHTML = title + sqlBlock(s.sql) + renderDataTable(s.table, {
        clickColumns: true,
        selectedCols: local.selectedCols,
      });
      foot.innerHTML = footerHtml({ check: "Prüfen" });
      return;
    }

    if (s.type === "build") {
      const rawPool = [...(s.pieces || []), ...(s.distractors || [])];
      if (!local.pool) {
        const a = rawPool.slice();
        for (let i = a.length - 1; i > 0; i -= 1) {
          const j = (i * 13 + index * 7) % (i + 1);
          [a[i], a[j]] = [a[j], a[i]];
        }
        local.pool = a;
      }
      const used = local.built.slice();
      host.innerHTML = title
        + `<p class="sql-do">${used.length ? "Gebaute Query oben. Baustein dort antippen entfernt ihn." : "Bausteine in der richtigen Reihenfolge antippen."}</p>`
        + `<div class="token-line" id="token-line">${used.map((t, i) => `<button type="button" class="piece-chip" data-pop="${i}"><span class="piece-num">${i + 1}</span>${ui().esc(t)}</button>`).join("") || '<span class="muted">Noch leer — unten wählen</span>'}</div>`
        + `<div class="piece-row" id="token-pool">${local.pool.map((t) => `<button type="button" class="piece-chip" data-push="${ui().esc(t)}">${ui().esc(t)}</button>`).join("")}</div>`
        + sqlBlock(assembledSql() || "—");
      foot.innerHTML = footerHtml({ check: "Prüfen", run: "Ausführen" });
      return;
    }

    if (s.type === "fill") {
      const parts = (s.template || "").split("___");
      let html = "";
      parts.forEach((chunk, i) => {
        html += `<span class="fill-chunk">${ui().colorizeSql(chunk)}</span>`;
        if (i < parts.length - 1) {
          html += `<input class="fill-blank" data-blank="${i}" value="${ui().esc(local.fillValues[i] || "")}" spellcheck="false" placeholder="…">`;
        }
      });
      host.innerHTML = title + `<div class="sql-fill fill-template">${html}</div>`;
      foot.innerHTML = footerHtml({ check: "Prüfen", run: "Ausführen" });
      return;
    }

    if (s.type === "write" || s.type === "apply" || s.type === "challenge") {
      host.innerHTML = title
        + `<label class="sr-only" for="academy-sql">SQL</label>`
        + `<textarea class="sql-editor" id="academy-sql" spellcheck="false" placeholder="${ui().esc(s.placeholder || "SELECT …")}">${ui().esc(local.sqlDraft || "")}</textarea>`;
      foot.innerHTML = footerHtml({ check: "Prüfen", run: "Ausführen" });
      return;
    }

    host.innerHTML = title;
    foot.innerHTML = footerHtml({ next: "Weiter" });
  }

  async function runSql(sql) {
    const data = await ui().postJson("/api/run", {
      sql,
      allow_write: Boolean(step().allow_write),
    });
    return data;
  }

  async function checkSql() {
    const sql = assembledSql();
    const data = await ui().postJson("/api/academy/check", {
      lesson_id: lesson.id,
      step: index,
      sql,
    });
    return { sql, data };
  }

  function pgDetails(data) {
    if (!data.pg_error || data.pg_error === data.error) return "";
    return `<details class="pg-error"><summary>PostgreSQL-Meldung anzeigen</summary><pre>${ui().esc(data.pg_error)}</pre></details>`;
  }

  function resultHtml(data) {
    if (!data.ok && data.error) {
      return failCard(data.coach || data.error, pgDetails(data));
    }
    if (data.correct === false && (data.coach || data.error)) {
      const table = data.columns ? ui().renderSqlResult(data) : "";
      return failCard(data.coach || data.error, table + pgDetails(data));
    }
    return ui().renderSqlResult(data);
  }

  async function onCheck() {
    const s = step();
    if (s.type === "inspect") {
      if (inspectCorrect(s)) completeInteractive();
      else showFeedback(failCard(s.feedback_bad || "Schau noch einmal in die Tabelle: die richtige Spalte, Zeile oder Zelle."));
      return;
    }
    if (s.type === "predict") {
      const expected = new Set((s.expected_ids || []).map(String));
      const got = local.selectedIds;
      const ok = expected.size === got.size && [...expected].every((id) => got.has(id));
      if (ok) {
        completeInteractive();
        if (s.execute && s.sql) {
          const data = await runSql(s.sql);
          const el = document.getElementById("step-feedback");
          if (el && data.ok) {
            el.insertAdjacentHTML("beforeend", `<p class="muted">SQL hat ausgeführt:</p>${ui().renderSqlResult(data)}`);
          }
        }
      } else {
        showFeedback(failCard(s.feedback_bad || "Markiere genau die Zeilen, die zur Abfrage passen."));
      }
      return;
    }
    if (s.type === "predict-cols") {
      const expected = new Set((s.expected_columns || []).map((c) => c.toLowerCase()));
      const got = new Set([...local.selectedCols].map((c) => c.toLowerCase()));
      const ok = expected.size === got.size && [...expected].every((c) => got.has(c));
      if (ok) completeInteractive();
      else showFeedback(failCard(s.feedback_bad || "Markiere genau die Spalten, die nach SELECT stehen."));
      return;
    }

    showFeedback('<p class="muted">Prüfe die Abfrage…</p>');
    const { data } = await checkSql();
    if (data.correct) {
      markStepDone();
      const why = s.feedback_ok || RESULT_OK;
      showFeedback(successCard(why) + ui().renderSqlResult(data));
      renderMeter();
      return;
    }
    showFeedback(resultHtml(data));
  }

  async function onRun() {
    const s = step();
    const sql = s.sql || assembledSql();
    showFeedback('<p class="muted">Führe Abfrage aus…</p>');
    const data = await runSql(sql);
    const box = document.getElementById("step-result");
    const html = data.ok ? ui().renderSqlResult(data) : resultHtml(data);
    if (s.type === "demo" && data.ok) {
      markStepDone();
      const card = `<div class="success-card"><p class="verdict verdict-ok">Ausgeführt</p><p>Vergleiche Tabelle und Ergebnis. ${s.visualize === "where" ? "Nicht passende Zeilen gehören nicht ins Ergebnis." : ""}</p><button class="btn btn-primary" type="button" data-act="next">Weiter</button></div>`;
      showFeedback(card);
      if (box) box.innerHTML = html;
      if (s.visualize === "where" && s.table) {
        const dimmed = new Set();
        (s.table.rows || []).forEach((row) => {
          if (s.match_column && !sameValue(row[s.match_column], s.match_value)) {
            dimmed.add(rowId(row, s.id_field));
          }
        });
        document.querySelectorAll("#step-root tr[data-row-id]").forEach((tr) => {
          if (dimmed.has(tr.dataset.rowId)) tr.classList.add("is-out");
        });
      }
      if (s.visualize === "columns" && s.keep_columns) {
        const keep = new Set(s.keep_columns);
        document.querySelectorAll("#step-root th[data-col], #step-root td[data-col]").forEach((el) => {
          if (!keep.has(el.dataset.col)) el.classList.add("is-fade");
        });
      }
      document.querySelector(".success-card")?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      renderMeter();
      return;
    }
    if (box) box.innerHTML = html;
    else showFeedback(html);
  }

  function paintRowSelection() {
    document.querySelectorAll("#step-root tr[data-row-id]").forEach((tr) => {
      tr.classList.toggle("is-on", local.selectedIds.has(tr.dataset.rowId));
    });
  }

  function paintColSelection() {
    document.querySelectorAll("#step-root th[data-col]").forEach((th) => {
      const col = th.dataset.col;
      th.classList.toggle("is-on", local.selectedCols.has(col) || local.selectedCols.has(col.toLowerCase()));
    });
  }

  function rowIdsInTable(table) {
    return [...table.querySelectorAll("tr[data-row-id]")].map((tr) => tr.dataset.rowId);
  }

  function rowRange(ids, fromId, toId) {
    const a = ids.indexOf(fromId);
    const b = ids.indexOf(toId);
    if (a < 0 || b < 0) return [toId];
    const lo = Math.min(a, b);
    const hi = Math.max(a, b);
    return ids.slice(lo, hi + 1);
  }

  document.getElementById("step-card").addEventListener("mousedown", (e) => {
    if (!e.shiftKey) return;
    if (e.target.closest("tr[data-row-id], th[data-col]")) e.preventDefault();
  });

  document.getElementById("step-meter").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-go]");
    if (!btn) return;
    index = Number(btn.dataset.go);
    resetLocal();
    renderStep();
  });

  document.getElementById("step-card").addEventListener("click", (e) => {
    const s = step();
    const part = e.target.closest("[data-part]");
    if (part) {
      local.explainOpen.add(Number(part.dataset.part));
      renderStep();
      return;
    }
    const th = e.target.closest("th[data-col]");
    if (th && (s.interaction === "click_column" || s.type === "predict-cols")) {
      const col = th.dataset.col;
      if (e.ctrlKey || e.metaKey) {
        if (local.selectedCols.has(col)) local.selectedCols.delete(col);
        else local.selectedCols.add(col);
      } else {
        local.selectedCols = new Set([col]);
      }
      paintColSelection();
      return;
    }
    const td = e.target.closest("td[data-col]");
    if (td && s.interaction === "click_cell") {
      local.selectedCols = new Set([`${td.dataset.col}::${td.dataset.value}`]);
      td.closest("table")?.querySelectorAll("td.is-on").forEach((cell) => cell.classList.remove("is-on"));
      td.classList.add("is-on");
      return;
    }
    const tr = e.target.closest("tr[data-row-id]");
    if (tr && (s.interaction === "click_row" || s.type === "predict")) {
      const id = tr.dataset.rowId;
      const table = tr.closest("table");
      const multi = s.type === "predict" && !s.single && s.interaction !== "click_row";
      if (!multi) {
        local.selectedIds = new Set([id]);
        local.lastRowId = id;
      } else if (e.shiftKey && local.lastRowId) {
        const range = rowRange(rowIdsInTable(table), local.lastRowId, id);
        if (e.ctrlKey || e.metaKey) range.forEach((rid) => local.selectedIds.add(rid));
        else local.selectedIds = new Set(range);
      } else if (e.ctrlKey || e.metaKey) {
        if (local.selectedIds.has(id)) local.selectedIds.delete(id);
        else local.selectedIds.add(id);
        local.lastRowId = id;
      } else {
        local.selectedIds = new Set([id]);
        local.lastRowId = id;
      }
      paintRowSelection();
      return;
    }
    const push = e.target.closest("[data-push]");
    if (push) {
      local.built.push(push.dataset.push);
      renderStep();
      return;
    }
    const pop = e.target.closest("[data-pop]");
    if (pop) {
      local.built.splice(Number(pop.dataset.pop), 1);
      renderStep();
    }
  });

  document.getElementById("step-card").addEventListener("input", (e) => {
    if (e.target.id === "inspect-num") local.numberValue = e.target.value;
    if (e.target.id === "academy-sql") local.sqlDraft = e.target.value;
    if (e.target.classList.contains("fill-blank")) {
      local.fillValues[Number(e.target.dataset.blank)] = e.target.value;
    }
  });

  document.getElementById("step-footer").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn || btn.disabled) return;
    const act = btn.dataset.act;
    if (act === "goto-quiz") {
      switchAcademyTab("quiz");
      document.querySelector(".academy [data-panel=quiz]")?.scrollIntoView({ block: "start", behavior: "smooth" });
      return;
    }
    if (act === "next") {
      if (step().type === "look" || step().type === "explain") markStepDone();
      if (index < steps.length - 1) {
        index += 1;
        resetLocal();
        renderStep();
      } else if (quizCount()) {
        markStepDone();
        switchAcademyTab("quiz");
      } else {
        markStepDone();
        window.location.href = root.dataset.nextId ? `/learn/${root.dataset.nextId}` : "/";
      }
      return;
    }
    if (act === "hint") {
      const hints = step().hints || [];
      if (local.hintLevel < hints.length) local.hintLevel += 1;
      const fb = document.getElementById("step-feedback")?.innerHTML;
      renderStep();
      if (fb) showFeedback(fb);
      else document.getElementById("step-footer").insertAdjacentHTML("beforeend", "");
      return;
    }
    if (act === "check") onCheck();
    if (act === "run") onRun();
  });

  document.getElementById("step-footer").addEventListener("click", (e) => {
    const opt = e.target.closest("[data-opt]");
    if (!opt) return;
  });

  document.getElementById("step-card").addEventListener("click", (e) => {
    const opt = e.target.closest("[data-opt]");
    if (!opt || step().type !== "mcq") return;
    const s = step();
    const i = Number(opt.dataset.opt);
    const ok = Boolean(s.options[i]?.correct);
    document.querySelectorAll("[data-opt]").forEach((b, idx) => {
      b.disabled = true;
      if (s.options[idx].correct) b.classList.add("correct");
    });
    if (!ok) opt.classList.add("wrong");
    if (ok) completeInteractive(s.explain);
    else showFeedback(failCard(s.explain || "Vergleiche die Aussage mit dem, was die Query wirklich tut."));
  });

  document.addEventListener("keydown", (e) => {
    if (!document.getElementById("academy-sql")) return;
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      onRun();
    }
  });

  document.querySelectorAll(".academy .tab").forEach((tab) => {
    tab.addEventListener("click", () => switchAcademyTab(tab.dataset.tab));
  });

  (function initAcademyQuiz() {
    const scoreEl = document.getElementById("quiz-score");
    const questions = [...document.querySelectorAll(".academy .quiz-question")];
    if (!questions.length) return;
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
            : `<p class="verdict verdict-fail">Nicht ganz.</p><p class="muted">${explain || "Schau nochmal in den Schritt oben."}</p>`;
          const s = ui().loadStore();
          const a = ui().academyState(s, lesson.id);
          if (!a.quiz) a.quiz = {};
          a.quiz[qi] = ok;
          markComplete(a);
          s.lastAcademy = lesson.id;
          saveQuiet(s);
          updateScore();
        });
      });
    });
  })();

  resetLocal();
  renderStep();
}

initAcademy();
