// Frontend behavior for the LLM Judge Tool.
//
// Submitting the form sends the prompt to the backend's /api/generate
// endpoint, which calls several LLMs and returns all of their responses.
// Each model's response (or error) is rendered in its own labeled card.
// There is no "winner" yet — that will be added once the judge (PR 6) is
// wired up.

const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt-input");
const responseOutput = document.getElementById("response-output");
const resultsGrid = document.getElementById("results-grid");
const submitButton = document.getElementById("submit-button");

function renderResults(results) {
  resultsGrid.innerHTML = "";

  results.forEach(function (result) {
    const card = document.createElement("div");
    card.className = "model-card" + (result.error ? " model-card--error" : "");

    const title = document.createElement("h3");
    title.textContent = result.model;
    card.appendChild(title);

    const body = document.createElement("div");
    body.className = "model-card__body";
    body.textContent = result.error ? result.error : result.response;
    card.appendChild(body);

    resultsGrid.appendChild(card);
  });
}

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  const prompt = promptInput.value.trim();

  if (!prompt) {
    return;
  }

  submitButton.disabled = true;
  responseOutput.textContent = "Loading responses from all models...";
  resultsGrid.innerHTML = "";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await res.json();

    if (!res.ok) {
      responseOutput.textContent = `Error: ${data.error || "Something went wrong."}`;
      return;
    }

    responseOutput.textContent = `Showing ${data.results.length} model response(s):`;
    renderResults(data.results);
  } catch (err) {
    responseOutput.textContent = `Error: could not reach the backend (${err}).`;
  } finally {
    submitButton.disabled = false;
  }
});
