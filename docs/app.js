"use strict";

const CATS = [
  { id: "europa", label: "Europa" },
  { id: "swiat", label: "Świat" },
  { id: "polska", label: "Polska" },
  { id: "krakow", label: "Kraków" },
  { id: "kultura", label: "Kultura" },
];
const CAT_COLORS = { europa: ["#4c95ff", "#1446a0"], swiat: ["#2bc4a8", "#0b5e57"], polska: ["#ff6b6f", "#9b1c22"], krakow: ["#a98bff", "#4a2aa6"], kultura: ["#ffb347", "#a8501a"] };
const HERO_COUNT = 4;

const state = { index: [], edition: null, date: null, cat: "europa", topic: null, cache: {} };
const $ = (id) => document.getElementById(id);

const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* prywatne okno */ } },
};

// ── formatowanie ──
const dayFmt = new Intl.DateTimeFormat("pl-PL", { weekday: "long", day: "numeric", month: "long" });
const timeFmt = new Intl.DateTimeFormat("pl-PL", { hour: "2-digit", minute: "2-digit" });
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const parseDay = (iso) => { const [y, m, d] = iso.split("-").map(Number); return new Date(y, m - 1, d, 12); };
const localISO = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

function ago(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const mins = Math.round((Date.now() - d) / 60000);
  if (state.date !== localISO() || mins > 60 * 30) return timeFmt.format(d) + ", " + d.toLocaleDateString("pl-PL", { day: "numeric", month: "short" });
  if (mins < 60) return `${Math.max(mins, 1)} min temu`;
  const h = Math.round(mins / 60);
  return `${h} godz. temu`;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function initials(name) {
  const words = name.replace(/^The\s+/i, "").split(/[\s.]+/).filter(Boolean);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function hue(name) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}
function avatarStyle(name) {
  const h = hue(name);
  return `background:linear-gradient(135deg,hsl(${h} 70% 52%),hsl(${(h + 40) % 360} 65% 38%))`;
}

function placeholder(item) {
  const [c1, c2] = CAT_COLORS[state.cat];
  return `<div class="ph" style="--c1:${c1};--c2:${c2}" aria-hidden="true">${esc(initials(item.source))}</div>`;
}
function picture(item, eager) {
  if (!item.image) return placeholder(item);
  return `<img src="${esc(item.image)}" alt="" ${eager ? "" : 'loading="lazy"'} referrerpolicy="no-referrer" data-ph="1">`;
}
// zdjęcia, których serwis nie pozwala wczytać, zastępujemy planszą
document.addEventListener("error", (e) => {
  const img = e.target;
  if (img.tagName !== "IMG" || !img.dataset.ph) return;
  const holder = document.createElement("div");
  const [c1, c2] = CAT_COLORS[state.cat];
  holder.className = "ph";
  holder.style.cssText = `--c1:${c1};--c2:${c2}`;
  holder.textContent = img.closest("[data-source]")?.dataset.source ? initials(img.closest("[data-source]").dataset.source) : "";
  img.replaceWith(holder);
}, true);

const topicLabel = (t) => (state.edition?.topics?.[t]) || cap(t);

// ── dane ──
async function getJSON(url) {
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

async function loadEdition(date) {
  if (!state.cache[date]) state.cache[date] = await getJSON(`data/${date}.json`);
  state.edition = state.cache[date];
  state.date = date;
  state.topic = null;
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── widok ──
function renderCats() {
  $("cats").innerHTML = CATS.map((c) => {
    const n = state.edition?.categories?.[c.id]?.length ?? 0;
    return `<button class="cat" role="tab" aria-selected="${c.id === state.cat}" data-cat="${c.id}" title="${n} wiadomości">${c.label}</button>`;
  }).join("");
  // na wąskim ekranie nie wszystkie zakładki się mieszczą – wybrana ma być widoczna
  const cats = $("cats"), sel = cats.querySelector('[aria-selected="true"]');
  if (sel) cats.scrollLeft = Math.max(0, sel.offsetLeft + sel.offsetWidth - cats.clientWidth + 20);
  fadeCats();
}

function fadeCats() {
  const c = $("cats");
  c.classList.toggle("more", c.scrollLeft + c.clientWidth < c.scrollWidth - 4);
}
$("cats").addEventListener("scroll", fadeCats, { passive: true });
addEventListener("resize", fadeCats);

function renderNotice() {
  const n = $("notice");
  const newest = state.index[0];
  const today = localISO();
  if (state.date !== newest) {
    n.innerHTML = `<span>Archiwum: <b>${esc(dayFmt.format(parseDay(state.date)))}</b></span><button type="button" data-go="${newest}">Wróć do najnowszego</button>`;
    n.hidden = false;
  } else if (newest !== today) {
    n.innerHTML = `<span>Dzisiejsze wydanie pojawi się o 7:00. Na razie widzisz wydanie z: <b>${esc(dayFmt.format(parseDay(newest)))}</b>.</span>`;
    n.hidden = false;
  } else {
    n.hidden = true;
  }
}

function render() {
  const ed = state.edition;
  renderCats();
  renderNotice();
  const items = ed.categories[state.cat] || [];
  const withImg = items.filter((i) => i.image);
  const heroes = (withImg.length >= 2 ? withImg : items).slice(0, HERO_COUNT);
  const rest = items.filter((i) => !heroes.includes(i));

  const gen = new Date(ed.generated);
  $("editionLabel").textContent = `Wydanie ${timeFmt.format(gen)}`;
  $("carousel").innerHTML = heroes.map((it, i) => `
    <button class="hero" data-i="${items.indexOf(it)}" data-source="${esc(it.source)}" aria-label="${esc(it.title)}">
      ${picture(it, i === 0)}
      <span class="pill">${esc(topicLabel(it.topic))}</span>
      <span class="hero-text">
        <span class="meta light"><span class="src">${esc(it.source)}</span>${it.published ? `<span class="sep"></span><span>${esc(ago(it.published))}</span>` : ""}</span>
        <h3>${esc(it.title)}</h3>
      </span>
    </button>`).join("");
  $("dots").innerHTML = heroes.length > 1 ? heroes.map((_, i) => `<span class="${i ? "" : "on"}"></span>`).join("") : "";
  $("heroSec").hidden = heroes.length === 0;
  $("carousel").scrollLeft = 0;

  const topics = [...new Set(rest.map((i) => i.topic))];
  if (state.topic && !topics.includes(state.topic)) state.topic = null;
  $("topics").innerHTML = rest.length > 3 && topics.length > 1
    ? [`<button class="topic" aria-pressed="${!state.topic}" data-topic="">Wszystko</button>`,
       ...topics.map((t) => `<button class="topic" aria-pressed="${state.topic === t}" data-topic="${esc(t)}">${esc(topicLabel(t))}</button>`)].join("")
    : "";
  const shown = rest.filter((i) => !state.topic || i.topic === state.topic);
  $("count").textContent = `${items.length} wiadomości`;
  $("list").innerHTML = shown.length ? shown.map((it) => `
    <button class="item" data-i="${items.indexOf(it)}" data-source="${esc(it.source)}">
      <span class="thumb">${picture(it)}</span>
      <span>
        <span class="topic-lbl">${esc(topicLabel(it.topic))}</span>
        <h3>${esc(it.title)}</h3>
        ${it.summary ? `<p>${esc(it.summary)}</p>` : ""}
        <span class="meta"><span class="avatar mini-av" style="${avatarStyle(it.source)}">${esc(initials(it.source)[0])}</span><span class="src">${esc(it.source)}</span>${it.published ? `<span class="sep"></span><span>${esc(ago(it.published))}</span>` : ""}</span>
      </span>
    </button>`).join("") : `<div class="empty">${items.length ? "Brak innych wiadomości w tym temacie." : "W tej kategorii nie ma dziś wiadomości."}</div>`;

  renderFoot();
}

function renderFoot() {
  const ed = state.edition;
  const sources = new Set();
  Object.values(ed.categories).flat().forEach((i) => { sources.add(i.source); (i.also || []).forEach((s) => sources.add(s)); });
  const mode = ed.mode === "ai"
    ? "Wybór i streszczenia: Claude (na podstawie leadów ze źródeł)."
    : "Streszczenia to oryginalne leady źródeł (część po angielsku).";
  $("foot").innerHTML = `Wydanie z ${esc(dayFmt.format(parseDay(ed.date)))}, przygotowane o ${esc(timeFmt.format(new Date(ed.generated)))}. ${mode}
    Każda wiadomość prowadzi do pełnego tekstu w źródle.
    <details><summary>Źródła w tym wydaniu (${sources.size})</summary>${esc([...sources].sort((a, b) => a.localeCompare(b, "pl")).join(" · "))}</details>`;
}

// ── artykuł ──
let current = null;
function openArticle(i) {
  const it = state.edition.categories[state.cat][i];
  if (!it) return;
  current = it;
  const hero = $("artHero");
  hero.querySelectorAll("img, .ph").forEach((n) => n.remove());
  hero.dataset.source = it.source;
  hero.insertAdjacentHTML("afterbegin", picture(it, true));
  $("artTopic").textContent = topicLabel(it.topic);
  $("artTitle").textContent = it.title;
  $("artMeta").innerHTML = `<span>${esc(CATS.find((c) => c.id === state.cat).label)}</span>${it.published ? `<span class="sep"></span><span>${esc(ago(it.published))}</span>` : ""}`;
  $("artAvatar").textContent = initials(it.source);
  $("artAvatar").style.cssText = avatarStyle(it.source);
  $("artSource").textContent = it.source;
  $("artSummary").textContent = it.summary || "Źródło nie udostępnia streszczenia – pełny tekst znajdziesz pod linkiem.";
  $("artAlso").textContent = it.also?.length ? `Piszą o tym także: ${it.also.join(", ")}` : "";
  $("artLink").href = it.link;
  $("artLink").firstChild.textContent = `Czytaj w: ${it.source} `;
  $("article").showModal();
  $("article").scrollTop = 0;
}

$("shareBtn").addEventListener("click", async () => {
  if (!current) return;
  if (navigator.share) {
    try { await navigator.share({ title: current.title, url: current.link }); } catch { /* anulowano */ }
  } else {
    try { await navigator.clipboard.writeText(current.link); $("shareBtn").title = "Skopiowano link"; } catch { /* brak uprawnień */ }
  }
});

// ── archiwum ──
function openArchive() {
  const today = localISO();
  $("archList").innerHTML = state.index.map((d) => {
    const dt = parseDay(d);
    const label = d === today ? "Dzisiaj" : cap(dt.toLocaleDateString("pl-PL", { weekday: "long" }));
    return `<button class="arch-day" data-go="${d}" aria-current="${d === state.date}">
      <span class="arch-cal"><b>${dt.getDate()}</b><small>${dt.toLocaleDateString("pl-PL", { month: "short" })}</small></span>
      <span><span class="t">${esc(label)}</span><br><span class="s">${esc(dayFmt.format(dt))}</span></span>
    </button>`;
  }).join("");
  $("archive").showModal();
}

// ── zdarzenia ──
document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-cat],[data-topic],[data-i],[data-go],[data-close]");
  if (!t) {
    if (e.target.tagName === "DIALOG") e.target.close(); // klik w tło
    return;
  }
  if (t.dataset.cat) {
    state.cat = t.dataset.cat;
    state.topic = null;
    store.set("przeglad.cat", state.cat);
    render();
  } else if (t.dataset.topic !== undefined) {
    state.topic = t.dataset.topic || null;
    render();
  } else if (t.dataset.i !== undefined) {
    openArticle(Number(t.dataset.i));
  } else if (t.dataset.go) {
    $("archive").close();
    loadEdition(t.dataset.go).catch(showError);
  } else if (t.dataset.close !== undefined) {
    t.closest("dialog").close();
  }
});
$("archiveBtn").addEventListener("click", openArchive);

