/**
 * AgentRAG Frontend — app.js
 * Handles: demo chat, upload zone interaction, agent badge toggling,
 * typing animation reveal, nav scroll effects.
 */

/* ============================================================
   Demo Chat Messages (for the preview section)
   ============================================================ */
const DEMO_RESPONSES = [
  {
    text: "That question is best answered from the web! Let me search Tavily for you… 🌐",
    tag: "🌐 Web Agent — Tavily Search",
    agent: "web",
  },
  {
    text: "According to the document, the hybrid retrieval approach combines dense (FAISS) and sparse (BM25) methods to maximise recall and precision simultaneously.",
    tag: "📄 PDF Agent — FAISS + BM25",
    agent: "pdf",
  },
  {
    text: "I found 3 relevant passages in your PDF. The key insight is that chunk size and overlap significantly affect retrieval quality.",
    tag: "📄 PDF Agent — FAISS + BM25",
    agent: "pdf",
  },
  {
    text: "Searching the web now… According to recent sources, LangGraph v0.2 introduced improved streaming and persistence APIs. 🔗",
    tag: "🌐 Web Agent — Tavily Search",
    agent: "web",
  },
];

let demoResponseIndex = 0;

const chatMessages = document.getElementById("demo-chat-messages");
const chatInput    = document.getElementById("demo-chat-input");
const sendBtn      = document.getElementById("demo-send-btn");
const agentPdfBadge = document.getElementById("agent-pdf-badge");
const agentWebBadge = document.getElementById("agent-web-badge");
const typingBubble  = document.getElementById("typing-bubble");

/**
 * Appends a message bubble to the chat.
 */
function appendMessage(content, isUser = false, agentTag = null) {
  const msgEl = document.createElement("div");
  msgEl.className = "msg" + (isUser ? " user-msg" : "");
  msgEl.setAttribute("role", "listitem");

  const avatarEl = document.createElement("div");
  avatarEl.className = "msg-avatar";
  avatarEl.setAttribute("aria-hidden", "true");
  avatarEl.textContent = isUser ? "👤" : "🤖";

  const bubbleWrap = document.createElement("div");

  const bubbleEl = document.createElement("div");
  bubbleEl.className = "msg-bubble";
  bubbleEl.innerHTML = content;

  bubbleWrap.appendChild(bubbleEl);

  if (!isUser && agentTag) {
    const tagEl = document.createElement("div");
    tagEl.className = "msg-agent-tag";
    tagEl.textContent = agentTag;
    bubbleWrap.appendChild(tagEl);
  }

  msgEl.appendChild(avatarEl);
  msgEl.appendChild(bubbleWrap);

  chatMessages.appendChild(msgEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Shows typing dots, then resolves with the response after delay.
 */
function showTypingThenRespond(response) {
  return new Promise((resolve) => {
    // Re-show the typing bubble if it was hidden
    if (typingBubble) {
      typingBubble.innerHTML =
        '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
      typingBubble.closest(".msg").style.display = "";
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setTimeout(() => {
      // Hide the static typing bubble
      if (typingBubble) {
        typingBubble.closest(".msg").style.display = "none";
      }

      // Toggle active agent badge
      setActiveAgent(response.agent);

      appendMessage(response.text, false, response.tag);
      resolve();
    }, 1400);
  });
}

/**
 * Toggles the active agent badge in the sidebar.
 */
function setActiveAgent(agent) {
  if (agent === "web") {
    agentPdfBadge?.classList.remove("active");
    agentWebBadge?.classList.add("active");
  } else {
    agentWebBadge?.classList.remove("active");
    agentPdfBadge?.classList.add("active");
  }
}

/**
 * Handles sending a message in the demo chat.
 */
async function handleDemoSend() {
  const text = chatInput?.value.trim();
  if (!text) return;

  chatInput.value = "";
  sendBtn.disabled = true;

  appendMessage(text, true);

  const response = DEMO_RESPONSES[demoResponseIndex % DEMO_RESPONSES.length];
  demoResponseIndex++;

  await showTypingThenRespond(response);

  sendBtn.disabled = false;
  chatInput.focus();
}

// Attach events
sendBtn?.addEventListener("click", handleDemoSend);

chatInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleDemoSend();
  }
});

/* ============================================================
   Initial typing animation (for the demo "What's the latest news" reply)
   ============================================================ */
function resolveTypingBubble() {
  setTimeout(() => {
    if (!typingBubble) return;

    setActiveAgent("web");

    typingBubble.innerHTML =
      "According to recent sources, LangGraph just released improved <strong>streaming</strong> and <strong>persistence</strong> APIs. Agents can now checkpoint mid-workflow — great for long-running tasks! 🔗";

    const agentTag = document.createElement("div");
    agentTag.className = "msg-agent-tag";
    agentTag.textContent = "🌐 Web Agent — Tavily Search";
    typingBubble.closest(".msg").querySelector("div").appendChild(agentTag);

  }, 2500);
}

resolveTypingBubble();

/* ============================================================
   Upload Zone — Drag & Drop visual feedback
   ============================================================ */
const uploadZone = document.getElementById("demo-upload-zone");

if (uploadZone) {
  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.style.background = "var(--postit)";
    uploadZone.style.opacity = "1";
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.style.background = "";
    uploadZone.style.opacity = "";
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.style.background = "";
    uploadZone.style.opacity = "1";
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      uploadZone.innerHTML = `<span class="upload-zone-icon">✅</span><strong>${file.name}</strong><br/><small>Ready to initialize</small>`;
    }
  });

  uploadZone.addEventListener("click", () => {
    uploadZone.innerHTML = `<span class="upload-zone-icon">✅</span><strong>document.pdf</strong><br/><small>Ready to initialize</small>`;
  });

  uploadZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      uploadZone.click();
    }
  });
}

/* ============================================================
   Nav scroll shadow
   ============================================================ */
const nav = document.querySelector(".nav");

window.addEventListener("scroll", () => {
  if (window.scrollY > 10) {
    nav?.classList.add("nav--scrolled");
  } else {
    nav?.classList.remove("nav--scrolled");
  }
}, { passive: true });

/* ============================================================
   Intersection Observer — fade-in on scroll
   ============================================================ */
const observerTargets = document.querySelectorAll(
  ".feature-card, .step-card, .tech-pill, .stat-item"
);

const fadeObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.animation = "fadeSlideUp 0.45s ease forwards";
        fadeObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

observerTargets.forEach((el) => {
  el.style.opacity = "0";
  fadeObserver.observe(el);
});

/* ============================================================
   Smooth scroll for anchor links
   ============================================================ */
document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (e) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});
