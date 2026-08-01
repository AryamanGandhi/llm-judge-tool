// Frontend behavior for the LLM Judge Tool.
//
// Submitting the form sends the prompt to the backend's /api/generate
// endpoint, which calls several LLMs and returns all of their responses,
// plus a "judgment" from a judge LLM that picks the best one. The winning
// model's card is highlighted, and the judge's reasoning is shown above
// the results grid.

const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt-input");
const responseOutput = document.getElementById("response-output");
const judgmentOutput = document.getElementById("judgment-output");
const resultsGrid = document.getElementById("results-grid");
const submitButton = document.getElementById("submit-button");

function renderJudgment(judgment) {
  judgmentOutput.innerHTML = "";

  if (!judgment) {
    return;
  }

  if (judgment.winner) {
    const banner = document.createElement("div");
    banner.className = "judgment-banner";

    const title = document.createElement("div");
    title.className = "judgment-banner__title";
    title.textContent = `🏆 Winner: ${judgment.winner}`;
    banner.appendChild(title);

    const reasoning = document.createElement("div");
    reasoning.className = "judgment-banner__reasoning";
    reasoning.textContent = judgment.reasoning;
    banner.appendChild(reasoning);

    judgmentOutput.appendChild(banner);
  } else if (judgment.error) {
    const banner = document.createElement("div");
    banner.className = "judgment-banner judgment-banner--error";
    banner.textContent = `Judge unavailable: ${judgment.error}`;
    judgmentOutput.appendChild(banner);
  }
}

function renderResults(results, judgment) {
  resultsGrid.innerHTML = "";

  const winningModel = judgment && judgment.winner ? judgment.winner : null;

  results.forEach(function (result) {
    const isWinner = winningModel !== null && result.model === winningModel;

    const card = document.createElement("div");
    card.className =
      "model-card" +
      (result.error ? " model-card--error" : "") +
      (isWinner ? " model-card--winner" : "");

    const title = document.createElement("h3");
    title.textContent = result.model;
    if (isWinner) {
      const badge = document.createElement("span");
      badge.className = "winner-badge";
      badge.textContent = "Winner";
      title.appendChild(badge);
    }
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
  judgmentOutput.innerHTML = "";
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
    renderJudgment(data.judgment);
    renderResults(data.results, data.judgment);
  } catch (err) {
    responseOutput.textContent = `Error: could not reach the backend (${err}).`;
  } finally {
    submitButton.disabled = false;
  }
});