$("carousel").addEventListener("scroll", () => {
  const c = $("carousel");
  const first = c.firstElementChild;
  if (!first) return;
  const i = Math.round(c.scrollLeft / (first.offsetWidth + 14));
  [...$("dots").children].forEach((d, k) => d.classList.toggle("on", k === i));
}, { passive: true });

function showError() {
  $("main").innerHTML = `<div class="empty">Nie udało się wczytać wiadomości. Sprawdź połączenie z internetem i odśwież stronę.</div>`;
}

async function init() {
  $("todayLabel").textContent = cap(dayFmt.format(new Date()));
  const saved = store.get("przeglad.cat");
  if (CATS.some((c) => c.id === saved)) state.cat = saved;
  try {
    const idx = await getJSON("data/index.json");
    state.index = idx.editions;
    await loadEdition(state.index[0]);
  } catch {
    showError();
  }
}

// po powrocie do aplikacji rano – sprawdź, czy jest nowe wydanie
document.addEventListener("visibilitychange", async () => {
  if (document.visibilityState !== "visible" || !state.index.length) return;
  try {
    const idx = await getJSON("data/index.json");
    if (idx.editions[0] !== state.index[0]) {
      const wasNewest = state.date === state.index[0];
      state.index = idx.editions;
      if (wasNewest) loadEdition(state.index[0]);
    }
  } catch { /* offline */ }
});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
init();
