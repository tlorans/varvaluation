function nextPremium(thisYear) {
  return 0.03 + 0.5 * thisYear;
}

document.querySelectorAll("[data-next-premium]").forEach((box) => {
  const input = box.querySelector("input");
  const out = box.querySelector(".feedback");
  const go = () => {
    const x = Number(input.value) / 100;
    if (!Number.isFinite(x)) {
      out.textContent = "";
      return;
    }
    const y = nextPremium(x);
    out.textContent = "Next year’s expected premium: " + (100 * y).toFixed(1) + "%";
    out.className = "feedback ok";
  };
  box.querySelector("button").addEventListener("click", go);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") go();
  });
});
