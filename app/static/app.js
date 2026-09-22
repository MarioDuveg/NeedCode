const state = {
  problems: [],
  current: null,
  scores: JSON.parse(sessionStorage.getItem("algograder-scores") || "{}"),
  drafts: {},
};

const $ = (id) => document.getElementById(id);
const editor = $("editor");
const submitBtn = $("submit");
const pasteWarning = $("paste-warning");

function saveScores() {
  sessionStorage.setItem("algograder-scores", JSON.stringify(state.scores));
  const totalPassed = Object.values(state.scores).reduce((a, b) => a + Number(b || 0), 0);
  const overall = (totalPassed / 30) * 10;
  $("overall").textContent = `Calificación: ${overall.toFixed(1)} / 10`;
}

function updateLineNumbers() {
  const count = Math.max(1, editor.value.split("\n").length);
  $("line-numbers").textContent = Array.from({ length: count }, (_, i) => i + 1).join("\n");
  $("line-numbers").scrollTop = editor.scrollTop;
}

function flashPasteWarning() {
  pasteWarning.hidden = false;
  clearTimeout(flashPasteWarning.timer);
  flashPasteWarning.timer = setTimeout(() => (pasteWarning.hidden = true), 2200);
}

["paste", "drop"].forEach((eventName) => {
  editor.addEventListener(eventName, (event) => {
    event.preventDefault();
    flashPasteWarning();
  });
});
editor.addEventListener("beforeinput", (event) => {
  if (event.inputType === "insertFromPaste" || event.inputType === "insertFromDrop") {
    event.preventDefault();
    flashPasteWarning();
  }
});
editor.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "v") {
    event.preventDefault();
    flashPasteWarning();
  }
  if (event.key === "Tab") {
    event.preventDefault();
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    editor.setRangeText("    ", start, end, "end");
    updateLineNumbers();
  }
});
editor.addEventListener("input", () => {
  if (state.current) state.drafts[state.current.slug] = editor.value;
  updateLineNumbers();
});
editor.addEventListener("scroll", () => {
  $("line-numbers").scrollTop = editor.scrollTop;
});

function renderList() {
  const list = $("problem-list");
  list.innerHTML = "";
  state.problems.forEach((p, index) => {
    const button = document.createElement("button");
    button.className = "problem-btn" + (p.slug === state.current?.slug ? " active" : "");
    button.innerHTML = `<strong>${index + 1}. ${p.title}</strong><span>${p.difficulty} · ${state.scores[p.slug] ?? 0}/10</span>`;
    button.addEventListener("click", () => selectProblem(p.slug));
    list.appendChild(button);
  });
}

function selectProblem(slug) {
  const p = state.problems.find((item) => item.slug === slug);
  if (!p) return;
  if (state.current) state.drafts[state.current.slug] = editor.value;
  state.current = p;
  $("title").textContent = p.title;
  $("difficulty").textContent = p.difficulty;
  $("statement").textContent = p.statement;
  $("signature").textContent = p.signature;
  $("score").textContent = `${state.scores[p.slug] ?? 0} / 10`;
  $("examples").innerHTML = p.examples
    .map((e) => `<div class="example"><b>Entrada:</b> ${escapeHtml(e.input)}<br><b>Salida:</b> ${escapeHtml(e.output)}</div>`)
    .join("");
  editor.value = state.drafts[p.slug] ?? p.starter_code;
  $("results").innerHTML = '<div class="empty-results">Los resultados de los 10 casos aparecerán aquí.</div>';
  $("status").textContent = "Listo.";
  updateLineNumbers();
  renderList();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[ch]));
}

function renderResults(data) {
  const html = data.cases.map((item) => {
    const status = item.passed ? "Aprobado" : (item.error || "Falló");
    const timing = item.elapsed_ms == null ? "" : `${item.elapsed_ms} ms`;
    let detail = "";
    if (!item.passed && item.public && item.expected !== null) {
      detail = `<div class="result-error">esperado: ${escapeHtml(JSON.stringify(item.expected))}<br>recibido: ${escapeHtml(JSON.stringify(item.received))}</div>`;
    } else if (!item.passed && item.error) {
      detail = `<div class="result-error">${escapeHtml(item.error)}</div>`;
    }
    return `<div class="case ${item.passed ? "pass" : "fail"}"><strong>Caso ${item.case}: ${escapeHtml(status)}</strong><small>${item.public ? "visible" : "oculto"}${timing ? " · " + timing : ""}</small>${detail}</div>`;
  }).join("");
  $("results").innerHTML = `<div class="case-grid">${html}</div>`;
}

async function submitSolution() {
  if (!state.current) return;
  submitBtn.disabled = true;
  $("status").textContent = "Evaluando 10 casos…";
  try {
    const response = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem: state.current.slug, code: editor.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No se pudo evaluar la solución.");
    state.scores[state.current.slug] = Math.max(state.scores[state.current.slug] || 0, data.score);
    saveScores();
    $("score").textContent = `${state.scores[state.current.slug]} / 10`;
    $("status").textContent = `${data.passed}/${data.total} casos · ${data.elapsed_ms} ms totales`;
    renderResults(data);
    renderList();
  } catch (err) {
    $("status").textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
}

$("submit").addEventListener("click", submitSolution);
$("reset").addEventListener("click", () => {
  if (!state.current) return;
  editor.value = state.current.starter_code;
  state.drafts[state.current.slug] = editor.value;
  updateLineNumbers();
});

async function boot() {
  saveScores();
  const response = await fetch("/api/problems");
  state.problems = await response.json();
  selectProblem(state.problems[0].slug);
}

boot().catch((err) => {
  document.body.innerHTML = `<pre style="padding:20px">Error al cargar: ${escapeHtml(err.message)}</pre>`;
});
