const state = {
  referenceDataUrl: null,
};

const elements = {
  messages: document.getElementById("messages"),
  composer: document.getElementById("composer"),
  textInput: document.getElementById("textInput"),
  referenceInput: document.getElementById("referenceInput"),
  referencePreview: document.getElementById("referencePreview"),
  clearChat: document.getElementById("clearChat"),
  generateButton: document.getElementById("generateButton"),
  outputFormat: document.getElementById("outputFormat"),
  typoProbability: document.getElementById("typoProbability"),
  typoValue: document.getElementById("typoValue"),
  correctionProbability: document.getElementById("correctionProbability"),
  correctionValue: document.getElementById("correctionValue"),
  baselineDrift: document.getElementById("baselineDrift"),
  baselineValue: document.getElementById("baselineValue"),
  inkBlotProbability: document.getElementById("inkBlotProbability"),
  inkValue: document.getElementById("inkValue"),
  messageTemplate: document.getElementById("messageTemplate"),
};

function addMessage(role, html) {
  const fragment = elements.messageTemplate.content.cloneNode(true);
  const node = fragment.querySelector(".message");
  const avatar = fragment.querySelector(".avatar");
  const bubble = fragment.querySelector(".bubble");
  node.classList.add(role);
  avatar.textContent = role === "user" ? "Y" : "H";
  bubble.innerHTML = html;
  elements.messages.appendChild(fragment);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function setPreview(dataUrl) {
  if (!dataUrl) {
    elements.referencePreview.classList.add("is-empty");
    elements.referencePreview.textContent = "Upload a handwritten page to extract style.";
    return;
  }
  elements.referencePreview.classList.remove("is-empty");
  elements.referencePreview.innerHTML = `<img src="${dataUrl}" alt="Reference preview">`;
}

function updateRangeLabels() {
  elements.typoValue.textContent = Number(elements.typoProbability.value).toFixed(2);
  elements.correctionValue.textContent = Number(elements.correctionProbability.value).toFixed(2);
  elements.baselineValue.textContent = `${elements.baselineDrift.value} px`;
  elements.inkValue.textContent = Number(elements.inkBlotProbability.value).toFixed(2);
}

async function readFileAsDataUrl(file) {
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderResultCard(data) {
  const pageLinks = (data.page_urls || [])
    .map((url, index) => `<a href="${url}" target="_blank" rel="noreferrer">Open page ${index + 1}</a>`)
    .join("");
  return `
    <p>${data.message}</p>
    <div class="result-card">
      <img class="result-preview" src="${data.preview_url}" alt="Generated preview">
      <div class="result-links">
        <a href="${data.download_url}" target="_blank" rel="noreferrer">Download ${data.download_name}</a>
        ${pageLinks}
      </div>
    </div>
  `;
}

elements.referenceInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    state.referenceDataUrl = null;
    setPreview(null);
    return;
  }
  state.referenceDataUrl = await readFileAsDataUrl(file);
  setPreview(state.referenceDataUrl);
});

elements.clearChat.addEventListener("click", () => {
  elements.messages.innerHTML = `
    <article class="message assistant">
      <div class="avatar">H</div>
      <div class="bubble">
        <p>Paste or type the document you want rewritten, upload one handwritten reference page, and I’ll generate a human-like handwritten version with controlled imperfections.</p>
      </div>
    </article>
  `;
});

elements.typoProbability.addEventListener("input", updateRangeLabels);
elements.correctionProbability.addEventListener("input", updateRangeLabels);
elements.baselineDrift.addEventListener("input", updateRangeLabels);
elements.inkBlotProbability.addEventListener("input", updateRangeLabels);
updateRangeLabels();

elements.composer.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = elements.textInput.value.trim();
  if (!text) {
    addMessage("assistant", "<p>Please enter text before generating.</p>");
    return;
  }
  if (!state.referenceDataUrl) {
    addMessage("assistant", "<p>Please upload a handwritten reference image first.</p>");
    return;
  }

  addMessage("user", `<p>${text.replaceAll("\n", "<br>")}</p>`);
  addMessage("assistant", '<p class="loading">Generating handwritten pages from your reference sample...</p>');
  const loadingNode = elements.messages.lastElementChild;

  elements.generateButton.disabled = true;

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        reference_image: state.referenceDataUrl,
        output_format: elements.outputFormat.value,
        settings: {
          typo_probability: Number(elements.typoProbability.value),
          correction_probability: Number(elements.correctionProbability.value),
          line_baseline_drift_px: Number(elements.baselineDrift.value),
          ink_blot_probability: Number(elements.inkBlotProbability.value),
        },
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Generation failed.");
    }
    loadingNode.querySelector(".bubble").innerHTML = renderResultCard(data);
  } catch (error) {
    loadingNode.querySelector(".bubble").innerHTML = `<p>${error.message}</p>`;
  } finally {
    elements.generateButton.disabled = false;
  }
});
