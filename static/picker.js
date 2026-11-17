const form = document.querySelector("form");
const input = form.elements["file"];
let snapshot = null;  // read into memory on selection, so a remote-drive file can't vanish before submit

input.addEventListener("change", async () => {
  const f = input.files[0];
  snapshot = f && { blob: new Blob([await f.arrayBuffer()]), name: f.name };
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!snapshot) return;
  const body = new FormData();
  body.append("file", snapshot.blob, snapshot.name);
  const r = await fetch(form.action, { method: "POST", body });
  if (r.redirected) return (location.href = r.url);
  document.open(); document.write(await r.text()); document.close();
});
