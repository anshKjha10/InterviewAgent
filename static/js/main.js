// ===================== UTILITIES =====================
const API = {
  async upload(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/upload-resume', { method: 'POST', body: form });
    return res.json();
  },
  async summary(resumeId) {
    const q = resumeId ? `?resume_id=${resumeId}` : '';
    const res = await fetch(`/api/resume-summary${q}`);
    return res.json();
  },
  async startInterview(interviewType, resumeId) {
    const res = await fetch('/api/mock-interview/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interview_type: interviewType, resume_id: resumeId })
    });
    return res.json();
  },
  async getFeedback(sessionId) {
    const res = await fetch(`/api/feedback?session_id=${sessionId}`);
    return res.json();
  },
  async getRoadmap(resumeId, sessionId) {
    let url = '/api/roadmap';
    const params = [];
    if (resumeId) params.push(`resume_id=${resumeId}`);
    if (sessionId) params.push(`session_id=${sessionId}`);
    if (params.length) url += '?' + params.join('&');
    const res = await fetch(url);
    return res.json();
  },
  async getSessions() {
    const res = await fetch('/api/sessions');
    return res.json();
  }
};

// ===================== STORAGE =====================
const Store = {
  set(key, val) { localStorage.setItem(`aip_${key}`, JSON.stringify(val)); },
  get(key) {
    try { return JSON.parse(localStorage.getItem(`aip_${key}`)); }
    catch { return null; }
  },
  clear(key) { localStorage.removeItem(`aip_${key}`); }
};

// ===================== TOAST =====================
function showToast(msg, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', info: '💜' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(40px)'; toast.style.transition = '0.3s'; setTimeout(() => toast.remove(), 300); }, 3500);
}

// ===================== LOADING =====================
function showLoading(text = 'Processing...') {
  let overlay = document.getElementById('loadingOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `<div class="spinner"></div><p class="loading-text" id="loadingText"></p>`;
    document.body.appendChild(overlay);
  }
  overlay.querySelector('#loadingText').textContent = text;
  overlay.classList.add('active');
}

function hideLoading() {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) overlay.classList.remove('active');
}

// ===================== NAVBAR ACTIVE STATE =====================
function setNavActive() {
  const path = window.location.pathname.replace('/', '') || 'index.html';
  document.querySelectorAll('.navbar-nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (href && (path === href || (path === '' && href === 'index.html'))) {
      a.classList.add('active');
    }
  });
}

document.addEventListener('DOMContentLoaded', setNavActive);

// ===================== SCORE COLOR =====================
function scoreColor(score) {
  if (score >= 8) return '#10b981';
  if (score >= 6) return '#f59e0b';
  return '#ef4444';
}

function scoreGrade(score) {
  if (score >= 9) return 'Excellent';
  if (score >= 7) return 'Good';
  if (score >= 5) return 'Average';
  return 'Needs Work';
}

// ===================== RENDER SCORE RING =====================
function renderScoreRing(score, maxScore = 10) {
  const pct = (score / maxScore) * 100;
  const r = 40, cx = 50, cy = 50;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = scoreColor(score);
  return `
    <div class="score-ring">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="8"
          stroke-dasharray="${dash} ${circ}" stroke-linecap="round"/>
      </svg>
      <div class="score-ring-text" style="color:${color}">
        <span>${score}</span>
        <span class="score-ring-label">/10</span>
      </div>
    </div>`;
}

// ===================== SSE ANSWER STREAM =====================
function streamAnswer({ sessionId, questionId, answer, qIndex, onEval, onChunk, onDone }) {
  fetch('/api/mock-interview/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer: answer,
      q_index: qIndex
    })
  }).then(res => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    function read() {
      reader.read().then(({ done, value }) => {
        if (done) { onDone && onDone(); return; }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        lines.forEach(line => {
          if (!line.startsWith('data: ')) return;
          const payload = line.slice(6);
          if (payload.startsWith('[EVAL]')) {
            const evalData = JSON.parse(payload.slice(6));
            onEval && onEval(evalData);
          } else if (payload.startsWith('[DONE]')) {
            const doneData = JSON.parse(payload.slice(6));
            onDone && onDone(doneData);
          } else {
            onChunk && onChunk(payload);
          }
        });
        read();
      });
    }
    read();
  });
}
