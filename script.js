const btn = document.getElementById("themeBtn");
const root = document.documentElement;

btn.addEventListener("click", () => {
  const isDark = root.getAttribute("data-theme") === "dark";
  root.setAttribute("data-theme", isDark ? "light" : "dark");
});

document.getElementById("year").textContent = new Date().getFullYear();