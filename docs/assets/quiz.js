document.querySelectorAll("[data-quiz]").forEach((box) => {
  const correct = box.dataset.correct;
  box.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const right = btn.dataset.choice === correct;
      box.querySelectorAll("button").forEach((b) => {
        b.disabled = true;
        b.dataset.state = b.dataset.choice === correct ? "right" : "wrong";
      });
      const out = box.querySelector(".feedback");
      out.textContent = right ? "Yes." : "No. Use 0.03 + 0.50 × this year’s premium.";
      out.className = "feedback " + (right ? "ok" : "bad");
    });
  });
});
