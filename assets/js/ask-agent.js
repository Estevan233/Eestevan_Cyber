(function () {
  const root = document.querySelector("[data-agent-endpoint]");
  if (!root) return;

  const form = document.getElementById("ask-form");
  const textarea = document.getElementById("ask-question");
  const messages = document.getElementById("ask-messages");
  const submit = document.getElementById("ask-submit");
  const status = document.getElementById("ask-status");
  const sessionKey = "estevan-cyber-ask-session";
  const endpoint = resolveEndpoint(root.dataset.agentEndpoint || "/api/ask", root.dataset.devEndpoint);

  let sessionId = window.sessionStorage.getItem(sessionKey);
  if (!sessionId) {
    sessionId = createSessionId();
    window.sessionStorage.setItem(sessionKey, sessionId);
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const question = textarea.value.trim();
    if (!question) {
      textarea.focus();
      return;
    }

    appendMessage("user", question);
    textarea.value = "";
    setLoading(true);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId })
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "请求失败");
      }

      if (payload.session_id) {
        sessionId = payload.session_id;
        window.sessionStorage.setItem(sessionKey, sessionId);
      }

      appendMessage("assistant", payload.answer || "没有返回有效回答。", payload.sources || []);
    } catch (error) {
      appendMessage("assistant", "问答服务暂时不可用。先别急着怀疑人生，多半是 API 还没部署或密钥没配。");
    } finally {
      setLoading(false);
    }
  });

  function resolveEndpoint(configured, devEndpoint) {
    const host = window.location.hostname;
    if ((host === "localhost" || host === "127.0.0.1") && devEndpoint) {
      return devEndpoint;
    }
    return configured;
  }

  function createSessionId() {
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID();
    }
    return "web-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
  }

  function setLoading(isLoading) {
    submit.disabled = isLoading;
    textarea.disabled = isLoading;
    status.textContent = isLoading ? "检索中..." : "";
  }

  function appendMessage(role, text, sources) {
    const article = document.createElement("article");
    article.className = "ask-message ask-message--" + role;

    const bubble = document.createElement("div");
    bubble.className = "ask-message__bubble";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    bubble.appendChild(paragraph);

    if (sources && sources.length) {
      bubble.appendChild(renderSources(sources));
    }

    article.appendChild(bubble);
    messages.appendChild(article);
    messages.scrollTop = messages.scrollHeight;
  }

  function renderSources(sources) {
    const list = document.createElement("div");
    list.className = "ask-sources";

    sources.slice(0, 4).forEach(function (source) {
      const isWeb = source.source_type === "web";
      const link = document.createElement("a");
      link.className = "ask-source" + (isWeb ? " ask-source--web" : "");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener";

      const badge = document.createElement("span");
      badge.className = "ask-source__badge";
      badge.textContent = isWeb ? "🌐 网页" : "📄 笔记";

      const title = document.createElement("strong");
      title.textContent = source.title;

      const snippet = document.createElement("span");
      snippet.textContent = source.snippet;

      link.appendChild(badge);
      link.appendChild(title);
      link.appendChild(snippet);
      list.appendChild(link);
    });

    return list;
  }
})();
