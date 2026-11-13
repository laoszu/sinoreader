pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";

const MIN_SCALE = 0.25, MAX_SCALE = 5, STEP = 1.2;

const bus = new pdfjsViewer.EventBus();
const viewer = new pdfjsViewer.PDFViewer({container: c, viewer: v, eventBus: bus});

let fit = true; // while true, re-fit to width on resize / rotation

const clamp = s => Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));
const hasDoc = () => viewer.pagesCount > 0;

function fitWidth() {
  fit = true;
  if (hasDoc()) viewer.currentScaleValue = "page-width";
}
function setScale(s) {
  if (!hasDoc()) return;
  fit = false;
  viewer.currentScale = clamp(s);
}

bus.on("pagesinit", fitWidth);
bus.on("scalechanging", e => zl.textContent = Math.round(e.scale * 100) + "%");

// Toolbar
inn.onclick = () => setScale(viewer.currentScale * STEP);
out.onclick = () => setScale(viewer.currentScale / STEP);
fitb.onclick = fitWidth;
open.onclick = pick.onclick = () => file.click();

// Keep fit-to-width correct when the window resizes or the phone rotates
new ResizeObserver(() => { if (fit && hasDoc()) viewer.currentScaleValue = "page-width"; }).observe(c);

// Desktop: Ctrl/Cmd + wheel (also trackpad pinch) and Ctrl +/-/0
c.addEventListener("wheel", e => {
  if (!e.ctrlKey && !e.metaKey) return;
  e.preventDefault();
  setScale(viewer.currentScale * Math.exp(-e.deltaY * 0.01));
}, {passive: false});

addEventListener("keydown", e => {
  if (!(e.ctrlKey || e.metaKey)) return;
  if (e.key === "+" || e.key === "=") { e.preventDefault(); inn.click(); }
  else if (e.key === "-") { e.preventDefault(); out.click(); }
  else if (e.key === "0") { e.preventDefault(); fitWidth(); }
});

// Phone/tablet: two-finger pinch
let pinch = null, raf = 0;
const dist = t => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);

c.addEventListener("touchstart", e => {
  if (e.touches.length === 2) pinch = {d: dist(e.touches), s: viewer.currentScale};
}, {passive: true});

c.addEventListener("touchmove", e => {
  if (!pinch || e.touches.length !== 2) return;
  e.preventDefault();
  const target = pinch.s * dist(e.touches) / pinch.d;
  if (!raf) raf = requestAnimationFrame(() => { raf = 0; setScale(target); });
}, {passive: false});

c.addEventListener("touchend", e => { if (e.touches.length < 2) pinch = null; });

// Load the chosen PDF in the browser (nothing is uploaded).
let task = null, loading = 0;

async function show(data) {
  const mine = ++loading;
  picker.style.display = "none";
  bar.style.display = "flex";
  c.style.display = "block";
  // Tear down the old document first: replacing it while pages are still rendering
  // makes pdf.js touch already-destroyed page views ("this[#st] is null").
  viewer.setDocument(null);
  if (task) { const old = task; task = null; await old.destroy(); }
  if (mine !== loading) return;               // a newer show() superseded this one
  task = pdfjsLib.getDocument({data: data.slice()});
  const doc = await task.promise;
  if (mine !== loading) return;
  viewer.setDocument(doc);
}

file.addEventListener("change", async () => {
  const f = file.files[0];
  if (!f) return;
  const data = new Uint8Array(await f.arrayBuffer());
  file.value = ""; // allow re-opening the same file
  show(data);
});
