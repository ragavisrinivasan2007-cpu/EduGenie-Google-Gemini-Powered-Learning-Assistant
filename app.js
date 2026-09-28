const $ = (id) => document.getElementById(id);

function showResult(element, content, type = "") {
  element.className = `result show ${type}`.trim();
  element.innerHTML = content;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showLoading(element) {
  showResult(element, "EduGenie is thinking...");
  element.classList.add("loading");
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || data.error || `Request failed (${response.status})`);
  }

  return data;
}

function setButtonBusy(form, busy) {
  const button = form.querySelector("button[type='submit']");
  if (!button) return;

  if (busy) {
    button.dataset.originalText = button.textContent;
    button.textContent = "Working...";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || "Submit";
    button.disabled = false;
  }
}

$("qaForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = $("qaResult");
  const question = $("question").value.trim();

  showLoading(result);
  setButtonBusy(form, true);

  try {
    const data = await request(`/qna?question=${encodeURIComponent(question)}`);
    showResult(result, escapeHtml(data.answer));
  } catch (error) {
    showResult(result, escapeHtml(error.message), "error");
  } finally {
    setButtonBusy(form, false);
  }
});

$("explainForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = $("explanationResult");
  const topic = $("topic").value.trim();

  showLoading(result);
  setButtonBusy(form, true);

  try {
    const data = await request("/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    showResult(result, escapeHtml(data.explanation));
  } catch (error) {
    showResult(result, escapeHtml(error.message), "error");
  } finally {
    setButtonBusy(form, false);
  }
});

$("summaryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = $("summaryResult");
  const text = $("summaryText").value.trim();

  showLoading(result);
  setButtonBusy(form, true);

  try {
    const data = await request("/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    showResult(result, escapeHtml(data.summary));
  } catch (error) {
    showResult(result, escapeHtml(error.message), "error");
  } finally {
    setButtonBusy(form, false);
  }
});

$("quizForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = $("quizResult");
  const text = $("quizText").value.trim();
  const questionCount = Number($("questionCount").value);

  showLoading(result);
  setButtonBusy(form, true);

  try {
    const data = await request("/quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, question_count: questionCount }),
    });

    renderQuiz(result, data.questions);
  } catch (error) {
    showResult(result, escapeHtml(error.message), "error");
  } finally {
    setButtonBusy(form, false);
  }
});

function renderQuiz(result, questions) {
  const html = questions.map((item, index) => {
    const options = item.options.map((option, optionIndex) => `
      <label class="quiz-option">
        <input type="radio" name="question-${index}" value="${escapeHtml(option)}">
        ${escapeHtml(option)}
      </label>
    `).join("");

    return `
      <div class="quiz-question" data-question="${index}">
        <h4>Q${index + 1}. ${escapeHtml(item.question)}</h4>
        ${options}
        <button type="button" class="check-answer">Check Answer</button>
        <div class="quiz-feedback"></div>
        <div class="answer-explanation" hidden>${escapeHtml(item.explanation)}</div>
      </div>
    `;
  }).join("");

  showResult(result, html);

  result.querySelectorAll(".check-answer").forEach((button) => {
    button.addEventListener("click", () => {
      const questionBox = button.closest(".quiz-question");
      const selected = questionBox.querySelector("input:checked");
      const feedback = questionBox.querySelector(".quiz-feedback");
      const explanation = questionBox.querySelector(".answer-explanation");
      const questionIndex = Number(questionBox.dataset.question);
      const correctAnswer = questions[questionIndex].answer;

      if (!selected) {
        feedback.className = "quiz-feedback incorrect";
        feedback.textContent = "Please select an option.";
        return;
      }

      if (selected.value === correctAnswer) {
        feedback.className = "quiz-feedback correct";
        feedback.textContent = "Correct! ✓";
      } else {
        feedback.className = "quiz-feedback incorrect";
        feedback.textContent = `Not quite. Correct answer: ${correctAnswer}`;
      }

      explanation.hidden = false;
    });
  });
}

$("learnForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const result = $("learnResult");
  const topic = $("learnTopic").value.trim();

  showLoading(result);
  setButtonBusy(form, true);

  try {
    const data = await request(`/learn/recommendations?topic=${encodeURIComponent(topic)}`);
    renderLearningPath(result, data);
  } catch (error) {
    showResult(result, escapeHtml(error.message), "error");
  } finally {
    setButtonBusy(form, false);
  }
});

function renderLearningPath(result, data) {
  const steps = data.steps.map((step) => `
    <div class="learning-step">
      <h4>${escapeHtml(step.level)}</h4>
      <p>Estimated time: ${escapeHtml(step.estimated_time)}</p>
      <strong>Key topics</strong>
      <ul>
        ${step.key_topics.map((topic) => `<li>${escapeHtml(topic)}</li>`).join("")}
      </ul>
      <strong>Resources</strong>
      <ul>
        ${step.resources.map((resource) => `<li>${escapeHtml(resource)}</li>`).join("")}
      </ul>
    </div>
  `).join("");

  const tips = data.adaptive_tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("");

  showResult(result, `
    <div class="learning-overview">
      <strong>${escapeHtml(data.topic)}</strong>
      <p>${escapeHtml(data.overview)}</p>
    </div>
    ${steps}
    <div class="learning-step">
      <h4>Adaptive tips</h4>
      <ul>${tips}</ul>
    </div>
  `);
}

async function loadHealth() {
  const status = $("healthStatus");

  try {
    const data = await request("/health");
    const mode = data.demo_mode ? "Demo mode" : "Live Gemini";
    status.textContent = `Backend: ${data.status} • ${mode} • ${data.model}`;
  } catch {
    status.textContent = "Backend unavailable";
  }
}

loadHealth();
