/**
 * FinAssist - AI Chatbot Interface Controller
 * Handles conversation rendering, user message submission, typing indicators, quick prompt pills, and history management.
 */

document.addEventListener('DOMContentLoaded', () => {
  initChatbotUI();
});

function initChatbotUI() {
  const triggerBtn = document.getElementById('btn-open-chatbot');
  const drawer = document.getElementById('chat-drawer');
  const closeBtn = document.getElementById('btn-close-chat');
  const sendBtn = document.getElementById('btn-send-chat');
  const chatInput = document.getElementById('chat-input-field');
  const messagesContainer = document.getElementById('chat-messages-container');
  const clearBtn = document.getElementById('btn-clear-chat');

  if (triggerBtn && drawer) {
    triggerBtn.addEventListener('click', () => {
      drawer.classList.toggle('active');
      if (drawer.classList.contains('active')) {
        loadChatHistory();
        chatInput.focus();
      }
    });
  }

  if (closeBtn && drawer) {
    closeBtn.addEventListener('click', () => drawer.classList.remove('active'));
  }

  if (sendBtn && chatInput) {
    sendBtn.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (confirm("Clear all chat history?")) {
        try {
          await fetch('/api/chat/history', { method: 'DELETE' });
          if (messagesContainer) messagesContainer.innerHTML = '';
          appendAiBubble("Chat history cleared. How can I help you today?");
        } catch (err) {
          console.error("Error clearing chat:", err);
        }
      }
    });
  }

  // Handle Quick Prompt Pills
  document.querySelectorAll('.chat-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      if (chatInput) {
        chatInput.value = pill.textContent;
        sendChatMessage();
      }
    });
  });
}

async function loadChatHistory() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;
  
  try {
    const res = await fetch('/api/chat/history');
    const json = await res.json();
    if (json.success && json.history.length > 0) {
      container.innerHTML = '';
      json.history.forEach(msg => {
        if (msg.sender === 'user') {
          appendUserBubble(msg.message, msg.created_at);
        } else {
          appendAiBubble(msg.message, msg.created_at);
        }
      });
    } else if (container.children.length === 0) {
      appendAiBubble("Hello! I am FinAssist AI. Ask me about loans, customer balances, today's collections, or interest calculations!");
    }
  } catch (err) {
    console.error("Error loading chat history:", err);
  }
}

async function sendChatMessage() {
  const chatInput = document.getElementById('chat-input-field');
  const message = chatInput.value.trim();
  if (!message) return;

  chatInput.value = '';
  appendUserBubble(message);

  // Show loading indicator
  const loadingId = showChatLoading();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message })
    });
    const json = await res.json();
    removeChatLoading(loadingId);

    if (json.success) {
      appendAiBubble(json.response);
    } else {
      appendAiBubble(`Sorry, an error occurred: ${json.error || 'Failed to process response.'}`);
    }
  } catch (err) {
    removeChatLoading(loadingId);
    appendAiBubble(`Network error: Unable to connect to FinAssist server.`);
  }
}

function appendUserBubble(text, timeStr = null) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const time = timeStr ? new Date(timeStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble chat-bubble-user';
  bubble.innerHTML = `
    <div>${escapeHtml(text)}</div>
    <div style="font-size: 0.7rem; opacity: 0.7; text-align: right; margin-top: 4px;">${time}</div>
  `;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function appendAiBubble(markdownText, timeStr = null) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const time = timeStr ? new Date(timeStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble chat-bubble-ai';

  const htmlContent = simpleMarkdownToHtml(markdownText);

  bubble.innerHTML = `
    <div>${htmlContent}</div>
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; font-size: 0.7rem; color: var(--text-muted);">
      <span>${time}</span>
      <button onclick="copyToClipboard(this)" data-text="${escapeHtml(markdownText)}" style="background: none; border: none; color: var(--accent-indigo); cursor: pointer; font-size: 0.75rem; font-weight: 600;">Copy</button>
    </div>
  `;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function showChatLoading() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return null;

  const loadingId = 'loading-' + Date.now();
  const bubble = document.createElement('div');
  bubble.id = loadingId;
  bubble.className = 'chat-bubble chat-bubble-ai';
  bubble.innerHTML = `
    <div style="display: flex; gap: 5px; align-items: center; padding: 5px 0;">
      <span class="dot" style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; animation: pulse 1s infinite alternate;"></span>
      <span class="dot" style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; animation: pulse 1s infinite alternate 0.3s;"></span>
      <span class="dot" style="width: 8px; height: 8px; background: var(--text-muted); border-radius: 50%; animation: pulse 1s infinite alternate 0.6s;"></span>
    </div>
  `;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return loadingId;
}

function removeChatLoading(loadingId) {
  if (!loadingId) return;
  const el = document.getElementById(loadingId);
  if (el) el.remove();
}

function copyToClipboard(btn) {
  const text = btn.getAttribute('data-text');
  if (text) {
    navigator.clipboard.writeText(text);
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = orig, 2000);
  }
}

function simpleMarkdownToHtml(md) {
  if (!md) return '';
  let html = md
    .replace(/^### (.*$)/gim, '<h3 style="font-size: 1rem; font-weight: 700; color: var(--accent-emerald); margin-top: 8px; margin-bottom: 4px;">$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4 style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary); margin-top: 6px; margin-bottom: 2px;">$1</h4>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '• $1<br/>')
    .replace(/\n\n/g, '<br/><br/>');
  return html;
}
