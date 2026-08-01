// Simple frontend behavior for the LLM Judge Tool.
//
// NOTE: This does NOT call the backend yet (that's a later PR). For now,
// submitting the form just displays a static placeholder response so the
// UI can be tried out end-to-end before real wiring is added.

const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt-input");
const responseOutput = document.getElementById("response-output");

form.addEventListener("submit", function (event) {
  event.preventDefault();

  const prompt = promptInput.value.trim();

  if (!prompt) {
    return;
  }

  // Placeholder behavior: display a static response referencing the
  // submitted prompt. Real backend integration will replace this in a
  // future PR.
  responseOutput.textContent =
    `(placeholder) You asked: "${prompt}"\n\n` +
    "Once the backend is connected, the best response from multiple " +
    "LLMs (as chosen by a judge model) will appear here.";
});
