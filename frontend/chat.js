/**
 * chat.js — AgentRAG Chat Page
 *
 * Responsibilities:
 *  - PDF upload via POST /upload  → session management
 *  - Chat messages via POST /chat → streaming-like UX
 *  - Session reset via POST /reset
 *  - UI state machine: idle → uploading → ready → chatting
 *  - Typing indicator, agent badge toggling
 *  - Example prompts, clear chat, error handling, toast notifications
 *  - Auto-growing textarea, keyboard shortcuts
 */

"use strict";

/* ============================================================
   Config
   ============================================================ */
const API_BASE = "http://localhost:8000";

/* ============================================================
   State
   ============================================================ */
const state = {
  sessionId:  null,
  pdfInfo:    null,
  filename:   null,
  isReady:    false,   // PDF processed, can chat
  isWaiting:  false,   // Waiting for agent reply
  messages:   [],      // { role, content, agent? }
};

/* ============================================================
   DOM refs
   ============================================================ */
const $uploadArea      = document.getElementById("upload-area");
const $fileInput       = document.getElementById("pdf-file-input");
const $uploadIcon      = document.getElementById("upload-icon");
const $uploadText      = document.getElementById("upload-text");
const $uploadHint      = document.getElementById("upload-hint");
const $uploadProgress  = document.getElementById("upload-progress");
const $progressText    = document.getElementById("progress-text");
const $progressFill    = document.getElementById("progress-bar-fill");
const $progressTrack   = document.getElementById("progress-bar-track");
const $docCard         = document.getElementById("doc-card");
const $docCardName     = document.getElementById("doc-card-name");
const $docCardInfo     = document.getElementById("doc-card-info");
const $docCardReset    = document.getElementById("doc-card-reset");
const $badgePdf        = document.getElementById("badge-pdf");
const $badgeWeb        = document.getElementById("badge-web");
const $messagesArea    = document.getElementById("messages-area");
const $emptyState      = document.getElementById("empty-state");
const $chatInput       = document.getElementById("chat-input");
const $sendBtn         = document.getElementById("send-btn");
const $clearBtn        = document.getElementById("clear-chat-btn");
const $lockedHint      = document.getElementById("input-locked-hint");
const $toast           = document.getElementById("toast");

/* ============================================================
   Toast
   ============================================================ */
let toastTimer = null;

