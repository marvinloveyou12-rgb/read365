// HuggingFace Space 백엔드 API 주소
const API_URL = "https://dongle0516-read365.hf.space";

const QUICK_QUESTIONS = [
  "독서로 회원가입 방법",
  "DLS 인증은 어떻게 하나요?",
  "독후활동 작성 방법",
  "대출불가 오류 해결",
  "독서이음활동이란?",
  "나이스 자동 연동 되나요?",
  "아이디 비밀번호 분실",
  "학교관리자 로그인 방법",
  "독서활동 PDF 출력 방법",
  "손글씨 독후감 업로드 방법",
];

// ── 빠른 질문 버튼 생성 ─────────────────────────────────────────────────────
const quickBtns = document.getElementById("quickBtns");
QUICK_QUESTIONS.forEach((q) => {
  const btn = document.createElement("button");
  btn.textContent = q;
  btn.onclick = () => sendMessage(q);
  quickBtns.appendChild(btn);
});

// ── 메시지 추가 ─────────────────────────────────────────────────────────────
function addMessage(role, text, sources = [], sourceTags = []) {
  const container = document.getElementById("messages");

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "👤" : "🤖";

  const right = document.createElement("div");

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  right.appendChild(bubble);

  // 출처 태그 (봇 메시지에만, 항상 표시)
  if (role === "bot" && sourceTags.length > 0) {
    const tagRow = document.createElement("div");
    tagRow.className = "source-tags";
    sourceTags.forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.textContent = tag;
      tagRow.appendChild(chip);
    });
    right.appendChild(tagRow);
  }

  // 참고 문서 토글 (봇 메시지에만)
  if (role === "bot" && sources.length > 0) {
    const toggle = document.createElement("div");
    toggle.className = "sources-toggle";
    toggle.textContent = "▶ 참고 문서 원문 보기";

    const box = document.createElement("div");
    box.className = "sources-box";
    sources.forEach((s, i) => {
      const p = document.createElement("p");
      p.textContent = `${i + 1}. ${s}...`;
      box.appendChild(p);
    });

    toggle.onclick = () => {
      const open = box.style.display === "block";
      box.style.display = open ? "none" : "block";
      toggle.textContent = open ? "▶ 참고 문서 원문 보기" : "▼ 참고 문서 닫기";
    };

    right.appendChild(toggle);
    right.appendChild(box);
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(right);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;

  return wrapper;
}

// ── 로딩 표시 ───────────────────────────────────────────────────────────────
function addTyping() {
  const container = document.getElementById("messages");
  const wrapper = document.createElement("div");
  wrapper.className = "message bot typing";
  wrapper.id = "typing";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  [1, 2, 3].forEach(() => {
    const dot = document.createElement("div");
    dot.className = "dot";
    bubble.appendChild(dot);
  });

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typing");
  if (el) el.remove();
}

// ── 메시지 전송 ─────────────────────────────────────────────────────────────
async function sendMessage(quickText) {
  const input = document.getElementById("userInput");
  const btn   = document.getElementById("sendBtn");

  const message = quickText || input.value.trim();
  if (!message) return;

  input.value = "";
  input.style.height = "auto";
  btn.disabled = true;

  addMessage("user", message);
  addTyping();

  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `서버 오류 (${res.status})`);
    }

    const data = await res.json();
    removeTyping();
    addMessage("bot", data.answer, data.sources || [], data.source_tags || []);
  } catch (e) {
    removeTyping();
    addMessage(
      "bot",
      `⚠️ 오류가 발생했습니다: ${e.message}\n\n잠시 후 다시 시도해 주세요.`
    );
  } finally {
    btn.disabled = false;
    input.focus();
  }
}

// ── 입력창 Enter 키 처리 ────────────────────────────────────────────────────
document.getElementById("userInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// ── 입력창 자동 높이 조절 ───────────────────────────────────────────────────
document.getElementById("userInput").addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = Math.min(this.scrollHeight, 120) + "px";
});
