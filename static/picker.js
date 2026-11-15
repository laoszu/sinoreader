const form = document.querySelector("form");

let snapshot = null;

const input = form.elements["file"];

input.addEventListener("change", async () => {
    const file = input.files[0];

    if (file) {
        const buffer = await file.arrayBuffer();
        snapshot = { buf: buffer, name: file.name };
    } else
        snapshot = null;
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!snapshot)
        return;

    const formData = new FormData();
    const blob = new Blob([snapshot.buf]);
    formData.append("file", blob, snapshot.name);

    const response = await fetch(form.action, {
        method: "POST",
        body: formData,
    });

    if (response.redirected) {
        location.href = response.url;
        return;
    }

    const html = await response.text();
    document.open();
    document.write(html);
    document.close();
});