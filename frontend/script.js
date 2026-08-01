// Frontend behavior for the LLM Judge Tool.
//
// Submitting the form sends the prompt to the backend's /api/generate
// endpoint and displays the real model response (or a clear error message
// if something goes wrong).

const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt-input");
const responseOutput = document.getElementById("response-output");
const submitButton = document.getElementById("submit-button");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  const prompt = promptInput.value.trim();

  if (!prompt) {
    return;
  }

  submitButton.disabled = true;
  responseOutput.textContent = "Loading...";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await res.json();

    if (!res.ok) {
      responseOutput.textContent = `Error: ${data.error || "Something went wrong."}`;
    } else {
      responseOutput.textContent = data.response;
    }
  } catch (err) {
    responseOutput.textContent = `Error: could not reach the backend (${err}).`;
  } finally {
    submitButton.disabled = false;
  }
});

