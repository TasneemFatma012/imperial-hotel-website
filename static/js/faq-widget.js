(() => {
  const widget = document.querySelector(".faq-widget");
  if (!widget) return;

  const toggle = widget.querySelector(".faq-widget__toggle");
  const panel = widget.querySelector(".faq-widget__panel");
  const close = widget.querySelector(".faq-widget__close");

  const openLinkedQuestion = () => {
    const id = window.location.hash.slice(1);
    const question = id.startsWith("faq-") && document.getElementById(id);
    if (!(question instanceof HTMLDetailsElement)) return;

    question.open = true;
    question.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
      block: "center",
    });
  };

  const setOpen = (open) => {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close FAQ help" : "Open FAQ help");
    if (open) close.focus();
    else toggle.focus();
  };

  toggle.addEventListener("click", () => {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });
  close.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) setOpen(false);
  });
  document.addEventListener("click", (event) => {
    if (!panel.hidden && !widget.contains(event.target)) setOpen(false);
  });
  window.addEventListener("hashchange", openLinkedQuestion);
  openLinkedQuestion();
})();
