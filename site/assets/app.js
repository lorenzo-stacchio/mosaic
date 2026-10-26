"use strict";

/* Crossfield — client-side search over site/data/venues.json.
   A "field" (circle) is a set of SCImago subject areas and/or categories that
   count as alternatives (OR). A venue is listed when it belongs to every
   field (AND), or to at least k of them when the overlap slider is lowered. */

(() => {
  const TYPE_LABELS = { j: "Journals", p: "Conferences and proceedings", k: "Book series", t: "Trade journals" };
  const TYPE_SINGULAR = { j: "Journal", p: "Conference", k: "Book series", t: "Trade journal" };
  const PAGE = 40;
  const MAX_FIELDS = 6;
  const PRESETS = [
    ["Computer Science", "Chemistry"],
    ["History", "Computer Science"],
    ["Mathematics", "History"],
    ["Psychology", "Artificial Intelligence"],
    ["Linguistics and Language", "Artificial Intelligence"],
  ];

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const fold = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const fmt = new Intl.NumberFormat("en");
  const ICON_X = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 2.5l7 7M9.5 2.5l-7 7"/></svg>';
  const ICON_OUT = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M5 2H2v8h8V7M7 2h3v3M10 2 5.5 6.5"/></svg>';

  let D = null;          // dataset
  let catArea = [];      // category index -> area index
  let options = [];      // combobox vocabulary
  let results = [];      // current filtered + sorted results
  let S = [];            // compiled fields

  const state = {
    fields: [],          // [{terms: [{k: "a" | "c", i}]}]
    widen: -1,
    types: new Set(["j", "p", "k", "t"]),
    q: 0,
    qEach: true,
    core: "any",
    coreOnly: true,
    oa: false,
    text: [],            // folded words, all must appear
    minMatch: 0,         // 0 = all fields
    sort: "balance",
    shown: PAGE,
  };

  /* ------------------------------------------------------------- data */

  function prepare(d) {
    catArea = d.cats.map((c) => c.a);
    for (const v of d.venues) {
      v.am = 0;
      for (const a of v.a) v.am |= 1 << a;
      v.cs = v.k.map((x) => x[0]);
      const topics = (v.x || []).map((i) => d.topics[i]);
      v.ft = fold([v.t, v.p, v.r?.n, ...(v.r?.f || []), ...topics, ...(v.s || [])].filter(Boolean).join(" "));
    }
    const areaCount = new Array(d.areas.length).fill(0);
    const catCount = new Array(d.cats.length).fill(0);
    for (const v of d.venues) {
      for (const a of v.a) areaCount[a]++;
      for (const c of v.cs) catCount[c]++;
    }
    options = [
      ...d.areas.map((a, i) => ({ k: "a", i, name: a.n, f: fold(a.n), n: areaCount[i] })),
      ...d.cats.map((c, i) => ({ k: "c", i, name: c.n, f: fold(c.n), n: catCount[i], area: d.areas[c.a].n })),
    ].filter((o) => o.n > 0);
  }

  const termName = (t) => (t.k === "a" ? D.areas[t.i].n : D.cats[t.i].n);

  function findTerm(name) {
    const a = D.areas.findIndex((x) => x.n === name);
    if (a >= 0) return { k: "a", i: a };
    const c = D.cats.findIndex((x) => x.n === name);
    return c >= 0 ? { k: "c", i: c } : null;
  }

  function compile(field) {
    let am = 0;
    const cs = new Set();
    for (const t of field.terms) t.k === "a" ? (am |= 1 << t.i) : cs.add(t.i);
    return { am, cs };
  }

  const inField = (v, f) => (v.am & f.am) !== 0 || v.cs.some((c) => f.cs.has(c));

  // Best quartile of a venue among the categories belonging to a field (0 = none).
  function fieldQuartile(v, f) {
    let best = 0;
    for (const [c, q] of v.k) {
      if (q && (f.cs.has(c) || (f.am & (1 << catArea[c]))) && (!best || q < best)) best = q;
    }
    return best;
  }

  function passesBase(v) {
    if (state.oa && !v.o) return false;
    if (!state.coreOnly && v.m) return false;
    if (state.core !== "any") {
      if (!v.r) return false;
      const limit = state.core === "ranked" ? 4 : Number(state.core);
      if (v.r.o > limit) return false;
    }
    if (state.text.length) {
      for (const w of state.text) if (!v.ft.includes(w)) return false;
    }
    return true;
  }

  function compute() {
    S = state.fields.map(compile);
    const n = S.length;
    const need = state.minMatch && state.minMatch < n ? state.minMatch : n;
    const totals = new Array(n).fill(0);
    const typeCounts = { j: 0, p: 0, k: 0, t: 0 };
    const out = [];
    if (!n) return { out, totals, typeCounts, need };

    for (const v of D.venues) {
      if (!passesBase(v)) continue;
      const typeOk = state.types.has(v.y);
      const qs = new Array(n);
      let hits = 0;
      for (let i = 0; i < n; i++) {
        if (inField(v, S[i])) {
          const q = fieldQuartile(v, S[i]);
          qs[i] = q;
          const qOk = !state.q || (state.qEach ? q && q <= state.q : v.q && v.q <= state.q);
          if (qOk) {
            hits++;
            if (typeOk) totals[i]++;
          }
        } else {
          qs[i] = -1;
        }
      }
      if (hits < need) continue;
      typeCounts[v.y]++;
      if (typeOk) out.push({ v, qs, hits });
    }

    const sjrDesc = (a, b) => (b.v.j ?? -1) - (a.v.j ?? -1);
    const weakest = (r) => Math.max(...r.qs.map((q) => (q < 0 ? 6 : q || 5)));
    const sorters = {
      balance: (a, b) => weakest(a) - weakest(b) || b.hits - a.hits || sjrDesc(a, b),
      sjr: sjrDesc,
      h: (a, b) => (b.v.h ?? -1) - (a.v.h ?? -1),
      core: (a, b) => (a.v.r?.o ?? 99) - (b.v.r?.o ?? 99) || sjrDesc(a, b),
      title: (a, b) => a.v.t.localeCompare(b.v.t),
    };
    out.sort(sorters[state.sort]);
    return { out, totals, typeCounts, need };
  }

  /* ----------------------------------------------------------- render */

  const fieldColor = (i) => `var(--f${i % 6})`;

  function fieldLabel(field) {
    const first = termName(field.terms[0]);
    return field.terms.length > 1 ? `${first} +${field.terms.length - 1}` : first;
  }

  function renderFields() {
    const ol = $("#sectors");
    ol.innerHTML = state.fields.map((f, fi) => {
      const terms = f.terms.map((t, ti) => `
        ${ti ? '<span class="term-or">or</span>' : ""}
        <span class="term">
          <span class="term-name">${esc(termName(t))}</span>
          ${t.k === "c" ? `<span class="term-kind">${esc(D.areas[catArea[t.i]].n)}</span>` : '<span class="term-kind">all categories</span>'}
          ${f.terms.length > 1 ? `<button type="button" data-remove-term="${fi}:${ti}" aria-label="Remove ${esc(termName(t))}">${ICON_X}</button>` : ""}
        </span>`).join("");
      return `
        <li class="sector" style="--c:${fieldColor(fi)}">
          <span class="sector-swatch" aria-hidden="true"></span>
          <div class="sector-terms">${terms}</div>
          <div class="sector-actions">
            <button type="button" class="sector-widen" data-widen="${fi}" aria-pressed="${state.widen === fi}"
              title="Add alternative fields to this circle">${state.widen === fi ? "Done" : "Widen"}</button>
            <button type="button" class="sector-remove" data-remove-field="${fi}" aria-label="Remove field ${esc(fieldLabel(f))}">${ICON_X}</button>
          </div>
        </li>`;
    }).join("");

    const combo = $("#combo");
    const input = $("#field-input");
    combo.classList.toggle("widening", state.widen >= 0);
    combo.style.setProperty("--wc", fieldColor(Math.max(state.widen, 0)));
    if (state.widen >= 0) {
      input.placeholder = `Add an alternative to ${fieldLabel(state.fields[state.widen])}`;
      $("#add-hint").textContent = "Fields added now count as alternatives inside the same circle. Press Done when finished.";
    } else {
      input.placeholder = state.fields.length
        ? "Add another field"
        : "Add a field, e.g. History, Organic Chemistry, Artificial Intelligence";
      $("#add-hint").innerHTML = state.fields.length >= MAX_FIELDS
        ? `Up to ${MAX_FIELDS} fields. Use <em>Widen</em> to add alternatives to an existing circle.`
        : "Adding a field creates a new circle. Use <em>Widen</em> on a circle to accept related fields as alternatives.";
    }
    input.disabled = state.widen < 0 && state.fields.length >= MAX_FIELDS;
    $("#presets").hidden = state.fields.length > 1;

    const fs = $("#match-fieldset");
    const n = state.fields.length;
    fs.hidden = n < 3;
    const range = $("#min-match");
    range.max = String(Math.max(n, 2));
    range.min = "2";
    const val = state.minMatch && state.minMatch < n ? state.minMatch : n;
    range.value = String(val);
    $("#min-match-out").textContent = val >= n ? `all ${n} fields` : `at least ${val} of ${n} fields`;
  }

  /* Venn-style diagram: circles on a ring around a common centre, so the
     centre is always the region shared by every field. */
  const svgNS = "http://www.w3.org/2000/svg";
  function renderDiagram(totals, count, need) {
    const svg = $("#venn");
    const n = state.fields.length;
    const cx = 160, cy = 120;
    const R = [72, 72, 70, 64, 58, 54, 50][n];
    const d = [0, 0, 34, 40, 44, 44, 44][n];
    let layer = svg.querySelector("g.circles");
    if (!layer) {
      svg.innerHTML = '<circle class="outline" cx="160" cy="120" r="72"/><g class="circles"></g><g class="labels"></g>';
      layer = svg.querySelector("g.circles");
    }
    svg.querySelector(".outline").style.display = n ? "none" : "";
    while (layer.children.length > n) layer.lastChild.remove();
    while (layer.children.length < n) {
      const c = document.createElementNS(svgNS, "circle");
      c.setAttribute("class", "circle");
      c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", 0);
      layer.appendChild(c);
    }
    const angle = (i) => (n === 2 ? (i ? 0 : Math.PI) : -Math.PI / 2 + (i * 2 * Math.PI) / n);
    let labels = "";
    [...layer.children].forEach((c, i) => {
      const a = angle(i);
      const x = cx + d * Math.cos(a), y = cy + d * Math.sin(a);
      requestAnimationFrame(() => {
        c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1)); c.setAttribute("r", R);
      });
      c.style.fill = fieldColor(i);
      c.style.fillOpacity = n === 1 ? 0.1 : 0.09;
      c.style.stroke = fieldColor(i);
      if (n > 1) {
        const lx = cx + (d + R * 0.62) * Math.cos(a), ly = cy + (d + R * 0.62) * Math.sin(a);
        labels += `<text class="sector-count" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" style="fill:${fieldColor(i)}">${fmt.format(totals[i])}</text>`;
      }
    });
    if (n) {
      const sub = n === 1 ? "venues" : need >= n ? (n === 2 ? "in both" : `in all ${n}`) : `in ${need}+ of ${n}`;
      const big = n > 2 ? 30 : 40;
      labels += `<text class="count" x="${cx}" y="${cy - 8}" style="font-size:${big}px">${fmt.format(count)}</text>`;
      labels += `<text class="count-sub" x="${cx}" y="${cy + big / 2 + 6}">${sub}</text>`;
    }
    svg.querySelector("g.labels").innerHTML = labels;

    const names = state.fields.map(fieldLabel);
    const cap = $("#venn-caption");
    if (!n) cap.textContent = "Pick a field to begin.";
    else if (n === 1) cap.textContent = `Add a second field to see where ${names[0]} meets it.`;
    else cap.textContent = `${fmt.format(count)} ${count === 1 ? "venue" : "venues"} indexed in ${need >= n ? (n === 2 ? "both" : "all") : `at least ${need} of`} ${names.slice(0, -1).join(", ")} and ${names.at(-1)}.`;
    svg.setAttribute("aria-label", n ? names.map((nm, i) => `${nm}: ${totals[i]}`).join("; ") + `; overlap: ${count}` : "No fields selected");
  }

  function renderTypeFilters(typeCounts) {
    $("#type-filters").innerHTML = Object.entries(TYPE_LABELS).map(([k, label]) => `
      <label class="check"><input type="checkbox" data-type="${k}" ${state.types.has(k) ? "checked" : ""}>
        ${label}<span class="n">${state.fields.length ? fmt.format(typeCounts[k]) : ""}</span></label>`).join("");
  }

  function qchip(q) {
    return q > 0 ? `<span class="qchip q${q}">Q${q}</span>` : '<span class="qchip q0" title="No quartile in this field">–</span>';
  }

  function scimagoUrl(v) { return `https://www.scimagojr.com/journalsearch.php?q=${v.i.slice(1)}&tip=sid&clean=0`; }
  function coreUrl(r) { return `https://portal.core.edu.au/${r.d === "c" ? "conf-ranks" : "jnl-ranks"}/${r.i}/`; }

  function venueHTML(item, idx) {
    const { v, qs } = item;
    const fromScimago = v.i[0] === "s";
    const href = fromScimago ? scimagoUrl(v) : coreUrl(v.r);
    const kind = TYPE_SINGULAR[v.y] + (v.r?.n ? ` ${v.r.n}` : "");

    const pub = [];
    if (v.p) pub.push(esc(v.p));
    if (v.c) pub.push(esc(v.c));
    let pubLine = pub.join(", ");
    if (v.s) pubLine += `${pubLine ? ". " : ""}ISSN ${esc(v.s.join(", "))}`;
    if (v.v) pubLine += `. Covered ${esc(v.v.replace(/-/g, "–"))}`;
    if (v.o) pubLine += v.o === 2 ? ". Diamond open access" : ". Open access";
    if (v.m) pubLine += `${pubLine ? ". " : ""}Listed in CORE only, not indexed by SCImago`;

    const fields = state.fields.map((f, i) => `
      <span class="v-field${qs[i] < 0 ? " miss" : ""}" style="--c:${fieldColor(i)}" title="${qs[i] < 0 ? "Not indexed in this field" : "Best quartile in this field"}">
        <span class="v-field-name">${esc(fieldLabel(f))}</span>${qs[i] < 0 ? '<span class="qchip q0">absent</span>' : qchip(qs[i])}
      </span>`).join("");

    let cats = "";
    if (v.m) {
      cats = `<p class="v-detail"><span class="lbl">CORE fields of research:</span> ${esc(v.r.f.join("; "))}</p>`;
    } else if (v.k.length) {
      const list = v.k.map(([c, q]) => {
        const hit = S.some((f) => f.cs.has(c) || f.am & (1 << catArea[c]));
        const txt = esc(D.cats[c].n) + (q ? ` (Q${q})` : "");
        return hit ? `<span class="hit">${txt}</span>` : txt;
      });
      cats = `<p class="v-detail"><span class="lbl">Categories:</span> ${list.join("; ")}</p>`;
    }
    const topics = v.x?.length
      ? `<p class="v-detail"><span class="lbl">Main topics:</span> ${esc(v.x.map((i) => D.topics[i]).join("; "))}</p>`
      : "";

    const links = [];
    if (fromScimago) links.push(`<a href="${href}" target="_blank" rel="noopener">SCImago profile ${ICON_OUT}</a>`);
    if (v.u) links.push(`<a href="${esc(v.u)}" target="_blank" rel="noopener">Website ${ICON_OUT}</a>`);
    if (v.r) links.push(`<a href="${coreUrl(v.r)}" target="_blank" rel="noopener">CORE entry ${ICON_OUT}</a>`);

    const metrics = [];
    if (fromScimago) {
      metrics.push(`<div class="metric"><dt>SJR</dt><dd>${v.j != null ? v.j.toFixed(3) : "–"}</dd></div>`);
      metrics.push(`<div class="metric"><dt>Best quartile</dt><dd>${qchip(v.q || 0)}</dd></div>`);
      metrics.push(`<div class="metric"><dt>H-index</dt><dd>${v.h ?? "–"}</dd></div>`);
    }
    if (v.r) {
      const ranked = v.r.o < 9;
      metrics.push(`<div class="metric"><dt>CORE ${esc(v.r.e || "")}</dt><dd class="${ranked ? "core" : "muted"}">${esc(v.r.k)}</dd></div>`);
    }

    return `
      <li class="venue">
        <div class="v-num">${idx + 1}</div>
        <div class="v-body">
          <h3 class="v-title"><a href="${href}" target="_blank" rel="noopener">${esc(v.t)}</a><span class="v-kind">${esc(kind)}</span></h3>
          <p class="v-pub">${pubLine}</p>
          <div class="v-fields">${fields}</div>
          ${cats}
          ${topics}
          <div class="v-links">${links.join("")}</div>
        </div>
        <dl class="v-metrics">${metrics.join("")}</dl>
      </li>`;
  }

  function renderResults() {
    const list = $("#venues");
    const empty = $("#empty");
    const more = $("#more");
    $(".results-head").hidden = !state.fields.length;
    $("#result-count").textContent = fmt.format(results.length);
    $("#result-noun").textContent = results.length === 1 ? "venue" : "venues";
    $("#export").disabled = !results.length;

    if (!state.fields.length) {
      list.innerHTML = "";
      more.hidden = true;
      empty.hidden = false;
      empty.innerHTML = `<h3>Start with the fields you work across</h3>
        <p>For example, a chemist who builds machine-learning models might add <em>Chemistry</em> and <em>Artificial Intelligence</em>; a historian working with quantitative methods might add <em>History</em> and <em>Mathematics</em>.</p>
        <p>Each venue then shows its quartile in every field you chose, its main topics, and links to its SCImago profile, website and CORE entry.</p>`;
      return;
    }
    if (!results.length) {
      list.innerHTML = "";
      more.hidden = true;
      empty.hidden = false;
      const tips = [];
      if (state.q) tips.push("lower the quartile requirement");
      if (state.core !== "any") tips.push("set CORE ranking to Any");
      if (state.text.length) tips.push("clear the text filter");
      if (state.fields.length > 2) tips.push("lower the overlap slider");
      tips.push("widen a circle with related categories, or use the whole subject area");
      empty.innerHTML = `<h3>No venue is indexed in all these fields</h3><p>To find near matches, ${tips.join(", ")}.</p>`;
      return;
    }
    empty.hidden = true;
    list.innerHTML = results.slice(0, state.shown).map(venueHTML).join("");
    more.hidden = results.length <= state.shown;
    more.textContent = `Show ${Math.min(PAGE, results.length - state.shown)} more of ${fmt.format(results.length - state.shown)}`;
  }

  function update({ keepPage = false } = {}) {
    if (!keepPage) state.shown = PAGE;
    const { out, totals, typeCounts, need } = compute();
    results = out;
    renderFields();
    renderDiagram(totals, out.length, need);
    renderTypeFilters(typeCounts);
    renderResults();
    writeHash();
  }

  /* ------------------------------------------------------ interaction */

  function addTerm(term) {
    if (state.widen >= 0) {
      const f = state.fields[state.widen];
      if (!f.terms.some((t) => t.k === term.k && t.i === term.i)) f.terms.push(term);
    } else {
      const dup = state.fields.some((f) => f.terms.length === 1 && f.terms[0].k === term.k && f.terms[0].i === term.i);
      if (!dup && state.fields.length < MAX_FIELDS) state.fields.push({ terms: [term] });
    }
    update();
  }

  function setupCombo() {
    const input = $("#field-input");
    const list = $("#field-list");
    let active = -1;
    let shown = [];

    function search(q) {
      const fq = fold(q.trim());
      if (!fq) return options.filter((o) => o.k === "a").sort((a, b) => a.name.localeCompare(b.name));
      const scored = [];
      for (const o of options) {
        const pos = o.f.indexOf(fq);
        if (pos < 0) continue;
        const wordStart = pos === 0 || o.f[pos - 1] === " " || o.f[pos - 1] === "(";
        scored.push([pos === 0 ? 0 : wordStart ? 1 : 2, o.k === "a" ? 0 : 1, o]);
      }
      scored.sort((a, b) => a[0] - b[0] || a[1] - b[1] || b[2].n - a[2].n);
      return scored.slice(0, 40).map((s) => s[2]);
    }

    function highlight(name, q) {
      const fq = fold(q.trim());
      const pos = fq ? fold(name).indexOf(fq) : -1;
      if (pos < 0) return esc(name);
      return esc(name.slice(0, pos)) + "<mark>" + esc(name.slice(pos, pos + fq.length)) + "</mark>" + esc(name.slice(pos + fq.length));
    }

    function open() {
      shown = search(input.value);
      active = shown.length ? 0 : -1;
      list.innerHTML = shown.length
        ? shown.map((o, i) => `
          <li id="opt-${i}" role="option" class="${o.k === "a" ? "opt-area" : "opt-cat"}" aria-selected="${i === active}" data-idx="${i}">
            <span class="opt-name">${highlight(o.name, input.value)}</span>
            <span class="opt-meta">${o.k === "a" ? "subject area" : esc(o.area)}</span>
          </li>`).join("")
        : '<li class="opt-empty" role="option" aria-disabled="true">No SCImago field matches. Try a broader word.</li>';
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
      input.setAttribute("aria-activedescendant", active >= 0 ? `opt-${active}` : "");
    }
    function close() {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }
    function move(delta) {
      if (!shown.length) return;
      active = (active + delta + shown.length) % shown.length;
      list.querySelectorAll("li").forEach((li, i) => li.setAttribute("aria-selected", String(i === active)));
      const li = list.querySelector(`#opt-${active}`);
      li?.scrollIntoView({ block: "nearest" });
      input.setAttribute("aria-activedescendant", `opt-${active}`);
    }
    function choose(i) {
      const o = shown[i];
      if (!o) return;
      input.value = "";
      close();
      addTerm({ k: o.k, i: o.i });
      input.focus();
    }

    input.addEventListener("input", open);
    input.addEventListener("focus", open);
    input.addEventListener("blur", () => setTimeout(close, 120));
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); list.hidden ? open() : move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") { e.preventDefault(); if (!list.hidden) choose(active); }
      else if (e.key === "Escape") { close(); }
      else if (e.key === "Backspace" && !input.value && state.fields.length && state.widen < 0) {
        state.fields.pop();
        update();
      }
    });
    list.addEventListener("mousedown", (e) => {
      const li = e.target.closest("li[data-idx]");
      if (li) { e.preventDefault(); choose(Number(li.dataset.idx)); }
    });
  }

  function setupControls() {
    $("#sectors").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.removeField != null) {
        const i = Number(b.dataset.removeField);
        state.fields.splice(i, 1);
        if (state.widen === i) state.widen = -1;
        else if (state.widen > i) state.widen--;
      } else if (b.dataset.removeTerm != null) {
        const [fi, ti] = b.dataset.removeTerm.split(":").map(Number);
        state.fields[fi].terms.splice(ti, 1);
      } else if (b.dataset.widen != null) {
        const i = Number(b.dataset.widen);
        state.widen = state.widen === i ? -1 : i;
        if (state.widen >= 0) setTimeout(() => $("#field-input").focus(), 0);
      }
      update();
    });

    $("#type-filters").addEventListener("change", (e) => {
      const k = e.target.dataset.type;
      if (!k) return;
      e.target.checked ? state.types.add(k) : state.types.delete(k);
      update();
    });

    const segmented = (sel, key, parse) => {
      $(sel).addEventListener("click", (e) => {
        const b = e.target.closest("button");
        if (!b) return;
        state[key] = parse(b);
        update();
      });
    };
    segmented("#quartile-filter", "q", (b) => Number(b.dataset.q));
    segmented("#core-filter", "core", (b) => b.dataset.core);

    $("#q-each").addEventListener("change", (e) => { state.qEach = e.target.checked; update(); });
    $("#core-only").addEventListener("change", (e) => { state.coreOnly = e.target.checked; update(); });
    $("#oa-only").addEventListener("change", (e) => { state.oa = e.target.checked; update(); });
    let timer;
    $("#text-filter").addEventListener("input", (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.text = fold(e.target.value).split(/\s+/).filter(Boolean); update(); }, 180);
    });
    $("#min-match").addEventListener("input", (e) => {
      const v = Number(e.target.value);
      state.minMatch = v >= state.fields.length ? 0 : v;
      update();
    });
    $("#sort").addEventListener("change", (e) => { state.sort = e.target.value; update(); });
    $("#more").addEventListener("click", () => { state.shown += PAGE; renderResults(); });
    $("#export").addEventListener("click", exportCsv);

    const presets = $("#presets");
    for (const p of PRESETS) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "preset";
      b.textContent = p.join(" and ");
      b.addEventListener("click", () => {
        state.fields = p.map(findTerm).filter(Boolean).map((t) => ({ terms: [t] }));
        state.widen = -1;
        update();
      });
      presets.appendChild(b);
    }

    $("#theme-toggle").addEventListener("click", () => {
      const root = document.documentElement;
      const dark = root.dataset.theme
        ? root.dataset.theme === "dark"
        : matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      try { localStorage.setItem("crossfield-theme", root.dataset.theme); } catch (_) { /* storage unavailable */ }
    });
  }

  function syncControls() {
    document.querySelectorAll("#quartile-filter button").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.q) === state.q)));
    document.querySelectorAll("#core-filter button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.core === state.core)));
    $("#q-each").checked = state.qEach;
    $("#core-only").checked = state.coreOnly;
    $("#oa-only").checked = state.oa;
    $("#sort").value = state.sort;
  }

  /* ------------------------------------------------- shareable state */

  function writeHash() {
    syncControls();
    const p = new URLSearchParams();
    if (state.fields.length) {
      p.set("f", state.fields.map((f) => f.terms.map((t) => `${t.k}:${termName(t)}`).join("|")).join(";"));
    }
    if (state.types.size < 4) p.set("type", [...state.types].join(""));
    if (state.q) p.set("q", state.q);
    if (!state.qEach) p.set("qbest", "1");
    if (state.core !== "any") p.set("core", state.core);
    if (!state.coreOnly) p.set("coreonly", "0");
    if (state.oa) p.set("oa", "1");
    if (state.text.length) p.set("text", state.text.join(" "));
    if (state.minMatch) p.set("k", state.minMatch);
    if (state.sort !== "balance") p.set("sort", state.sort);
    const hash = p.toString();
    history.replaceState(null, "", hash ? `#${hash}` : location.pathname + location.search);
  }

  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    if (p.get("f")) {
      state.fields = p.get("f").split(";").map((f) => ({
        terms: f.split("|").map((t) => {
          const [k, ...rest] = t.split(":");
          const name = rest.join(":");
          const i = k === "a" ? D.areas.findIndex((a) => a.n === name) : D.cats.findIndex((c) => c.n === name);
          return i >= 0 ? { k, i } : null;
        }).filter(Boolean),
      })).filter((f) => f.terms.length).slice(0, MAX_FIELDS);
    }
    if (p.get("type")) state.types = new Set(p.get("type").split("").filter((c) => c in TYPE_LABELS));
    if (p.get("q")) state.q = Math.min(3, Math.max(0, Number(p.get("q")) || 0));
    if (p.get("qbest")) state.qEach = false;
    if (["ranked", "2", "3"].includes(p.get("core"))) state.core = p.get("core");
    if (p.get("coreonly") === "0") state.coreOnly = false;
    if (p.get("oa")) state.oa = true;
    if (p.get("text")) state.text = fold(p.get("text")).split(/\s+/).filter(Boolean);
    if (p.get("k")) state.minMatch = Number(p.get("k")) || 0;
    if (["sjr", "h", "core", "title"].includes(p.get("sort"))) state.sort = p.get("sort");
  }

  /* ----------------------------------------------------------- export */

  function exportCsv() {
    const names = state.fields.map(fieldLabel);
    const head = ["Title", "Type", "ISSN", "Publisher", "Country", "Open access", "SJR", "Best quartile", "H-index",
      ...names.map((n) => `Quartile in ${n}`), "CORE rank", "CORE edition", "Categories", "Main topics",
      "SCImago URL", "Website", "CORE URL"];
    const rows = results.map(({ v, qs }) => [
      v.t, TYPE_SINGULAR[v.y], (v.s || []).join(" "), v.p || "", v.c || "",
      v.o === 2 ? "Diamond" : v.o ? "Yes" : "", v.j ?? "", v.q ? `Q${v.q}` : "", v.h ?? "",
      ...qs.map((q) => (q < 0 ? "absent" : q ? `Q${q}` : "")),
      v.r?.k || "", v.r?.e || "",
      v.m ? (v.r?.f || []).join("; ") : v.k.map(([c, q]) => D.cats[c].n + (q ? ` (Q${q})` : "")).join("; "),
      (v.x || []).map((i) => D.topics[i]).join("; "),
      v.i[0] === "s" ? scimagoUrl(v) : "", v.u || "", v.r ? coreUrl(v.r) : "",
    ]);
    const cell = (x) => {
      const s = String(x);
      return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const csv = "﻿" + [head, ...rows].map((r) => r.map(cell).join(",")).join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    a.download = `crossfield_${names.join("_x_").replace(/[^\w]+/g, "-").slice(0, 120) || "venues"}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  /* ------------------------------------------------------------- boot */

  function renderMeta() {
    const m = D.meta;
    const core = [m.core.conferences && `${m.core.conferences} conferences`, m.core.journals && `${m.core.journals} journals`].filter(Boolean).join(" and ");
    $("#colophon").innerHTML = `
      <p>Data: SCImago Journal Rank ${m.scimago.year} (${fmt.format(m.scimago.sources)} sources)${core ? `, CORE ${core} (${fmt.format(m.core.linked)} linked to SCImago, ${fmt.format(m.core.core_only)} listed only in CORE)` : ""}${m.openalex ? `, main topics and websites from OpenAlex (${fmt.format(m.openalex)} sources)` : ""}. Updated ${esc(m.built)}.</p>
      <p>Quartiles follow SCImago: Q1 is the top quarter of a category by SJR. CORE-only venues are placed in SCImago fields through their ANZSRC field-of-research codes and have no quartile.</p>`;
    if (m.partial) {
      const pivot = m.pivots.length ? ` Every source is indexed in ${m.pivots.join(" and ")}, so results always include ${m.pivots.length > 1 ? "these fields" : "this field"}.` : "";
      const notice = $("#notice");
      notice.hidden = false;
      notice.innerHTML = `<div class="notice-inner"><strong>Partial SCImago data.</strong> This build contains ${fmt.format(m.scimago.sources)} SCImago sources.${pivot} Add the full SCImago export to <code>data/raw/scimago/</code> and rebuild to search every combination.</div>`;
    }
  }

  async function boot() {
    try {
      const saved = localStorage.getItem("crossfield-theme");
      if (saved) document.documentElement.dataset.theme = saved;
    } catch (_) { /* storage unavailable */ }

    $("#empty").hidden = false;
    $("#empty").innerHTML = "<p>Loading venues…</p>";
    try {
      const res = await fetch("data/venues.json");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      D = await res.json();
    } catch (err) {
      $("#empty").innerHTML = `<h3>The venue index could not be loaded</h3>
        <p>Expected <code>data/venues.json</code> next to this page (${esc(err.message)}). Build it with <code>python -m crossfield build</code>, then reload.</p>`;
      return;
    }
    prepare(D);
    if (matchMedia("(max-width: 899px)").matches) $("#filters-details").open = false;
    renderMeta();
    setupCombo();
    setupControls();
    readHash();
    $("#text-filter").value = state.text.join(" ");
    update();
  }

  boot();
})();
