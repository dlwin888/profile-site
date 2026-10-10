const btn = document.getElementById("themeBtn");
const root = document.documentElement;

btn.addEventListener("click", () => {
  const isDark = root.getAttribute("data-theme") === "dark";
  root.setAttribute("data-theme", isDark ? "light" : "dark");
});

document.getElementById("year").textContent = new Date().getFullYear();

// ===== 文字实验室 =====
const API_BASE = "https://api.m3u8player.com.cn";

const labInput = document.getElementById("labInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const labResult = document.getElementById("labResult");

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderResult(data) {
  labResult.innerHTML = `
    <dl>
      <dt>总字符数</dt><dd>${data.char_count}</dd>
      <dt>不含空格</dt><dd>${data.char_no_space}</dd>
      <dt>词数</dt><dd>${data.word_count}</dd>
      <dt>中文字数</dt><dd>${data.chinese_count}</dd>
      <dt>反转结果</dt><dd>${escapeHtml(data.reversed_text)}</dd>
    </dl>
  `;
  labResult.hidden = false;
}

function renderError(msg) {
  labResult.innerHTML = `<p>出错了：${escapeHtml(msg)}</p>`;
  labResult.hidden = false;
}

function renderLoading() {
  labResult.innerHTML = `<p>分析中…</p>`;
  labResult.hidden = false;
}

async function analyzeOnServer(text) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
}

analyzeBtn.addEventListener("click", async () => {
  const text = labInput.value;
  if (!text.trim()) {
    renderError("请输入一些文字再分析。");
    return;
  }

  analyzeBtn.disabled = true;
  renderLoading();

  try {
    const data = await analyzeOnServer(text);
    renderResult(data);
  } catch (err) {
    renderError(`请求失败：${err.message}。请确认后端在 ${API_BASE} 运行。`);
  } finally {
    analyzeBtn.disabled = false;
  }
});

clearBtn.addEventListener("click", () => {
  labInput.value = "";
  labResult.hidden = true;
  labInput.focus();
});