function showToast(msg, type = "info", duration = 3500) {
  $toast.textContent   = msg;
  $toast.className     = `toast toast-${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $toast.classList.remove("show");
  }, duration);
}

/* ============================================================
   UI state helpers
   ============================================================ */

function setAgentBadge(agent) {
  // agent: "pdf" | "web" | null
  $badgePdf.classList.toggle("active", agent === "pdf");
  $badgeWeb.classList.toggle("active", agent === "web");
}

function setInputEnabled(enabled) {
  $chatInput.disabled = !enabled;
  $sendBtn.disabled   = !enabled;
  $lockedHint.classList.toggle("visible", !enabled && !state.isReady);
}

function showProgress(visible, text = "Processing PDF…", pct = null) {
  $uploadProgress.classList.toggle("visible", visible);
  $progressText.textContent = text;

  if (pct !== null) {
    $progressFill.style.width = `${pct}%`;
    $progressTrack.setAttribute("aria-valuenow", pct);
  }
}

function showDocCard(visible) {
  $docCard.classList.toggle("visible", visible);
  $uploadArea.style.display = visible ? "none" : "";
}

function fakeProgress(onDone) {
  // Animate the progress bar while the server works.
  // Quickly goes to ~80 %, then stalls until onDone is called.
  let pct = 0;
  const steps = [
    { target: 25, delay: 300,  label: "Loading PDF…" },
    { target: 55, delay: 900,  label: "Chunking & embedding…" },
    { target: 78, delay: 1600, label: "Building vector index…" },
    { target: 80, delay: 500,  label: "Almost ready…" },
  ];

  let i = 0;
  function next() {
    if (i >= steps.length) return;
    const step = steps[i++];
    setTimeout(() => {
      showProgress(true, step.label, step.target);
      next();
    }, step.delay);
  }
  next();

  return {
    complete(label = "System ready! ✅") {
      showProgress(true, label, 100);
      setTimeout(onDone, 600);
    },
    fail() {
      showProgress(false);
    }
  };
}

/* ============================================================
   Message rendering
   ============================================================ */

function hideEmptyState() {
  if ($emptyState) $emptyState.style.display = "none";
}

function createMsgEl({ role, content, agent = null, isTyping = false, isError = false }) {
  const isUser = role === "user";

  const msgEl = document.createElement("div");
  msgEl.className = "msg" + (isUser ? " user-msg" : "");

  const avatarEl = document.createElement("div");
  avatarEl.className = "msg-avatar";
  avatarEl.setAttribute("aria-hidden", "true");
  avatarEl.textContent = isUser ? "👤" : "🤖";

  const wrapEl = document.createElement("div");

  const bubbleEl = document.createElement("div");
  bubbleEl.className = "msg-bubble";

  if (isTyping) {
    bubbleEl.className += " typing-bubble";
    bubbleEl.innerHTML =
      '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  } else if (isError) {
    bubbleEl.className += " error-bubble";
    bubbleEl.textContent = content;
  } else {
    // Sanitise and render markdown-ish (bold only for simplicity)
    bubbleEl.innerHTML = simpleMarkdown(content);
  }

  wrapEl.appendChild(bubbleEl);

  if (!isUser && agent && !isTyping) {
    const tagEl = document.createElement("div");
    tagEl.className = "msg-agent-tag";
    const emoji = agent === "pdf" ? "📄 PDF Agent — FAISS + BM25" : "🌐 Web Agent — Tavily";
    tagEl.textContent = emoji;
    wrapEl.appendChild(tagEl);
  }

  msgEl.appendChild(avatarEl);
  msgEl.appendChild(wrapEl);

  return { msgEl, bubbleEl };
}

function appendMessage(opts) {
  hideEmptyState();
  const { msgEl } = createMsgEl(opts);
  $messagesArea.appendChild(msgEl);
  scrollToBottom();
  return msgEl;
}

function scrollToBottom() {
  $messagesArea.scrollTop = $messagesArea.scrollHeight;
}

function simpleMarkdown(text) {
  // Minimal safe rendering: bold, code, newlines → <br>
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br />");
}

/* ============================================================
   Upload flow
   ============================================================ */

async function handleFileSelected(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showToast("Only PDF files are supported.", "error");
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast("File is too large. Max 50 MB.", "error");
    return;
  }

  // Reset previous session if any
  if (state.sessionId) {
    await resetSession(false); // silent reset
  }

  // Show progress
  showDocCard(false);
  showProgress(true, "Uploading…", 5);

  const progressCtrl = fakeProgress(() => {
    // Called when server responds
  });

  const formData = new FormData();
  formData.append("file", file);

  let data;
  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body:   formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed." }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    data = await res.json();
  } catch (e) {
    progressCtrl.fail();
    showProgress(false);
    showToast(`Upload failed: ${e.message}`, "error", 5000);
    return;
  }

  progressCtrl.complete("System ready! ✅");

  // Update state
  state.sessionId = data.session_id;
  state.pdfInfo   = data.pdf_info;
  state.filename  = data.filename;
  state.isReady   = true;

  // Update doc card
  $docCardName.textContent = data.filename;
  $docCardInfo.textContent = data.pdf_info || "No summary available.";

  setTimeout(() => {
    showProgress(false);
    showDocCard(true);
    setInputEnabled(true);
    $lockedHint.classList.remove("visible");
    setAgentBadge(null);
    showToast(`✅ "${data.filename}" is ready!`, "success");
    $chatInput.focus();
  }, 700);
}

/* ── Drag & drop ── */
$uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  $uploadArea.classList.add("drag-over");
});

$uploadArea.addEventListener("dragleave", () => {
  $uploadArea.classList.remove("drag-over");
});

$uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  $uploadArea.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelected(file);
});

$fileInput.addEventListener("change", () => {
  if ($fileInput.files[0]) handleFileSelected($fileInput.files[0]);
});

$uploadArea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    $fileInput.click();
  }
});

/* ============================================================
   Reset / new PDF
   ============================================================ */

async function resetSession(showUi = true) {
  if (state.sessionId) {
    try {
      await fetch(`${API_BASE}/reset`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ session_id: state.sessionId }),
      });
    } catch (_) { /* best-effort */ }
  }

  state.sessionId = null;
  state.pdfInfo   = null;
  state.filename  = null;
  state.isReady   = false;
  state.messages  = [];

  if (showUi) {
    showDocCard(false);
    showProgress(false);
    clearMessages();
    setInputEnabled(false);
    setAgentBadge(null);
    $lockedHint.classList.add("visible");
    $fileInput.value = "";
    showToast("Session cleared. Upload a new PDF.", "info");
  }
}

$docCardReset.addEventListener("click", () => resetSession(true));

/* ============================================================
   Chat
   ============================================================ */

async function sendMessage(text) {
  if (!text.trim() || state.isWaiting || !state.isReady) return;

  const content = text.trim();
  $chatInput.value = "";
  autoResize();

  // Add user bubble
  appendMessage({ role: "user", content });
  state.messages.push({ role: "user", content });

  // Show typing indicator
  state.isWaiting = true;
  setInputEnabled(false);
  setAgentBadge(null);

  const typingEl = appendMessage({ role: "assistant", isTyping: true });

  let data;
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        session_id: state.sessionId,
        message:    content,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Agent error." }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    data = await res.json();
  } catch (e) {
    typingEl.remove();
    appendMessage({ role: "assistant", content: `⚠️ Error: ${e.message}`, isError: true });
    state.isWaiting = false;
    setInputEnabled(true);
    $chatInput.focus();
    showToast(`Error: ${e.message}`, "error", 5000);
    return;
  }

  // Remove typing indicator
  typingEl.remove();

  // Detect which agent was used by inspecting the reply (heuristic from state)
  // The API doesn't currently expose agent name, so we guess from keywords.
  // For a future improvement, the backend could return { reply, agent }.
  const reply     = data.reply || "(no reply)";
  const agentUsed = guessAgent(content, reply);

  setAgentBadge(agentUsed);
  appendMessage({ role: "assistant", content: reply, agent: agentUsed });
  state.messages.push({ role: "assistant", content: reply, agent: agentUsed });

  state.isWaiting = false;
  setInputEnabled(true);
  $chatInput.focus();
}

/** Very simple heuristic to guess which agent answered */
function guessAgent(query, reply) {
  const webKeywords = ["according to", "search", "found online", "web", "internet",
                       "latest", "news", "recent", "currently", "http", "source:"];
  const lower = (query + " " + reply).toLowerCase();
  return webKeywords.some(k => lower.includes(k)) ? "web" : "pdf";
}

/* ── Send button / Enter key ── */
$sendBtn.addEventListener("click", () => sendMessage($chatInput.value));

$chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage($chatInput.value);
  }
});

/* ── Auto-grow textarea ── */
function autoResize() {
  $chatInput.style.height = "auto";
  $chatInput.style.height = Math.min($chatInput.scrollHeight, 140) + "px";
}

$chatInput.addEventListener("input", autoResize);

/* ============================================================
   Clear chat
   ============================================================ */

function clearMessages() {
  // Remove all message elements, but keep the empty-state div
  const msgs = $messagesArea.querySelectorAll(".msg");
  msgs.forEach(m => m.remove());

  if ($emptyState) $emptyState.style.display = "";
  state.messages = [];
}

$clearBtn.addEventListener("click", () => {
  clearMessages();
  showToast("Chat cleared.", "info", 2000);
});

/* ============================================================
   Example prompts
   ============================================================ */

document.querySelectorAll(".example-prompt").forEach((btn) => {
  btn.addEventListener("click", () => {
    const prompt = btn.dataset.prompt;
    if (!state.isReady) {
      showToast("Please upload a PDF first!", "error");
      return;
    }
    $chatInput.value = prompt;
    autoResize();
    sendMessage(prompt);
  });
});

/* ============================================================
   Initial UI state
   ============================================================ */
setInputEnabled(false);
$lockedHint.classList.add("visible");
setAgentBadge(null);
