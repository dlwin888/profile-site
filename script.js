const btn = document.getElementById("themeBtn");
const root = document.documentElement;

btn.addEventListener("click", () => {
  const isDark = root.getAttribute("data-theme") === "dark";
  root.setAttribute("data-theme", isDark ? "light" : "dark");
});

document.getElementById("year").textContent = new Date().getFullYear();

// ===== 文字实验室 =====
const labInput = document.getElementById("labInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const labResult = document.getElementById("labResult");

function analyzeText(text) {
  const trimmed = text.trim();
  const charCount = text.length;
  const charNoSpace = text.replace(/\s/g, "").length;
  const wordCount = trimmed ? trimmed.split(/\s+/).length : 0;
  // 中文字符数（粗略统计）
  const chineseCount = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const reversed = [...text].reverse().join("");

  return {
    charCount,
    charNoSpace,
    wordCount,
    chineseCount,
    reversed,
  };
}

function renderResult(data) {
  labResult.innerHTML = `
    <dl>
      <dt>总字符数</dt><dd>${data.charCount}</dd>
      <dt>不含空格</dt><dd>${data.charNoSpace}</dd>
      <dt>词数</dt><dd>${data.wordCount}</dd>
      <dt>中文字数</dt><dd>${data.chineseCount}</dd>
      <dt>反转结果</dt><dd>${escapeHtml(data.reversed)}</dd>
    </dl>
  `;
  labResult.hidden = false;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

analyzeBtn.addEventListener("click", () => {
  const text = labInput.value;
  if (!text.trim()) {
    labResult.innerHTML = `<p>请输入一些文字再分析。</p>`;
    labResult.hidden = false;
    return;
  }
  const result = analyzeText(text);
  renderResult(result);
});

clearBtn.addEventListener("click", () => {
  labInput.value = "";
  labResult.hidden = true;
  labInput.focus();
});