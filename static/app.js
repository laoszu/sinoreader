const pages = document.getElementById("pages");
const popup = document.getElementById("popup");
const ds = pages.dataset;
const chars = new Map();
let current = null;
let zoom = +ds.zoom, pinyin = +ds.pinyin;

function setZoom(z, x = innerWidth / 2, y = innerHeight / 2) {
  z = Math.max(+ds.min, Math.min(+ds.max, Math.round(z)));
  if (z === zoom) return;
  const k = z / zoom;
  zoom = z;
  pages.style.setProperty("--zoom", z);
  document.getElementById("zoomlabel").textContent = z + "%";
  scrollTo((scrollX + x) * k - x, (scrollY + y) * k - y);
  history.replaceState(null, "", `?zoom=${z}&pinyin=${pinyin}`);
}

const on = (id, fn) => document.getElementById(id).addEventListener("click", (e) => { e.preventDefault(); fn(); });
on("in", () => setZoom(zoom * +ds.step));
on("out", () => setZoom(zoom / +ds.step));
on("fit", () => setZoom(100));
on("pinyin", () => {
  pinyin = 1 - pinyin;
  document.getElementById("pinyin").textContent = pinyin ? "拼音!" : "拼音";
  history.replaceState(null, "", `?zoom=${zoom}&pinyin=${pinyin}`);
  document.querySelectorAll(".page img").forEach((img) => {
    img.src = `/doc/${ds.doc}/page/${img.closest(".page").dataset.n}.svg?pinyin=${pinyin}`;
  });
});

on("save", () => {
    location.href = `/doc/${ds.doc}/pinyin.pdf`;
});

addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });

addEventListener("wheel", (e) => {
  if (!e.ctrlKey) return;
  e.preventDefault();
  setZoom(zoom * Math.exp(-e.deltaY * 0.01), e.clientX, e.clientY);
}, { passive: false });

async function buildChars(page) {
  const list = await (await fetch(`/doc/${ds.doc}/page/${page.dataset.n}/chars.json`)).json();
  chars.set(page, list);
  let line, last = -1;
  const frag = document.createDocumentFragment();
  list.forEach(([ch, x, y, w, h, n], i) => {
    if (n !== last) {
      line = Object.assign(document.createElement("div"), { className: "line" });
      frag.append(line);
      last = n;
    }
    const s = Object.assign(document.createElement("span"), { className: "c", textContent: ch });
    s.dataset.i = i;
    s.style.cssText = `left:${x * 100}%;top:${y * 100}%;width:${w * 100}%;height:${h * 100}%;font-size:${h * 100}cqh`;
    line.append(s);
  });
  page.append(frag);
}

// build the text layer only for pages near the viewport
const io = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (e.isIntersecting) { io.unobserve(e.target); buildChars(e.target); }
}), { rootMargin: "1500px 0px" });
document.querySelectorAll(".page").forEach((p) => io.observe(p));

function hide() { current = null; popup.style.display = "none"; }

async function show(span, ev) {
  current = span;
  const list = chars.get(span.closest(".page"));
  const i = parseInt(span.dataset.i, 10);
  const len = parseInt(ds.len, 10);
  const start = Math.max(0, i - len + 1);
  const q = list.slice(start, i + len).map((c) => c[0]).join("");
  const pos = i - start;

  if (!/[㐀-鿿]/.test(q[pos])) return hide();
  const groups = await (await fetch("/lookup?q=" + encodeURIComponent(q) + "&pos=" + pos)).json();
  if (current !== span) return;
  popup.textContent = groups.length
    ? groups.flatMap((g) => g.entries).map((e) => `${e.simplified} ${e.traditional} ${e.pinyin}\n${e.polish}\n${e.english}`).join("\n\n")
    : "nie ma w słowniku 😭";
  popup.style.display = "block";
  popup.style.left = Math.min(ev.pageX, scrollX + innerWidth - popup.offsetWidth - 8) + "px";
  popup.style.top = ev.pageY + 16 + "px";
}

addEventListener("pointerover", (e) => {
  if (e.pointerType !== "mouse" || e.buttons) return;
  const s = e.target.closest(".c");
  s ? show(s, e) : hide();
});
addEventListener("click", (e) => {
  const s = e.target.closest(".c");
  s && !getSelection().toString() ? show(s, e) : s || hide();
});