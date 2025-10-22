const form = document.getElementById("render-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "Submitting request…";
  resultsEl.innerHTML = "";

  const payload = {
    address: form.address.value || null,
    apn: form.apn.value || null,
    layers: form.layers.value.split(",").map((x) => x.trim()).filter(Boolean),
    buffer_feet: Number(form.buffer.value),
    output_dpi: Number(form.dpi.value),
  };

  try {
    const response = await fetch("/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const detail = await response.json();
      throw new Error(detail.detail || "Request failed");
    }

    const data = await response.json();
    statusEl.textContent = `Created ${Object.keys(data.images).length} layer images.`;
    renderResults(data);
  } catch (error) {
    console.error(error);
    statusEl.textContent = `Error: ${error.message}`;
  }
});

function renderResults(data) {
  const meta = document.createElement("div");
  meta.className = "metadata";
  meta.innerHTML = `
    <h2>Parcel</h2>
    <p><strong>APN:</strong> ${data.parcel.apn || "n/a"}</p>
    <p><strong>Address:</strong> ${data.parcel.address || "n/a"}</p>
    <p><strong>CRS:</strong> ${data.parcel.crs}</p>
    <p><strong>Created:</strong> ${new Date(data.created_at).toLocaleString()}</p>
  `;
  resultsEl.appendChild(meta);

  const gallery = document.createElement("div");
  gallery.className = "gallery";

  Object.entries(data.images).forEach(([layer, path]) => {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <h3>${layer}</h3>
      <img src="${path}" alt="${layer} image" />
      <a href="${path}" download>Download</a>
    `;
    gallery.appendChild(card);
  });

  if (data.contact_sheet) {
    const link = document.createElement("a");
    link.href = data.contact_sheet;
    link.textContent = "Download contact sheet (PDF)";
    link.className = "contact-sheet";
    gallery.appendChild(link);
  }

  resultsEl.appendChild(gallery);

  if (data.warnings?.length) {
    const warnings = document.createElement("div");
    warnings.className = "warnings";
    warnings.innerHTML = `<h3>Warnings</h3><ul>${data.warnings.map((w) => `<li>${w}</li>`).join("")}</ul>`;
    resultsEl.appendChild(warnings);
  }
}
