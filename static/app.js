const pages = document.getElementById("pages");
const popup = document.getElementById("popup");
const chars = new Map();
let current = null;

// ctrl +/-/0 and ctrl+wheel zoom the document
const zoom = (id) => (location.href = document.getElementById(id).href);
addEventListener("keydown", (e) => {
  const k = { "+": "in", "=": "in", "-": "out", "0": "fit" }[e.key];
  if (k && (e.ctrlKey || e.metaKey)) { e.preventDefault(); zoom(k); }
  if (e.key === "Escape") hide();
});
addEventListener("wheel", (e) => {
  if (e.ctrlKey) { e.preventDefault(); zoom(e.deltaY < 0 ? "in" : "out"); }
}, { passive: false });

// selectable text: transparent span per character over the page image
document.querySelectorAll(".page").forEach(async (page) => {
  const list = await (await fetch(`/doc/${pages.dataset.doc}/page/${page.dataset.n}/chars.json`)).json();
  chars.set(page, list);
  let line, last = -1;
  list.forEach(([ch, x, y, w, h, n], i) => {
    if (n !== last) {
      if (line) line.append(document.createElement("br"));   // line breaks when copying
      line = Object.assign(document.createElement("div"), { className: "line" });
      page.append(line);
      last = n;
    }
    const s = Object.assign(document.createElement("span"), { className: "c", textContent: ch });
    s.dataset.i = i;
    s.style.cssText = `left:${x * 100}%;top:${y * 100}%;width:${w * 100}%;height:${h * 100}%;font-size:${h * 100}cqh`;
    line.append(s);
  });
});

// dictionary popup: hover (mouse) or tap (phone)
function hide() { current = null; popup.style.display = "none"; }

async function show(span, ev) {
  current = span;
  const list = chars.get(span.closest(".page")), i = +span.dataset.i;
  const q = list.slice(i, i + +pages.dataset.len).map((c) => c[0]).join("");
  if (!/^[㐀-鿿]/.test(q)) return hide();
  const groups = await (await fetch("/lookup?q=" + encodeURIComponent(q))).json();
  if (current !== span) return;   // pointer moved on
  popup.textContent = groups.length
    ? groups.flatMap((g) => g.entries).map((e) => `${e.simplified} ${e.traditional} ${e.pinyin}\n${e.polish}\n${e.english}`).join("\n\n")
    : "Not in dictionary";
  popup.style.display = "block";
  popup.style.left = Math.min(ev.pageX, scrollX + innerWidth - popup.offsetWidth - 8) + "px";
  popup.style.top = ev.pageY + 16 + "px";
}

addEventListener("pointerover", (e) => {
  if (e.pointerType !== "mouse" || e.buttons) return;   // not while selecting
  const s = e.target.closest(".c");
  s ? show(s, e) : hide();
});
addEventListener("click", (e) => {
  const s = e.target.closest(".c");
  s && !getSelection().toString() ? show(s, e) : s || hide();
});
