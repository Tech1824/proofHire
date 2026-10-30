import cytoscape from 'cytoscape';
import * as API from '../lib/api.js';

const app = document.querySelector('#app');
const savedTheme = localStorage.getItem('proofhire-theme');
document.documentElement.dataset.theme = savedTheme ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
const state = {
  route: 'jobs', health: null, jobs: [], 
  selectedJobId: localStorage.getItem('proofhire-job') || 'job_1', 
  candidateId: localStorage.getItem('proofhire-cand') || null,
  task: null, 
  submissionId: localStorage.getItem('proofhire-sub') || null, 
  sessionId: localStorage.getItem('proofhire-session') || null, 
  turn: null, answerResult: null, chatHistory: [],
  candidate: JSON.parse(localStorage.getItem('proofhire-cand-data')) || null, 
  user: JSON.parse(localStorage.getItem('proofhire-user')) || (localStorage.getItem('proofhire-cand') ? { id: localStorage.getItem('proofhire-cand'), name: 'Arjun Mehta', role: 'candidate' } : null),
  error: ''
};

function getRoutes() {
  return [
    ['jobs', '01', 'Jobs'], 
    ['candidate', '02', state.candidateId ? 'Profile' : 'Sign In'], 
    ['task', '03', 'Task'],
    ['depth', '04', 'Depth check'], 
    ['shortlist', '05', state.candidateId ? 'My Results' : 'Shortlist'], 
    ['graph', '06', 'Graph']
  ];
}

const routes = getRoutes();

function setCandidateAuth(cand, user = null, subId = null, sessId = null) {
  if (cand) {
    state.candidateId = cand.candidate_id;
    state.candidate = cand;
    state.user = user || { id: cand.candidate_id, name: cand.name, email: cand.email, role: 'candidate' };
    localStorage.setItem('proofhire-cand', cand.candidate_id);
    localStorage.setItem('proofhire-cand-data', JSON.stringify(cand));
    localStorage.setItem('proofhire-user', JSON.stringify(state.user));
    if (subId) {
      state.submissionId = subId;
      localStorage.setItem('proofhire-sub', subId);
    }
    if (sessId) {
      state.sessionId = sessId;
      localStorage.setItem('proofhire-session', sessId);
    }
  } else {
    state.candidateId = null;
    state.candidate = null;
    state.user = null;
    state.submissionId = null;
    state.sessionId = null;
    state.turn = null;
    state.answerResult = null;
    state.chatHistory = [];
    localStorage.removeItem('proofhire-cand');
    localStorage.removeItem('proofhire-cand-data');
    localStorage.removeItem('proofhire-user');
    localStorage.removeItem('proofhire-sub');
    localStorage.removeItem('proofhire-session');
  }
  renderRoute();
}

function showGlobalLoader(message = 'Processing...') {
  let overlay = document.querySelector('.global-loader-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'global-loader-overlay';
    overlay.innerHTML = `<div class="loader-spinner"></div><div class="loader-message"></div>`;
    document.body.appendChild(overlay);
  }
  overlay.querySelector('.loader-message').textContent = message;
  overlay.classList.add('active');
}

function hideGlobalLoader() {
  const overlay = document.querySelector('.global-loader-overlay');
  if (overlay) overlay.classList.remove('active');
}

// Escapes backend text before it is placed into HTML.
function escapeHTML(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

// Returns a compact status label for health checks.
function statusClass(value) {
  return value === 'ok' ? 'online' : 'offline';
}

// Converts a confidence percentage into a plain-language label.
function confidenceDescription(scorePercent) {
  if (scorePercent >= 80) return 'High confidence';
  if (scorePercent >= 55) return 'Moderate confidence';
  return 'Low confidence';
}

// Builds the persistent navigation and workspace frame.
function shell(content) {
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', document.documentElement.dataset.theme === 'dark' ? '#06070A' : '#F5F7FF');
  const active = state.route;
  const currentRoutes = getRoutes();
  const pageLabel = currentRoutes.find(([key]) => key === active)?.[2] ?? 'Jobs';
  const selectedJob = state.jobs.find((job) => job.job_id === state.selectedJobId);
  const workspaceRoutes = currentRoutes.filter(([key]) => ['jobs', 'candidate', 'shortlist'].includes(key));
  const assessmentRoutes = currentRoutes.filter(([key]) => ['task', 'depth', 'graph'].includes(key));
  const renderNavItem = ([key, number, label]) => `<a href="#${key}" class="nav-link ${active === key ? 'active' : ''}" title="${label}" data-tooltip="${label}"><span class="nav-icon" aria-hidden="true">${({ jobs: '▦', candidate: '👤', task: '≡', depth: '◉', shortlist: '★', graph: '⌘' })[key] || '●'}</span><span class="nav-label">${label}</span></a>`;
  
  const action = ({ 
    jobs: ['#candidate', state.candidateId ? 'My Profile' : 'Sign In / Apply'], 
    candidate: ['#task', 'Coding Task'], 
    task: ['#depth', 'Depth Check'], 
    depth: ['#shortlist', 'My Results'], 
    shortlist: ['#graph', 'Explore Graph'], 
    graph: ['#shortlist', 'My Results'] 
  })[active] || ['#jobs', 'View Roles'];

  const authWidget = state.candidateId && state.candidate ? `
    <div class="user-pill">
      <span style="color: var(--verified); font-size: 8px;">●</span>
      <span style="color: var(--muted); font-size: 10px;">CANDIDATE:</span>
      <strong style="color: var(--text);">${escapeHTML(state.candidate.name)}</strong>
      <button id="switch-account-btn" style="background: var(--card); border: 1px solid var(--border); border-radius: 4px; color: var(--link); cursor: pointer; font-size: 10px; padding: 2px 6px; margin-left: 4px;">Sign Out</button>
    </div>` : `
    <a href="#candidate" class="button button-quiet" style="border: 1px solid var(--border); font-size: 11px; padding: 4px 10px;">🔑 Sign In / Register</a>`;

  const recruiterWidget = `
    <a href="http://localhost:8000/portal/dashboard.html" target="_blank" class="button button-quiet" style="border: 1px solid var(--border); font-size: 11px; padding: 4px 10px; display: inline-flex; align-items: center; gap: 5px; color: var(--text);" title="Access hiring manager pipeline, jobs, and evaluations">
      🏢 Recruiter Portal ↗
    </a>`;

  const collapsed = localStorage.getItem('proofhire-sidebar-collapsed') === 'true';
  app.innerHTML = `
    <div class="app-frame ${collapsed ? 'sidebar-collapsed' : ''}">
      <aside class="sidebar" aria-label="Workspace navigation">
        <div class="sidebar-brand-row"><a class="brand" href="#jobs" aria-label="ProofHire home"><img class="brand-symbol" src="/proofhire-logo.svg" alt="" aria-hidden="true"><span class="brand-name">PROOFHIRE</span></a><button class="sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Collapse navigation" title="Collapse navigation">‹</button></div>
        <nav class="sidebar-nav" aria-label="Main navigation">
          <div class="nav-group"><span class="nav-group-label">Candidate Desk</span>${workspaceRoutes.map(renderNavItem).join('')}</div>
          <div class="nav-group"><span class="nav-group-label">Assessment</span>${assessmentRoutes.map(renderNavItem).join('')}</div>
        </nav>
        <div class="sidebar-bottom"><span class="sidebar-system-label">SYSTEM MODE</span><button class="mode-switch" id="mode-switch" type="button" title="Switch between local mock data and the API"><i class="switch-dot"></i><span>${API.usesMocks() ? 'Demo mode' : 'Live API'}</span></button></div>
      </aside>
      <div class="workspace">
      <header class="topbar">
        <div class="breadcrumb"><a href="#jobs">ProofHire</a><span aria-hidden="true">›</span><span style="color: var(--muted); font-size: 11px;">Candidate Desk</span><span aria-hidden="true">›</span><strong>${pageLabel}</strong>${selectedJob ? `<span aria-hidden="true">›</span><span class="breadcrumb-role">${escapeHTML(selectedJob.title)}</span>` : ''}</div>
        <label class="role-switcher"><span>Role</span><select id="role-switcher" aria-label="Selected role">${state.jobs.map((job) => `<option value="${escapeHTML(job.job_id)}" ${job.job_id === state.selectedJobId ? 'selected' : ''}>${escapeHTML(job.title)}</option>`).join('')}</select></label>
        <div class="topbar-right">
          ${authWidget}
          ${recruiterWidget}
          <span class="mode-badge ${API.usesMocks() ? 'demo' : 'live'}"><i class="status-dot ${API.usesMocks() ? 'caution' : 'verified'}"></i>${API.usesMocks() ? 'Demo' : 'Live'}</span>
          <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme" title="Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme">${document.documentElement.dataset.theme === 'dark' ? '☀' : '☾'}</button>
          <a class="button button-primary topbar-action" href="${action[0]}">${action[1]} <span aria-hidden="true">↗</span></a>
        </div>
      </header>
      <main class="main-content">${content}</main>
      <footer class="app-footer"><span>PROOFHIRE <b id="app-version">${escapeHTML(state.health?.version ?? '0.1.0')}</b></span><span class="footer-center">UNDERSTANDING OVER POLISH</span><span class="health-line"><i class="status-dot ${statusClass(state.health?.status)}"></i>API ${escapeHTML(state.health?.status ?? 'checking')}</span></footer>
      </div>
    </div>`;
  app.querySelectorAll('.recommendation').forEach((badge) => {
    const recommendation = badge.textContent.trim().toLowerCase().replaceAll('_', ' ');
    badge.textContent = `Suggested: ${recommendation === 'no' ? 'needs stronger evidence' : recommendation}`;
  });
  app.querySelectorAll('.candidate-meta span:nth-child(2)').forEach((confidence) => {
    const percent = Number(confidence.textContent.match(/\d+/)?.[0] ?? 0);
    confidence.textContent = `${confidenceDescription(percent)} · ${percent}%`;
  });
  document.querySelector('#mode-switch')?.addEventListener('click', toggleMode);
  document.querySelector('#theme-toggle')?.addEventListener('click', toggleTheme);
  document.querySelector('#switch-account-btn')?.addEventListener('click', (e) => {
    e.preventDefault();
    setCandidateAuth(null);
    location.hash = '#candidate';
  });
  document.querySelector('#sidebar-toggle')?.addEventListener('click', () => {
    const isCollapsed = app.querySelector('.app-frame').classList.toggle('sidebar-collapsed');
    localStorage.setItem('proofhire-sidebar-collapsed', String(isCollapsed));
  });
  document.querySelector('#role-switcher')?.addEventListener('change', (event) => {
    state.selectedJobId = event.target.value;
    localStorage.setItem('proofhire-job', state.selectedJobId);
    state.task = null;
    renderRoute();
  });
}

// Switches themes and saves the user's preference.
function toggleTheme() {
  const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = nextTheme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', nextTheme === 'dark' ? '#06070A' : '#F5F7FF');
  localStorage.setItem('proofhire-theme', nextTheme);
  const button = document.querySelector('#theme-toggle');
  button.textContent = nextTheme === 'dark' ? '☀' : '☾';
  button.setAttribute('aria-label', `Switch to ${nextTheme === 'dark' ? 'light' : 'dark'} theme`);
  button.title = `Switch to ${nextTheme === 'dark' ? 'light' : 'dark'} theme`;
  if (state.route === 'graph') renderRoute();
}

// Renders a consistent loading state while a page request is in flight.
function showLoading(label = 'Loading workspace') {
  shell(`<section class="page-heading"><div><div class="eyebrow">PROOFHIRE / ${state.route.toUpperCase()}</div><h1>${escapeHTML(label)}<span class="cursor">_</span></h1></div></section><div class="loading-panel"><span class="loading-line"></span><span>REQUESTING LOCAL DATA</span></div>`);
}

// Renders a useful error state and keeps a retry action available.
function showError(error) {
  state.error = error?.message ?? String(error);
  const isDoneError = state.error.toLowerCase().includes('already done') || state.error.toLowerCase().includes('completed');
  shell(`<section class="page-heading"><div><div class="eyebrow">REQUEST INTERRUPTED</div><h1>Could not load this view</h1></div></section><section class="error-panel"><span class="error-mark">!</span><div><h2>Connection error</h2><p>${escapeHTML(state.error)}</p><div style="display: flex; gap: 12px; margin-top: 14px; flex-wrap: wrap;"><button class="button button-quiet" id="retry">↻ Retry</button>${isDoneError ? `<button class="button button-primary" id="reset-session-btn">Start fresh session ↻</button><a class="button button-outline" href="#shortlist">Review Shortlist →</a>` : ''}</div></div></section>`);
  document.querySelector('#retry')?.addEventListener('click', renderRoute);
  document.querySelector('#reset-session-btn')?.addEventListener('click', () => {
    state.sessionId = null;
    localStorage.removeItem('proofhire-session');
    state.chatHistory = [];
    state.turn = null;
    state.answerResult = null;
    renderRoute();
  });
}

// Builds the compact heading used by each workspace view.
function heading(index, title, subtitle, action = '') {
  return `<section class="page-heading"><div><div class="eyebrow">FIELD NOTES / ${index}</div><h1>${title}</h1><p class="page-subtitle">${subtitle}</p></div>${action}</section>`;
}

// Renders the active page from the URL hash.
async function renderRoute() {
  state.route = location.hash.replace('#', '') || 'jobs';
  if (!routes.some(([key]) => key === state.route)) state.route = 'jobs';
  state.error = '';
  showLoading(({ jobs: 'Loading open roles', candidate: 'Preparing candidate intake', task: 'Loading task desk', depth: 'Opening depth check', shortlist: 'Loading shortlist', graph: 'Building knowledge graph' })[state.route]);
  try {
    if (!state.health) state.health = await API.getHealth();
    if (!state.jobs.length) state.jobs = (await API.listJobs()).jobs;
    if (state.route === 'jobs') await renderJobs();
    if (state.route === 'candidate') renderCandidate();
    if (state.route === 'task') renderTask();
    if (state.route === 'depth') await renderDepth();
    if (state.route === 'shortlist') await renderShortlist();
    if (state.route === 'graph') await renderGraph();
  } catch (error) {
    showError(error);
  }
}

// Draws the available jobs and their evidence-oriented next actions.
async function renderJobs() {
  const jobs = state.jobs;
  const cards = await Promise.all(jobs.map(async (job, index) => {
    const detail = await API.getJob(job.job_id);
    const metaHtml = [detail.company, detail.seniority + ' track', detail.salary, detail.location, detail.work_mode, detail.employment_type, detail.years_experience ? `${detail.years_experience}+ Yrs Exp` : null].filter(Boolean).map(item => escapeHTML(item)).join(' <span class="separator">/</span> ');
    const respHtml = (detail.responsibilities && detail.responsibilities.length) ? `<div style="margin-top: 12px; font-size: 13px; color: #94a3b8;"><strong>RESPONSIBILITIES:</strong><ul style="margin: 4px 0 0 16px; padding: 0;">${detail.responsibilities.map(r => `<li>${escapeHTML(r)}</li>`).join('')}</ul></div>` : '';
    return `<article class="job-row"><div class="job-index">0${index + 1}</div><div class="job-main"><div class="job-company">${metaHtml}</div><h2>${escapeHTML(detail.title)}</h2><p>${escapeHTML(detail.description)}</p>${respHtml}<div class="skill-list" style="margin-top: 12px;">${detail.required_skills.map((skill) => `<span class="skill-tag">${escapeHTML(skill)}</span>`).join('')}</div></div><div class="job-metrics"><span class="metric-label">ASSESSMENT</span><strong>Technical Challenge</strong><span class="metric-meta">DYNAMIC TASK · CODE + DEPTH</span><button class="button button-primary open-job" data-job="${escapeHTML(detail.job_id)}">Apply / Start Challenge <span>↗</span></button></div></article>`;
  }));
  shell(`${heading('01 / CANDIDATE DESK', 'Open Positions<span class="heading-dot">.</span>', 'Browse active requisitions, review verified technical requirements, and start your evidence-backed assessment.', '<a class="button button-primary" href="#candidate">' + (state.candidateId ? 'My Profile 👤' : 'Sign In / Apply ↗') + '</a>')}
    <div class="section-rail"><span>ACTIVE POSITIONS</span><span>${String(jobs.length).padStart(2, '0')} OPEN REQUISITIONS <i class="status-dot online"></i></span></div>
    <section class="jobs-list">${cards.length ? cards.join('') : '<div class="empty-state">No roles active right now.</div>'}</section>
    <section class="bottom-strip"><div class="strip-sign">↳</div><div><strong>PROOF OF UNDERSTANDING OVER RÉSUMÉS</strong><p>Your actual code implementation and depth conversations become your verified hiring record.</p></div><a href="#shortlist" class="text-link">View My Results <span>→</span></a></section>`);
  document.querySelectorAll('.open-job').forEach((button) => button.addEventListener('click', () => {
    state.selectedJobId = button.dataset.job;
    localStorage.setItem('proofhire-job', state.selectedJobId);
    location.hash = '#task';
  }));
}

// Draws candidate profile, 1-click demo switcher, and registration forms.
function renderCandidate() {
  const isRegistered = Boolean(state.candidateId);
  const prior = state.candidate;
  const urlParams = new URLSearchParams(window.location.search);
  const githubToken = urlParams.get('github_token') || prior?.github_token || '';

  if (!isRegistered) {
    // Candidate Desk Onboarding & Demo Sign In
    shell(`${heading('02 / CANDIDATE DESK', 'Candidate Sign In & Registration<span class="heading-dot">.</span>', 'ProofHire verifies candidate capability through real project code and work-linked depth checks. Choose a demo profile or register to begin.')}
      <div class="auth-tabs-nav">
        <button class="auth-tab-btn active" id="tab-demo-btn" type="button">⚡ 1-Click Demo Profiles</button>
        <button class="auth-tab-btn" id="tab-reg-btn" type="button">＋ Create Candidate Profile</button>
      </div>

      <div id="pane-demo">
        <div style="margin-bottom: 14px; font-size: 13px; color: var(--muted);">Select a realistic pre-seeded candidate profile to inspect live evaluations, resume in-progress interviews, or review scoring evidence:</div>
        <div class="demo-candidates-grid">
          <div class="demo-cand-card">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: var(--text);">Arjun Mehta</strong>
                <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(52, 216, 160, 0.15); color: var(--verified); font-weight: 600;">Rank #1 · 88/100</span>
              </div>
              <p style="font-size: 12px; color: var(--muted); margin: 0 0 12px 0;">Senior Fullstack & Distributed Systems. Completed challenge with 6 recruiter-verified evidence claims.</p>
            </div>
            <button class="button button-primary demo-login-btn" type="button" data-cand="cand_arjun" data-sub="sub_arjun_1" data-sess="sess_arjun_1" style="width: 100%;">Sign in as Arjun (Shortlisted) ↗</button>
          </div>

          <div class="demo-cand-card">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: var(--text);">Asha Rao</strong>
                <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(61, 90, 254, 0.15); color: var(--primary); font-weight: 600;">Rank #2 · 72/100</span>
              </div>
              <p style="font-size: 12px; color: var(--muted); margin: 0 0 12px 0;">Backend Python Developer. Clean data structures, solid sliding window implementation with depth answers.</p>
            </div>
            <button class="button button-outline demo-login-btn" type="button" data-cand="cand_asha" data-sub="sub_asha_1" data-sess="sess_asha_1" style="width: 100%;">Sign in as Asha (Interview) ↗</button>
          </div>

          <div class="demo-cand-card">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: var(--text);">Rohan Verma</strong>
                <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(255, 138, 30, 0.15); color: var(--amber); font-weight: 600;">In Progress (Turn 3/5)</span>
              </div>
              <p style="font-size: 12px; color: var(--muted); margin: 0 0 12px 0;">Junior Backend applicant. Has saved submission draft and 3 completed depth turns ready to resume.</p>
            </div>
            <button class="button button-outline demo-login-btn" type="button" data-cand="cand_rohan" data-sub="sub_rohan_1" data-sess="sess_rohan_1" style="width: 100%;">Resume as Rohan (In-Progress) ↗</button>
          </div>

          <div class="demo-cand-card">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: var(--text);">Ravi Kumar</strong>
                <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(239, 68, 68, 0.15); color: #ef4444; font-weight: 600;">Score: 39/100 · Rejected</span>
              </div>
              <p style="font-size: 12px; color: var(--muted); margin: 0 0 12px 0;">Junior Applicant. Demonstrates how shallow buzzwords and misconceptions are flagged by rubric.</p>
            </div>
            <button class="button button-quiet demo-login-btn" type="button" data-cand="cand_ravi" data-sub="sub_ravi_1" data-sess="sess_ravi_1" style="width: 100%;">Sign in as Ravi (Flagged) ↗</button>
          </div>
        </div>

        <div style="margin-top: 24px; padding: 18px; border: 1px solid var(--border); border-radius: 10px; background: var(--card);">
          <form id="manual-login-form" style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <label style="font-size: 12px; color: var(--muted); font-weight: 600;">OR ENTER REGISTERED CANDIDATE EMAIL / ID:</label>
            <input id="manual-login-input" placeholder="e.g. arjun.mehta@devmail.io or cand_arjun" style="flex: 1; min-width: 240px; padding: 8px 12px; border-radius: 6px; background: var(--raised); border: 1px solid var(--border); color: var(--text);" required>
            <button class="button button-primary" type="submit">Sign In ↗</button>
          </form>
          <div id="manual-login-msg" style="margin-top: 8px; font-size: 12px;"></div>
        </div>
      </div>

      <div id="pane-reg" style="display: none;">
        <div class="form-layout"><form class="terminal-form" id="candidate-form">
          <div class="form-topline"><span>NEW CANDIDATE REGISTRATION</span><span>01 — 02</span></div>
          <label>FULL NAME<input name="name" required placeholder="Asha Rao"></label>
          <div class="form-pair">
            <label>EMAIL<input name="email" type="email" required placeholder="asha@example.com"></label>
            <label>GITHUB URL <a href="http://localhost:8000/api/auth/github/login" style="font-size: 10px; margin-left: 8px; color: #3b82f6;">[Connect for Higher Limits]</a><input name="github_url" type="url" placeholder="https://github.com/username"><input type="hidden" name="github_token" value="${escapeHTML(githubToken)}"></label>
          </div>
          ${githubToken ? '<div style="color: #10b981; font-size: 11px; margin-bottom: 12px;">✓ GitHub Account Connected</div>' : ''}
          <label>LINKEDIN OR RESUME PROFILE <span class="label-note">PASTE TEXT OR UPLOAD FILE</span>
            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
              <input type="file" id="resume-upload" accept=".txt,.md,.pdf" style="font-size: 11px;">
            </div>
            <textarea name="linkedin_text" id="resume-text" rows="4" placeholder="Paste profile summary or upload a text-based resume file..."></textarea>
          </label>
          <div class="field-divider"><span>PROJECT CONTEXT</span><span>02 — 02</span></div>
          <div style="color: #64748b; font-size: 11px; padding: 12px 0;">Repositories and commits are parsed automatically into an interactive Knowledge Graph.</div>
          <div class="form-actions">
            <button class="button button-primary" type="submit">Register & Build Candidate Graph <span>↗</span></button>
          </div>
        </form>
        <aside class="side-note">
          <div class="side-note-index">CANDIDATE / NOTE 01</div>
          <div class="note-glyph">⌁</div>
          <h3>Work before words.</h3>
          <p>Project code and profile claims become connected evidence for a focused, fair depth check.</p>
          <div class="note-separator"></div>
          <div class="mini-stat"><span>DATA HANDLING</span><b>LOCAL FIRST</b></div>
        </aside>
        </div>
      </div>`);

    const tabDemo = document.querySelector('#tab-demo-btn');
    const tabReg = document.querySelector('#tab-reg-btn');
    const paneDemo = document.querySelector('#pane-demo');
    const paneReg = document.querySelector('#pane-reg');
    tabDemo?.addEventListener('click', () => {
      tabDemo.classList.add('active'); tabReg.classList.remove('active');
      paneDemo.style.display = 'block'; paneReg.style.display = 'none';
    });
    tabReg?.addEventListener('click', () => {
      tabReg.classList.add('active'); tabDemo.classList.remove('active');
      paneReg.style.display = 'block'; paneDemo.style.display = 'none';
    });

    document.querySelectorAll('.demo-login-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const candId = btn.dataset.cand;
        const subId = btn.dataset.sub;
        const sessId = btn.dataset.sess;
        btn.disabled = true;
        btn.textContent = 'Logging in...';
        try {
          const res = await API.loginUser({ email: candId, role: 'candidate' });
          if (res.candidate) {
            setCandidateAuth(res.candidate, res.user, res.submission_id || subId, res.session_id || sessId);
            location.hash = '#candidate';
          }
        } catch (err) {
          btn.textContent = 'Sign in failed';
          console.error(err);
        }
      });
    });

    document.querySelector('#manual-login-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const val = document.querySelector('#manual-login-input').value.trim();
      const msg = document.querySelector('#manual-login-msg');
      msg.textContent = 'Signing in...';
      try {
        const res = await API.loginUser({ email: val, role: 'candidate' });
        if (res.candidate) {
          setCandidateAuth(res.candidate, res.user, res.submission_id, res.session_id);
          location.hash = '#candidate';
        } else {
          msg.textContent = 'Candidate not found. Please register or select a demo profile.';
          msg.style.color = '#ef4444';
        }
      } catch (err) {
        msg.textContent = err.message || 'Login failed';
        msg.style.color = '#ef4444';
      }
    });

    document.querySelector('#resume-upload')?.addEventListener('change', (event) => {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => { document.querySelector('#resume-text').value = e.target.result; };
      reader.readAsText(file);
    });

    document.querySelector('#candidate-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const button = event.currentTarget.querySelector('[type="submit"]');
      button.disabled = true;
      button.textContent = 'Building candidate graph...';
      showGlobalLoader('Building Candidate Knowledge Graph...');
      try {
        const result = await API.createCandidate({
          name: form.get('name'), email: form.get('email'), github_url: form.get('github_url'), github_token: form.get('github_token') || undefined, linkedin_text: form.get('linkedin_text'),
          projects: []
        });
        const cand = await API.getCandidate(result.candidate_id);
        setCandidateAuth(cand, { id: cand.candidate_id, name: cand.name, email: cand.email, role: 'candidate' });
        location.hash = '#candidate';
      } catch (err) {
        showError(err);
        button.disabled = false;
        button.textContent = 'Retry Registration';
      } finally {
        hideGlobalLoader();
      }
    });

    return;
  }

  // Registered / Logged In Candidate Profile
  shell(`${heading('02 / CANDIDATE PROFILE', 'Your verified profile<span class="heading-dot">.</span>', 'Update your details, adjust claimed experience, or fetch newly uploaded GitHub projects into your Knowledge Graph.')}
    <div style="margin-bottom: 20px; padding: 12px 18px; border: 1px solid var(--border); border-radius: 8px; background: var(--raised); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
      <div>
        <span style="font-size: 11px; color: var(--muted); font-weight: 600;">ACTIVE CANDIDATE:</span> 
        <strong style="font-size: 15px; color: var(--text);">${escapeHTML(prior?.name ?? '')}</strong> 
        <code style="font-size: 11px; margin-left: 8px; padding: 2px 6px; border-radius: 4px; background: var(--card); border: 1px solid var(--border); color: var(--primary);">${escapeHTML(state.candidateId)}</code> 
        <span style="font-size: 12px; color: var(--muted); margin-left: 10px;">${escapeHTML(prior?.email ?? '')}</span>
      </div>
      <button id="profile-logout-btn" class="button button-quiet" style="font-size: 11px; padding: 4px 10px;" type="button">Switch Account / Sign Out</button>
    </div>

    <div class="form-layout"><form class="terminal-form" id="candidate-form">
      <div class="form-topline"><span>REGISTERED CANDIDATE PROFILE</span><span>${escapeHTML(state.candidateId)}</span></div>
      <label>FULL NAME<input name="name" required placeholder="Asha Rao" value="${escapeHTML(prior?.name ?? '')}"></label>
      <div class="form-pair">
        <label>EMAIL<input name="email" type="email" required placeholder="asha@example.com" value="${escapeHTML(prior?.email ?? '')}"></label>
        <label>GITHUB URL <a href="http://localhost:8000/api/auth/github/login" style="font-size: 10px; margin-left: 8px; color: #3b82f6;">[Connect for Higher Limits]</a><input name="github_url" type="url" placeholder="https://github.com/username" value="${escapeHTML(prior?.github_url ?? '')}"><input type="hidden" name="github_token" value="${escapeHTML(githubToken)}"></label>
      </div>
      ${githubToken ? '<div style="color: #10b981; font-size: 11px; margin-bottom: 12px;">✓ GitHub Account Connected</div>' : ''}
      <label>LINKEDIN OR RESUME PROFILE <span class="label-note">PASTE TEXT OR UPLOAD FILE</span>
        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
          <input type="file" id="resume-upload" accept=".txt,.md,.pdf" style="font-size: 11px;">
        </div>
        <textarea name="linkedin_text" id="resume-text" rows="4" placeholder="Paste profile summary or upload a text-based resume file...">${escapeHTML(prior?.linkedin_text ?? '')}</textarea>
      </label>
      <div class="field-divider"><span>PROJECT CONTEXT</span><span>02 — 02</span></div>
      <div style="color: #64748b; font-size: 11px; padding: 12px 0;">Repositories and commits are parsed automatically into an interactive Knowledge Graph.</div>
      <div class="form-actions" style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button class="button button-primary" type="submit">Update Details <span>✔</span></button>
        <button class="button button-outline" id="resync-github-btn" type="button">🔄 Fetch & Re-sync GitHub Projects</button>
      </div>
    </form>
    <aside class="side-note">
      <div class="side-note-index">PROFILE / NOTE 01</div>
      <div class="note-glyph">⌁</div>
      <h3>Work before words.</h3>
      <p>Project code and profile claims become connected evidence for a focused, fair depth check.</p>
      <div class="note-separator"></div>
      <div class="mini-stat"><span>DATA HANDLING</span><b>LOCAL FIRST</b></div>
      <div class="mini-stat"><span>GRAPH STATUS</span><b>${escapeHTML(prior?.graph_status ?? 'NOT BUILT')}</b></div>
      <div id="candidate-result">${prior?.graph_summary ? `<div class="result-callout"><i class="status-dot online"></i><strong>GRAPH ACTIVE</strong><span>${prior.graph_summary.nodes ?? 0} nodes · ${prior.graph_summary.edges ?? 0} edges</span><a href="#graph" style="margin-left: 8px;">View graph →</a></div>` : ''}</div>
      <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border);">
        <span style="font-size: 10px; color: var(--muted); font-weight: 600; letter-spacing: 0.05em; display: block; margin-bottom: 8px;">QUICK ASSESSMENT LINKS</span>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          <a href="#task" class="text-link" style="font-size: 12px;">→ 03 / Practical Coding Task</a>
          <a href="#depth" class="text-link" style="font-size: 12px;">→ 04 / AI Depth Check Interview</a>
          <a href="#shortlist" class="text-link" style="font-size: 12px;">→ 05 / My Evaluation & Results</a>
        </div>
      </div>
    </aside>
    </div>`);

  document.querySelector('#profile-logout-btn')?.addEventListener('click', () => {
    setCandidateAuth(null);
    location.hash = '#candidate';
  });

  document.querySelector('#resume-upload')?.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => { document.querySelector('#resume-text').value = e.target.result; };
    reader.readAsText(file);
  });

  document.querySelector('#resync-github-btn')?.addEventListener('click', async (e) => {
    e.preventDefault();
    const resyncBtn = e.currentTarget;
    resyncBtn.disabled = true;
    resyncBtn.textContent = 'Syncing GitHub...';
    const form = document.querySelector('#candidate-form');
    const githubUrl = form.querySelector('[name="github_url"]').value;
    const resultDiv = document.querySelector('#candidate-result');
    resultDiv.innerHTML = `<div class="result-callout" style="border-color: #3b82f6;"><i class="status-dot online" style="background: #3b82f6;"></i><strong style="color: #3b82f6;">FETCHING NEW REPOSITORIES & REBUILDING GRAPH...</strong><span>Connecting to GitHub API to ingest newly uploaded projects...</span></div>`;

    try {
      await API.resyncCandidateGithub(state.candidateId, { github_url: githubUrl });
      let candidate = await API.getCandidate(state.candidateId);
      while (candidate.graph_status === 'processing' || candidate.graph_status === 'pending') {
        await new Promise(r => setTimeout(r, 2500));
        candidate = await API.getCandidate(state.candidateId);
      }
      state.candidate = candidate;
      localStorage.setItem('proofhire-cand-data', JSON.stringify(candidate));
      resultDiv.innerHTML = `<div class="result-callout"><i class="status-dot online"></i><strong style="color: #10b981;">GRAPH RE-SYNC COMPLETE!</strong><span>${candidate.graph_summary?.nodes ?? 0} nodes · ${candidate.graph_summary?.edges ?? 0} edges</span><a href="#graph" style="margin-left: 8px;">Explore Graph →</a></div>`;
      resyncBtn.disabled = false;
      resyncBtn.textContent = '🔄 Fetch & Re-sync GitHub Projects';
    } catch (err) {
      resultDiv.innerHTML = `<div class="result-callout" style="border-color: #ef4444;"><strong style="color: #ef4444;">RE-SYNC FAILED</strong><span>${escapeHTML(err.message)}</span></div>`;
      resyncBtn.disabled = false;
      resyncBtn.textContent = 'Retry Re-sync';
    }
  });

  document.querySelector('#candidate-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector('[type="submit"]');
    button.disabled = true;
    button.textContent = 'Updating...';
    try {
      const updated = await API.updateCandidate(state.candidateId, {
        name: form.get('name'),
        email: form.get('email'),
        github_url: form.get('github_url'),
        linkedin_text: form.get('linkedin_text')
      });
      state.candidate = { ...state.candidate, ...updated };
      localStorage.setItem('proofhire-cand-data', JSON.stringify(state.candidate));
      button.disabled = false;
      button.textContent = 'Updated Successfully! ✔';
      setTimeout(() => { button.textContent = 'Update Details ✔'; }, 2000);
    } catch (err) {
      showError(err);
      button.disabled = false;
      button.textContent = 'Retry Update';
    }
  });
}

// Draws the active task
function renderTask() {
  const job = state.jobs.find((item) => item.job_id === state.selectedJobId) ?? state.jobs[0];
  const task = state.task;
  shell(`${heading('03 / PRACTICAL ASSESSMENT', 'Task desk<span class="heading-dot">.</span>', 'A company-specific exercise that leads into a conversation about the candidate’s own solution.', `<button class="button button-outline" id="generate-task">↻ Generate task</button>`)}
    <div class="task-layout"><section class="task-brief panel"><div class="panel-topline"><span>ASSESSMENT BRIEF</span><span class="live-tag"><i class="status-dot online"></i> ${escapeHTML(job.company)}</span></div><div class="job-select-line"><label for="job-select">ROLE</label><select id="job-select">${state.jobs.map((item) => `<option value="${escapeHTML(item.job_id)}" ${item.job_id === job.job_id ? 'selected' : ''}>${escapeHTML(item.title)} — ${escapeHTML(item.company)}</option>`).join('')}</select></div>
      ${task ? `<div class="task-heading"><div class="eyebrow">${escapeHTML(task.language)} / ${task.time_limit_min} MIN</div><h2>${escapeHTML(task.title)}</h2><p>${escapeHTML(task.brief)}</p></div><div class="requirements-title">REQUIREMENTS</div><ul class="requirement-list">${task.requirements.map((item, index) => `<li><span>0${index + 1}</span>${escapeHTML(item)}</li>`).join('')}</ul>` : '<div class="empty-state compact">Generate the role-specific task to load its brief.</div>'}
      <div class="rubric-strip"><span>RUBRIC</span><b>${task ? task.rubric.map((row) => escapeHTML(row.skill)).join(' · ') : 'Awaiting task'}</b></div></section>
      <section class="submission-panel panel"><div class="panel-topline"><span>SUBMISSION CONSOLE</span><span class="metric-meta">NO CODE EXECUTION</span></div><label class="code-label">SOLUTION SOURCE</label><textarea id="submission-code" class="code-input submission-code" spellcheck="false" placeholder="Paste the candidate's solution here...">${escapeHTML(task?.starter_code ?? '')}</textarea><label class="notes-label">CANDIDATE NOTES <span>OPTIONAL</span></label><textarea id="submission-notes" rows="3" placeholder="Approach, trade-offs, assumptions..." class="notes-input"></textarea><div class="submit-row"><span class="form-hint">${state.candidateId ? `PROFILE ${escapeHTML(state.candidateId)}` : 'No candidate profile found.'}</span><button class="button button-primary" id="submit-solution" ${task && state.candidateId ? '' : 'disabled'}>Save submission <span>↗</span></button></div><div id="submission-result"></div></section></div>`);
  document.querySelector('#job-select').addEventListener('change', (event) => { state.selectedJobId = event.target.value; localStorage.setItem('proofhire-job', state.selectedJobId); state.task = null; renderTask(); });
  document.querySelector('#generate-task').addEventListener('click', async () => {
    const button = document.querySelector('#generate-task');
    button.disabled = true;
    button.textContent = 'Generating...';
    showGlobalLoader('Generating Role-Specific Task...');
    try { state.task = await API.generateTask(state.selectedJobId); renderTask(); }
    catch (error) { showError(error); }
    finally { hideGlobalLoader(); }
  });
  document.querySelector('#submit-solution').addEventListener('click', async () => {
    if (!state.task) return;
    const button = document.querySelector('#submit-solution');
    button.disabled = true;
    button.textContent = 'Saving...';
    showGlobalLoader('Indexing Submission Code...');
    try {
      const result = await API.createSubmission({ candidate_id: state.candidateId, task_id: state.task.task_id, files: [{ path: state.task.language === 'python' ? 'limiter.py' : 'menu.js', content: document.querySelector('#submission-code').value }], notes: document.querySelector('#submission-notes').value });
      state.submissionId = result.submission_id;
      localStorage.setItem('proofhire-sub', state.submissionId);
      // Clear any old depth session tied to a previous submission
      state.sessionId = null;
      localStorage.removeItem('proofhire-session');
      state.answerResult = null;
      state.chatHistory = [];
      document.querySelector('#submission-result').innerHTML = `<div class="result-callout"><i class="status-dot online"></i><strong>SUBMISSION SAVED</strong><span>${result.stats.files} file · ${result.stats.functions} functions indexed</span><a href="#depth">Start depth check →</a></div>`;
    } catch (error) { document.querySelector('#submission-result').innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`; }
    finally { button.disabled = false; button.innerHTML = 'Save submission <span>↗</span>'; hideGlobalLoader(); }
  });
}

// Draws the chat and live evidence panel for a depth-check session.
async function renderDepth() {
  if (state.sessionId && state.chatHistory.length === 0) {
    try {
      const sess = await API.getDepthSession(state.sessionId);
      let score = 0;
      state.chatHistory = [];
      sess.turns.forEach(t => {
         state.chatHistory.push({
           kind: 'question',
           turn: { turn_number: t.turn_number, text: t.text, code_snippet: t.code_snippet, expects: t.expects, node_ref: t.node_ref, type: t.type, level: t.level }
         });
         if (t.answer_text) {
           state.chatHistory.push({
             kind: 'answer',
             answer: t.answer_text,
             evaluation: t.evaluation
           });
           score = Math.round((score * (t.turn_number - 1) + t.evaluation.score * 20) / t.turn_number);
           state.answerResult = {
             status: sess.status === 'done' || t.turn_number >= 5 ? 'done' : 'in_progress',
             evaluation: t.evaluation,
             running: { score_100: score, confidence: 0.92, dimensions: t.evaluation.dimensions },
             meta: t.meta || { context_tokens: 300, full_context_tokens: 1800 },
             next: null
           };
         }
      });
      if (sess.status === 'done') {
        state.turn = null;
        if (!state.answerResult && sess.turns.length > 0) {
          state.answerResult = { status: 'done', evaluation: sess.turns[sess.turns.length - 1].evaluation || {}, running: { score_100: score, confidence: 0.92, dimensions: {} }, meta: { context_tokens: 300, full_context_tokens: 1800 }, next: null };
        } else if (state.answerResult) {
          state.answerResult.status = 'done';
        }
      } else {
        state.turn = sess.turns[sess.turns.length - 1];
      }
    } catch (error) {
      console.error("Failed to load depth session", error);
    }
  }

  const session = state.sessionId;
  const turn = state.turn;
  const result = state.answerResult;
  const isDone = result?.status === 'done' || (!turn && session);
  shell(`${heading('04 / TECHNICAL CONVERSATION', 'Depth check<span class="heading-dot">.</span>', 'Questions follow the candidate’s own work. Scores stay attached to exact answer evidence.', session ? `<button class="button button-quiet" id="end-session">Finish session</button>` : '')}
    <div class="depth-layout"><section class="chat-panel panel"><div class="panel-topline"><span><i class="status-dot ${session ? 'online' : 'offline'}"></i> ${session ? `SESSION ${escapeHTML(session.slice(-8))}` : 'SESSION NOT STARTED'}</span><span>${turn ? `<span class="badge" style="margin-right: 8px; font-size: 10px; padding: 2px 8px;">${escapeHTML(turn.phase_label ?? (turn.turn_number <= 3 ? 'PHASE 1: PROVENANCE' : 'PHASE 2: CODE VERIFICATION'))}</span>TURN ${turn.turn_number} / 6` : 'WAITING'}</span></div>
      <div class="chat-scroll" id="chat-scroll">${session ? `<div class="chat-message system-message"><span class="message-stamp">PROOFHIRE / INTERVIEWER</span><p class="typewriter">${escapeHTML(turn?.text ?? (result?.status === 'done' ? 'Depth check complete. Your answers are ready for recruiter review.' : 'Session complete.'))}</p>${turn?.code_snippet ? `<pre class="snippet"><span>${escapeHTML(turn.code_snippet.path)}:${turn.code_snippet.start_line}</span><code>${escapeHTML(turn.code_snippet.code)}</code></pre>` : ''}</div>${result ? `<div class="chat-message answer-message"><span class="message-stamp">CANDIDATE / TURN ${result.evaluation.turn_number}</span><p>${escapeHTML(result.evaluation.evidence_quote || 'No answer provided.')}</p><span class="answer-score">SCORE ${result.evaluation.score}/5 · ${escapeHTML(result.evaluation.flags.join(', ') || 'NO FLAGS')}</span></div><div class="chat-message system-message follow-up"><span class="message-stamp">PROOFHIRE / NEXT</span><p class="typewriter">${escapeHTML(result.next?.text ?? 'Depth check complete. The evidence is ready for recruiter review.')}</p></div>` : ''}` : '<div class="chat-empty"><div class="terminal-prompt">$ depth-check --start</div><h2>Ready to test understanding.</h2><p>Start with the submitted solution, then follow the evidence one answer at a time.</p><button class="button button-primary" id="start-session">Start depth check <span>↗</span></button></div>'}</div>
      ${session && !isDone ? `<form id="answer-form" class="answer-form"><label for="candidate-answer">${turn?.expects === 'code' ? 'CODE RESPONSE' : 'YOUR RESPONSE'}</label>${turn?.expects === 'code' ? '<textarea id="candidate-answer" name="answer" class="code-input" rows="4" placeholder="Write or paste a small code change..."></textarea>' : '<textarea id="candidate-answer" name="answer" rows="3" placeholder="Explain your reasoning, referring to the submitted code..."></textarea>'}<div class="answer-controls"><span class="form-hint">ENTER TO SEND · SHIFT+ENTER FOR NEW LINE</span><button class="button button-primary" type="submit">Send answer <span>↗</span></button></div></form><div class="voice-controls" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color);"><button class="button button-outline" id="start-voice-call" type="button">🎙️ Start Voice-to-Voice Call (Alpha)</button><div id="voice-status" style="margin-top: 8px; font-size: 12px; font-family: monospace; color: var(--accent-color);"></div></div>` : session ? `<div class="session-complete"><i class="status-dot online"></i> <strong>SESSION COMPLETE</strong> · EVIDENCE SAVED<div style="margin-top: 14px; display: flex; gap: 10px; align-items: center;"><a href="#shortlist" class="button button-primary">Review in Shortlist →</a><button class="button button-quiet" id="restart-depth" type="button">Start new session ↻</button></div></div>` : ''}</section>
    <aside class="evidence-panel panel"><div class="panel-topline"><span>LIVE EVIDENCE</span><span class="evidence-lock">● VERIFIED QUOTE</span></div>${result ? `<div class="score-overview"><div><span class="metric-label">RUNNING SCORE</span><div class="score-number">${result.running.score_100}<small>/100</small></div></div><div class="confidence-block"><span class="metric-label">CONFIDENCE</span><strong>${Math.round(result.running.confidence * 100)}<small>%</small></strong></div></div><div class="ascii-bar" aria-label="Score ${result.running.score_100} out of 100">[${'█'.repeat(Math.round(result.running.score_100 / 10))}${'░'.repeat(10 - Math.round(result.running.score_100 / 10))}] ${result.running.score_100}</div><div class="evidence-quote"><div class="quote-head"><span>ANSWER ${String(result.evaluation.turn_number).padStart(2, '0')} / EVIDENCE</span><span>SCORE ${result.evaluation.score}/5</span></div><blockquote>“${escapeHTML(result.evaluation.evidence_quote || 'No evidence quote available.') }”</blockquote><p>${escapeHTML(result.evaluation.reasoning)}</p></div><div class="dimension-list">${Object.entries(result.running.dimensions).map(([name, score]) => `<div class="dimension-row"><span>${escapeHTML(name)}</span><div class="dimension-track"><i style="width:${Math.min(100, Number(score) * 20)}%"></i></div><b>${Number(score).toFixed(1)}</b></div>`).join('')}</div><div class="token-meter"><div class="token-head"><span>TOKEN SAVINGS</span><b>${Math.max(0, Math.round((1 - result.meta.context_tokens / result.meta.full_context_tokens) * 100))}% less context</b></div><div class="token-comparison"><div><span>GRAPH CONTEXT</span><b>${result.meta.context_tokens.toLocaleString()} <small>tokens</small></b></div><div><span>FULL PROJECT</span><b>${result.meta.full_context_tokens.toLocaleString()} <small>tokens</small></b></div></div><div class="token-track"><i style="width:${Math.max(4, result.meta.context_tokens / result.meta.full_context_tokens * 100)}%"></i></div></div>${result.evaluation.flags.length ? `<div class="flag-row">${result.evaluation.flags.map((flag) => `<span class="flag-tag">${escapeHTML(flag)}</span>`).join('')}</div>` : '<div class="clean-eval">NO RISK FLAGS</div>'}` : '<div class="evidence-empty"><div class="evidence-mark">[ ]</div><h3>Evidence will appear here.</h3><p>Each answer is evaluated on its own. Scores are calculated separately from the model response.</p><div class="empty-meter"><span></span></div></div>'}<div class="evidence-footer"><span>LLM IS NOT THE HIRING DECISION</span><span>HUMAN REVIEW REQUIRED</span></div></aside></div>`);
  if (session) document.querySelector('#chat-scroll').innerHTML = chatTranscript();
  document.querySelector('#start-session')?.addEventListener('click', () => beginDepth(state.submissionId));
  document.querySelector('#restart-depth')?.addEventListener('click', async () => {
    state.sessionId = null;
    localStorage.removeItem('proofhire-session');
    state.answerResult = null;
    state.chatHistory = [];
    state.turn = null;
    if (state.submissionId) {
      await beginDepth(state.submissionId);
    } else {
      await renderDepth();
    }
  });
  document.querySelector('#end-session')?.addEventListener('click', async () => { await API.finishDepth(state.sessionId); state.answerResult = { ...(state.answerResult ?? {}), status: 'done', next: null }; state.turn = null; renderDepth(); });
  document.querySelector('#answer-form')?.addEventListener('submit', sendAnswer);
  document.querySelector('#start-voice-call')?.addEventListener('click', startVoiceCall);
  const confidenceLabel = document.querySelector('.confidence-block .metric-label');
  if (confidenceLabel && result) confidenceLabel.textContent = `${result.running.confidence >= 0.8 ? 'High' : result.running.confidence >= 0.55 ? 'Moderate' : 'Low'} confidence`;
  typewriterVisible();
}

let voiceSocket = null;
let audioContext = null;
let audioProcessor = null;
let mediaStream = null;

async function startVoiceCall() {
  const btn = document.querySelector('#start-voice-call');
  const status = document.querySelector('#voice-status');
  if (voiceSocket) {
    voiceSocket.close();
    if (audioContext) audioContext.close();
    if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
    voiceSocket = null;
    audioContext = null;
    mediaStream = null;
    btn.innerHTML = '🎙️ Start Voice-to-Voice Call (Alpha)';
    status.textContent = 'Call ended.';
    return;
  }
  
  try {
    // Create AudioContext immediately inside the user click handler to satisfy browser autoplay policies
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    btn.innerHTML = '🎙️ Connecting...';
    status.textContent = 'Requesting microphone access...';
    
    // Request raw mic access
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
    
    status.textContent = 'Connecting to WebSocket...';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    voiceSocket = new WebSocket(`${wsProtocol}//127.0.0.1:8000/api/interview/stream?session_id=${state.sessionId}`);
    
    voiceSocket.onopen = async () => {
      btn.innerHTML = '⏹️ End Voice Call';
      status.textContent = 'Connected. Listening...';
      
      const source = audioContext.createMediaStreamSource(mediaStream);
      audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
      
      source.connect(audioProcessor);
      audioProcessor.connect(audioContext.destination);
      
      audioProcessor.onaudioprocess = (e) => {
        if (!voiceSocket || voiceSocket.readyState !== WebSocket.OPEN) return;
        
        const float32Data = e.inputBuffer.getChannelData(0);
        // Convert Float32 to Int16 PCM
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          let s = Math.max(-1, Math.min(1, float32Data[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Send raw PCM bytes to backend
        voiceSocket.send(int16Data.buffer);
      };
    };
    
    // We need a small queue to play chunks smoothly
    let nextPlayTime = audioContext.currentTime;
    
    voiceSocket.onmessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        if (response.serverContent && response.serverContent.modelTurn) {
          const parts = response.serverContent.modelTurn.parts;
          parts.forEach(part => {
            if (part.inlineData && part.inlineData.data) {
              const base64 = part.inlineData.data;
              const binaryString = window.atob(base64);
              const len = binaryString.length;
              const bytes = new Uint8Array(len);
              for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              
              audioContext.decodeAudioData(bytes.buffer).then(audioBuffer => {
                const source = audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(audioContext.destination);
                
                const startTime = Math.max(audioContext.currentTime, nextPlayTime);
                source.start(startTime);
                nextPlayTime = startTime + audioBuffer.duration;
              }).catch(e => {
                console.error("Audio decode error:", e);
              });
            }
          });
        }
      } catch (e) {
        console.error("Error parsing voice message:", e);
      }
    };
    
    voiceSocket.onclose = () => {
      if (audioContext) audioContext.close();
      if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
      voiceSocket = null;
      btn.innerHTML = '🎙️ Start Voice-to-Voice Call (Alpha)';
      status.textContent = 'Connection closed.';
    };
    
  } catch (err) {
    status.textContent = 'Error: ' + err.message;
    btn.innerHTML = '🎙️ Start Voice-to-Voice Call (Alpha)';
  }
}

// Renders every question and answer in the order it happened.
function chatTranscript() {
  return state.chatHistory.map((entry) => {
    if (entry.kind === 'question') {
      const snippet = entry.turn.code_snippet;
      return `<div class="chat-message system-message"><span class="message-stamp">PROOFHIRE / TURN ${entry.turn.turn_number}</span><p class="typewriter">${escapeHTML(entry.turn.text)}</p>${snippet ? `<pre class="snippet"><span>${escapeHTML(snippet.path)}:${snippet.start_line}</span><code>${escapeHTML(snippet.code)}</code></pre>` : ''}</div>`;
    }
    const evaluation = entry.evaluation;
    return `<div class="chat-message answer-message"><span class="message-stamp">CANDIDATE / TURN ${evaluation.turn_number}</span><p>${escapeHTML(entry.answer)}</p><span class="answer-score">SCORE ${evaluation.score}/5 · ${escapeHTML(evaluation.flags.join(', ') || 'NO FLAGS')}</span></div>`;
  }).join('');
}

// Starts a new session and displays its first question.
async function beginDepth(submissionId) {
  if (!submissionId) { showError("No submission found. Please complete the task first."); return; }
  showGlobalLoader('Initializing Depth Check...');
  try {
    state.sessionId = null;
    state.chatHistory = [];
    state.answerResult = null;
    state.turn = null;
    const started = await API.startDepth(submissionId);
    state.sessionId = started.session_id;
    localStorage.setItem('proofhire-session', state.sessionId);
    state.turn = started.turn;
    state.answerResult = null;
    state.chatHistory = [{ kind: 'question', turn: started.turn }];
    renderDepth();
  } catch (error) { showError(error); }
  finally { hideGlobalLoader(); }
}

// Evaluates the current answer and updates the live evidence panel.
async function sendAnswer(event) {
  event.preventDefault();
  const answerBox = document.querySelector('#candidate-answer');
  const answer = answerBox.value;
  if (!answer.trim()) { answerBox.focus(); return; }
  const button = event.currentTarget.querySelector('[type="submit"]');
  button.disabled = true;
  button.textContent = 'Evaluating...';
  showGlobalLoader('Evaluating Answer & Verifying Evidence...');
  try {
    state.answerResult = await API.submitDepthAnswer(state.sessionId, answer, state.turn?.expects === 'code' ? answer : null);
    state.chatHistory.push({ kind: 'answer', answer, evaluation: state.answerResult.evaluation });
    state.turn = state.answerResult.next;
    if (state.turn) state.chatHistory.push({ kind: 'question', turn: state.turn });
    if (state.answerResult.status === 'done') await API.finishDepth(state.sessionId);
    renderDepth();
  } catch (error) { showError(error); }
  finally { hideGlobalLoader(); }
}

// Loads and draws candidate's personal evaluation and the recruiter comparative shortlist.
async function renderShortlist() {
  const [job, list, myEval] = await Promise.all([
    API.getJob(state.selectedJobId),
    API.getShortlist(state.selectedJobId),
    state.candidateId ? API.getCandidateEvaluation(state.candidateId, state.selectedJobId).catch(() => null) : Promise.resolve(null)
  ]);

  const candidatesList = list?.candidates || [];
  
  // Render Candidate Personal Evaluation Scorecard if available
  let myScorecardHtml = '';
  if (myEval?.profile) {
    const prof = myEval.profile;
    const myEvList = prof.evidence || [];
    const mySkillProf = prof.skill_profile || prof.dims || {};
    const confirmedCount = myEvList.filter(e => e.recruiter_confirmed).length;

    myScorecardHtml = `
      <section class="evaluation-banner" style="border: 2px solid var(--border); background: var(--card); border-radius: 12px; padding: 22px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px; margin-bottom: 16px;">
          <div>
            <div style="font-size: 11px; color: var(--muted); font-weight: 600; letter-spacing: 0.05em;">YOUR VERIFIED EVALUATION SCORECARD</div>
            <h2 style="margin: 4px 0; font-size: 22px; color: var(--text);">${escapeHTML(myEval.candidate?.name || state.candidate?.name)}</h2>
            <div style="font-size: 13px; color: var(--muted);">${escapeHTML(job.title)} · ${escapeHTML(job.company)}</div>
          </div>
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <div style="text-align: right;">
              <span style="font-size: 11px; color: var(--muted); display: block;">OVERALL SCORE</span>
              <strong style="font-size: 24px; color: var(--verified);">${prof.overall_score || 0}<small style="font-size: 14px; color: var(--muted);">/100</small></strong>
            </div>
            <div style="text-align: right; padding-left: 12px; border-left: 1px solid var(--border);">
              <span style="font-size: 11px; color: var(--muted); display: block;">RANK</span>
              <strong style="font-size: 24px; color: var(--primary);">#${myEval.rank || 1}</strong>
            </div>
            <div style="text-align: right; padding-left: 12px; border-left: 1px solid var(--border);">
              <span style="font-size: 11px; color: var(--muted); display: block;">STATUS</span>
              <span class="recommendation rec-${escapeHTML(prof.recommendation || 'reviewed')}" style="font-size: 12px; margin-top: 4px; display: inline-block;">${escapeHTML((prof.recommendation || 'reviewed').replaceAll('_', ' '))}</span>
            </div>
          </div>
        </div>

        <div style="padding: 10px 14px; background: rgba(52, 216, 160, 0.1); border: 1px solid var(--verified); border-radius: 8px; margin-bottom: 16px; font-size: 12px; color: var(--verified); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
          <span>✔ <strong>Human Recruiter Audit:</strong> ${confirmedCount} of ${myEvList.length} evidence claims verified by hiring recruiter.</span>
          <span style="font-size: 11px; color: var(--text);">${Math.round((prof.confidence || 0.85) * 100)}% evaluation confidence</span>
        </div>

        <p style="font-size: 13px; color: var(--text); line-height: 1.6; margin-bottom: 16px;">${escapeHTML(prof.summary || 'Assessment record complete.')}</p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 18px;">
          <div style="padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--raised);">
            <span class="metric-label" style="margin-bottom: 8px; display: block;">KEY STRENGTHS</span>
            <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: var(--text); line-height: 1.6;">
              ${(prof.strengths || []).map(s => `<li>${escapeHTML(s)}</li>`).join('') || '<li>Consistent architectural clarity.</li>'}
            </ul>
          </div>
          <div style="padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--raised);">
            <span class="metric-label" style="margin-bottom: 8px; display: block;">SKILL PROFILE BREAKDOWN</span>
            ${Object.entries(mySkillProf).map(([skill, val]) => `
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
                <span style="color: var(--muted); text-transform: capitalize;">${escapeHTML(skill)}</span>
                <b>${Number(val).toFixed(1)} / 5.0</b>
              </div>
            `).join('')}
          </div>
        </div>

        <details class="evidence-details" style="margin-top: 12px;" open>
          <summary><span>Verified Depth Evidence Trail</span><span>${myEvList.length} SKILLS VERIFIED <b>＋</b></span></summary>
          <div class="evidence-list" style="margin-top: 14px;">
            ${myEvList.map(item => `
              <div class="evidence-card" style="margin-bottom: 12px; padding: 12px 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--raised);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <strong style="color: var(--primary); font-size: 13px;">${escapeHTML(item.skill_name || 'Technical Reasoning')}</strong>
                  <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: var(--verified-bg); color: var(--verified);">TURN ${String(item.turn_number).padStart(2, '0')} · SCORE: ${item.score}/5</span>
                </div>
                <div style="margin: 6px 0; font-size: 12px;"><b style="color: var(--primary);">Interviewer Question:</b> ${escapeHTML(item.question || 'Grounded question')}</div>
                <div style="margin: 6px 0; font-size: 12px;"><b style="color: var(--link);">Your Answer Quote:</b> <blockquote style="margin: 4px 0; padding: 6px 10px; border-left: 2px solid var(--link); font-style: italic; font-size: 11px; background: rgba(59, 130, 246, 0.05);">“${escapeHTML(item.quote || item.candidate_answer)}”</blockquote></div>
                <div style="font-size: 11px; color: var(--muted); margin-top: 6px;"><b>Rubric Analysis:</b> ${escapeHTML(item.reasoning || 'Evaluated against verified criteria.')}</div>
                <div style="margin-top: 6px; font-size: 11px; color: var(--verified); font-weight: 600;">${item.recruiter_confirmed ? '✔ Recruiter Confirmed' : 'Pending Confirmation'}</div>
              </div>
            `).join('')}
          </div>
        </details>
      </section>
    `;
  } else if (state.candidateId) {
    myScorecardHtml = `
      <div style="margin-bottom: 24px; padding: 18px; border: 1px solid var(--border); border-radius: 10px; background: var(--card);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <strong style="color: var(--text); font-size: 15px;">Assessment In Progress</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--muted);">You have not finished the full assessment for this role yet. Complete the coding task and depth check to view your scorecard.</p>
          </div>
          <div style="display: flex; gap: 8px;">
            <a href="#task" class="button button-outline" style="font-size: 12px;">Coding Task ↗</a>
            <a href="#depth" class="button button-primary" style="font-size: 12px;">Depth Check ↗</a>
          </div>
        </div>
      </div>
    `;
  }

  // Recruiter Portal Link Box
  const recruiterNotice = `
    <div style="margin: 20px 0; padding: 16px 20px; border: 1px dashed var(--border); border-radius: 10px; background: var(--raised); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div>
        <strong style="color: var(--primary); font-size: 14px;">🏢 Hiring Managers & Recruiters</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--muted);">Manage job requisitions, view company applicant pipelines, update candidate stages, and run side-by-side matrices in the dedicated portal.</p>
      </div>
      <a href="http://localhost:8000/portal/dashboard.html" target="_blank" class="button button-primary" style="font-size: 12px; padding: 6px 14px;">Open Recruiter Portal ↗</a>
    </div>
  `;

  // Candidate cards for all candidates view
  const cards = candidatesList.map((candidate) => {
    const evList = candidate.evidence || [];
    const skillProf = candidate.skill_profile || candidate.dims || {};
    const strengths = candidate.strengths || [];
    const concerns = candidate.concerns || [];
    
    return `<article class="candidate-row" data-candidate-id="${escapeHTML(candidate.candidate_id)}"><div class="rank-cell"><span>RANK</span><strong>#${candidate.rank || '-'}</strong></div><div class="candidate-overview"><div class="candidate-name-row"><h2>${escapeHTML(candidate.name)}</h2><span class="recommendation rec-${escapeHTML(candidate.recommendation || 'reviewed')}">${escapeHTML((candidate.recommendation || 'reviewed').replaceAll('_', ' '))}</span></div><div class="score-track"><i style="width:${candidate.overall_score || 0}%"></i></div><div class="candidate-meta"><span>${candidate.overall_score || 0}<small> / 100</small></span><span>${Math.round((candidate.confidence || 0.8) * 100)}% confidence</span><span>${escapeHTML(candidate.candidate_id)}</span></div>
  
  <div class="pipeline-actions" style="margin: 10px 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
    <span style="font-size: 11px; color: var(--muted); font-weight: 600;">STAGE:</span>
    <span class="stage-badge" style="padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: var(--raised); border: 1px solid var(--border); color: var(--verified);">${escapeHTML(candidate.status || 'Reviewed')}</span>
    <button class="button button-quiet status-btn" style="padding: 3px 8px; font-size: 11px;" data-cand="${escapeHTML(candidate.candidate_id)}" data-status="Shortlisted">★ Shortlist</button>
    <button class="button button-quiet status-btn" style="padding: 3px 8px; font-size: 11px;" data-cand="${escapeHTML(candidate.candidate_id)}" data-status="Interview">📅 Interview</button>
    <button class="button button-quiet status-btn" style="padding: 3px 8px; font-size: 11px;" data-cand="${escapeHTML(candidate.candidate_id)}" data-status="Rejected">✕ Reject</button>
  </div>

  <p class="candidate-summary">${escapeHTML(candidate.summary || 'Candidate assessment record active.')}</p><div class="strength-concerns"><div><span class="list-label">STRENGTH SIGNAL</span><p>${escapeHTML(strengths[0] ?? 'Consistently grounded code explanations.')}</p></div><div><span class="list-label">OPEN QUESTION</span><p>${escapeHTML(concerns[0] ?? 'No critical flags raised.')}</p></div></div><details class="evidence-details"><summary><span>Evidence Trail & Transparent Scorecard</span><span>${evList.length} SKILLS VERIFIED <b>＋</b></span></summary><div class="evidence-list">${evList.map((item) => `
    <div class="evidence-card" style="margin-bottom: 14px; padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--raised);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <strong style="color: var(--primary); font-size: 13px;">${escapeHTML(item.skill_name || 'Technical Skill')}</strong>
        <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; background: var(--verified-bg); color: var(--verified);">TURN ${String(item.turn_number).padStart(2, '0')} · SCORE: ${item.score}/5</span>
      </div>
      <div style="font-size: 11px; margin-bottom: 8px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 14px;">
        <span>📍 <b>Identified in:</b> <code style="font-size: 11px; color: var(--text);">${escapeHTML(item.where_identified || item.source_file_path || 'Submission Code')}</code></span>
        <span>📂 <b>Project/Task:</b> <strong style="color: var(--text);">${escapeHTML(item.project_or_task || 'Task Challenge')}</strong></span>
      </div>
      <div style="margin: 8px 0; padding: 8px 10px; border-left: 3px solid var(--primary); background: rgba(61, 90, 254, 0.05); font-size: 12px; border-radius: 0 4px 4px 0;">
        <b style="color: var(--primary);">Question Asked:</b> ${escapeHTML(item.question || 'Grounded technical question')}
      </div>
      <div style="margin: 8px 0; padding: 8px 10px; border-left: 3px solid var(--link); background: rgba(59, 130, 246, 0.05); font-size: 12px; border-radius: 0 4px 4px 0;">
        <b style="color: var(--link);">Candidate Answer:</b>
        <p style="margin: 4px 0 0 0; white-space: pre-wrap; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text);">${escapeHTML(item.candidate_answer || item.quote)}</p>
      </div>
      <div style="margin: 8px 0; font-size: 12px; color: var(--text);">
        <b>Evaluator Reasoning:</b> ${escapeHTML(item.reasoning || 'Evaluated against technical rubric.')}
        ${item.quote ? `<blockquote style="margin: 6px 0 0 0; padding: 6px 10px; border-left: 2px solid var(--verified); font-style: italic; font-size: 11px; color: var(--verified);">“${escapeHTML(item.quote)}”</blockquote>` : ''}
      </div>
      <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
        <span class="audit-status" style="font-size: 11px; color: var(--muted);">
          Human Review: ${item.recruiter_confirmed ? '<strong style="color: var(--verified);">✔ Recruiter Confirmed</strong>' : '<span style="color: var(--amber);">Pending Recruiter Review</span>'}
        </span>
        <button class="button button-quiet confirm-btn" style="padding: 4px 10px; font-size: 11px;" data-sess="${escapeHTML(candidate.session_id)}" data-turn="${item.turn_number}">
          ${item.recruiter_confirmed ? '✔ Confirmed' : 'Confirm Evaluation ✔'}
        </button>
      </div>
    </div>`).join('')}</div></details></div><div class="candidate-profile"><span class="metric-label">SKILL PROFILE</span>${Object.entries(skillProf).map(([skill, value]) => `<div class="profile-row"><span>${escapeHTML(skill)}</span><b>${Number(value).toFixed(1)}</b></div>`).join('')}</div></article>`;
  });

  const candOptions = candidatesList.map((c, i) => `<option value="${i}">${escapeHTML(c.name)} (#${c.rank || i+1} · ${c.overall_score || 0}/100)</option>`).join('');
  const compareTool = candidatesList.length >= 2 ? `
    <details class="compare-details" style="margin: 20px 0; padding: 18px; border: 1px solid var(--border); border-radius: 12px; background: var(--raised);">
      <summary style="cursor: pointer; font-weight: 600; color: var(--link); display: flex; justify-content: space-between; align-items: center;">
        <span>⚖️ SIDE-BY-SIDE CANDIDATE COMPARISON MATRIX</span>
        <span style="font-size: 11px; padding: 3px 8px; border-radius: 4px; background: var(--primary); color: #fff;">COMPARE <b>＋</b></span>
      </summary>
      <div style="margin-top: 18px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
          <div><label style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 6px;">CANDIDATE 1</label><select id="cmp-1" style="width: 100%; padding: 8px; border-radius: 6px; background: var(--card); border: 1px solid var(--border); color: var(--text);">${candOptions}</select></div>
          <div><label style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 6px;">CANDIDATE 2</label><select id="cmp-2" style="width: 100%; padding: 8px; border-radius: 6px; background: var(--card); border: 1px solid var(--border); color: var(--text);">${candidatesList.map((c, i) => `<option value="${i}" ${i === 1 ? 'selected' : ''}>${escapeHTML(c.name)} (#${c.rank || i+1} · ${c.overall_score || 0}/100)</option>`).join('')}</select></div>
        </div>
        <div id="compare-matrix"></div>
      </div>
    </details>` : '';

  shell(`${heading(state.candidateId ? '05 / RESULTS' : '05 / EVIDENCE REVIEW', state.candidateId ? 'My Results<span class="heading-dot">.</span>' : 'Shortlist<span class="heading-dot">.</span>', `${escapeHTML(job.title)} / ${escapeHTML(job.company)} · Ranked by evidence, not resume polish.`, '<span class="review-stamp"><i class="status-dot online"></i> HUMAN REVIEW</span>')}
    ${myScorecardHtml}
    ${recruiterNotice}
    <details class="all-applicants-details" ${state.candidateId ? '' : 'open'} style="margin-top: 16px;">
      <summary style="cursor: pointer; font-size: 13px; font-weight: 600; color: var(--link); padding: 10px 0;">
        <span>All Requisition Applicants & Comparative Pipeline (${candidatesList.length} Candidates)</span>
        <span style="font-size: 11px; margin-left: 8px; padding: 2px 6px; border-radius: 4px; background: var(--raised); border: 1px solid var(--border);">TOGGLE ▾</span>
      </summary>
      <div style="margin-top: 14px;">
        ${compareTool}
        <div class="section-rail"><span>RANKED CANDIDATES</span><span>UPDATED ${new Date(list?.generated_at || Date.now()).toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).toUpperCase()}</span></div>
        <section class="shortlist-list">${cards.length ? cards.join('') : '<div class="empty-state">No completed depth checks yet for this role.</div>'}</section>
      </div>
    </details>
    <div class="shortlist-footnote" style="margin-top: 24px;"><span>↳</span><p>Scores are computed from individual answer evaluations. Every claim links to verified quotes. Final hiring decisions remain human.</p></div>`);

  // Side-by-Side Compare Matrix Renderer
  const renderCompareMatrix = () => {
    const el1 = document.querySelector('#cmp-1');
    const el2 = document.querySelector('#cmp-2');
    const container = document.querySelector('#compare-matrix');
    if (!el1 || !el2 || !container) return;
    const c1 = candidatesList[parseInt(el1.value, 10)] || candidatesList[0];
    const c2 = candidatesList[parseInt(el2.value, 10)] || candidatesList[1];
    if (!c1 || !c2) return;

    const allSkills = Array.from(new Set([...Object.keys(c1.skill_profile || c1.dims || {}), ...Object.keys(c2.skill_profile || c2.dims || {})]));
    
    container.innerHTML = `
      <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <thead>
            <tr style="border-bottom: 2px solid var(--border); text-align: left;">
              <th style="padding: 10px; color: var(--muted); width: 25%;">DIMENSION / METRIC</th>
              <th style="padding: 10px; width: 37.5%; color: var(--primary); font-size: 15px;">${escapeHTML(c1.name)} <span class="tag" style="font-size: 11px;">#${c1.rank || 1}</span></th>
              <th style="padding: 10px; width: 37.5%; color: var(--link); font-size: 15px;">${escapeHTML(c2.name)} <span class="tag" style="font-size: 11px;">#${c2.rank || 2}</span></th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom: 1px solid var(--border);">
              <td style="padding: 10px; color: var(--muted); font-weight: 600;">Overall Score</td>
              <td style="padding: 10px; font-weight: 700; font-size: 18px; color: var(--verified);">${c1.overall_score || 0} / 100</td>
              <td style="padding: 10px; font-weight: 700; font-size: 18px; color: var(--verified);">${c2.overall_score || 0} / 100</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border);">
              <td style="padding: 10px; color: var(--muted); font-weight: 600;">Confidence</td>
              <td style="padding: 10px;">${Math.round((c1.confidence || 0.8) * 100)}%</td>
              <td style="padding: 10px;">${Math.round((c2.confidence || 0.8) * 100)}%</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border);">
              <td style="padding: 10px; color: var(--muted); font-weight: 600;">Recommendation</td>
              <td style="padding: 10px;"><span class="recommendation rec-${escapeHTML(c1.recommendation || 'reviewed')}">${escapeHTML((c1.recommendation || 'reviewed').replaceAll('_', ' '))}</span></td>
              <td style="padding: 10px;"><span class="recommendation rec-${escapeHTML(c2.recommendation || 'reviewed')}">${escapeHTML((c2.recommendation || 'reviewed').replaceAll('_', ' '))}</span></td>
            </tr>
            ${allSkills.map(skill => {
              const v1 = Number(c1.skill_profile?.[skill] ?? c1.dims?.[skill] ?? 0);
              const v2 = Number(c2.skill_profile?.[skill] ?? c2.dims?.[skill] ?? 0);
              return `
                <tr style="border-bottom: 1px solid var(--border);">
                  <td style="padding: 10px; color: var(--muted); text-transform: capitalize;">${escapeHTML(skill)}</td>
                  <td style="padding: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><b>${v1.toFixed(1)}</b><small>/ 5.0</small></div>
                    <div class="dimension-track" style="height: 6px; border-radius: 3px; background: var(--raised); overflow: hidden;"><i style="width: ${v1 * 20}%; height: 100%; display: block; background: var(--primary);"></i></div>
                  </td>
                  <td style="padding: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><b>${v2.toFixed(1)}</b><small>/ 5.0</small></div>
                    <div class="dimension-track" style="height: 6px; border-radius: 3px; background: var(--raised); overflow: hidden;"><i style="width: ${v2 * 20}%; height: 100%; display: block; background: var(--link);"></i></div>
                  </td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`;
  };

  document.querySelector('#cmp-1')?.addEventListener('change', renderCompareMatrix);
  document.querySelector('#cmp-2')?.addEventListener('change', renderCompareMatrix);
  renderCompareMatrix();

  // Pipeline Status Buttons Handler
  app.querySelectorAll('.status-btn').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const candId = btn.dataset.cand;
      const newStatus = btn.dataset.status;
      btn.disabled = true;
      try {
        await API.updateCandidateStatus(candId, newStatus);
        const card = btn.closest('.candidate-row');
        const badge = card ? card.querySelector('.stage-badge') : null;
        if (badge) {
          badge.textContent = newStatus;
          badge.style.color = newStatus === 'Rejected' ? '#ef4444' : newStatus === 'Shortlisted' ? 'var(--verified)' : 'var(--primary)';
        }
      } catch (err) {
        alert('Failed to update stage: ' + err.message);
      } finally {
        btn.disabled = false;
      }
    });
  });

  // Human Review Confirm Handler
  app.querySelectorAll('.confirm-btn').forEach((button) => {
    button.addEventListener('click', async () => {
      button.disabled = true;
      const session = button.dataset.sess;
      const turn = Number(button.dataset.turn);
      try {
        await API.confirmEvidence(session, turn, true);
        button.textContent = '✔ Confirmed';
        button.classList.add('confirmed');
        const card = button.closest('.evidence-card');
        const statusSpan = card ? card.querySelector('.audit-status') : null;
        if (statusSpan) {
          statusSpan.innerHTML = 'Human Review: <strong style="color: var(--verified);">✔ Recruiter Confirmed</strong>';
        }
      } catch (error) {
        showError(error);
        button.disabled = false;
      }
    });
  });
}

// Loads a candidate's node-link data and renders it with Cytoscape.
async function renderGraph() {
  const candidateId = state.candidateId;
  if (!candidateId) {
    shell(`${heading('06 / KNOWLEDGE GRAPH', 'Evidence Graph<span class="heading-dot">.</span>', 'Visualizing the candidate’s project architecture and profile claims.')}
      <div class="empty-state">No candidate profile loaded. Go to <a href="#candidate">Candidate Intake</a> first.</div>`);
    return;
  }
  const [candidate, graph] = await Promise.all([API.getCandidate(candidateId), API.getCandidateGraph(candidateId)]);
  state.candidate = candidate;
  const darkTheme = document.documentElement.dataset.theme === 'dark';
  const colorMap = darkTheme
    ? { candidate: '#8fa0ff', project: '#34d8a0', file: '#aeb6c2', function: '#34d8a0', class: '#8fa0ff', skill: '#ff8a1e', claim: '#ff5c7a' }
    : { candidate: '#3d5afe', project: '#0b7a5a', file: '#5d667c', function: '#0b7a5a', class: '#2a3fd6', skill: '#9a4a00', claim: '#c21e3a' };
  shell(`${heading('06 / KNOWLEDGE MAP', 'Work graph<span class="heading-dot">.</span>', 'A compact map of code, skills, and profile claims used to find relevant questions.', '<a href="#depth" class="button button-outline">Open depth check <span>↗</span></a>')}
    <div class="graph-layout"><section class="graph-panel panel"><div class="panel-topline"><span>NODE-LINK VIEW / ${escapeHTML(candidate.name)}</span><span>${graph.nodes.length} NODES · ${graph.edges.length} EDGES</span></div><div id="graph-canvas" class="graph-canvas" role="img" aria-label="Candidate project knowledge graph"></div><div class="graph-legend">${Object.entries(colorMap).map(([type, color]) => `<span><i style="--legend-color:${color}"></i>${escapeHTML(type)}</span>`).join('')}</div></section><aside class="graph-aside panel"><div class="panel-topline"><span>GRAPH SUMMARY</span><span class="live-tag"><i class="status-dot online"></i> ${escapeHTML(candidate.graph_status ?? 'ready')}</span></div><div class="graph-summary-number"><strong>${candidate.graph_summary?.nodes ?? graph.nodes.length}</strong><span>nodes indexed</span></div><div class="graph-summary-number"><strong>${candidate.graph_summary?.edges ?? graph.edges.length}</strong><span>relationships found</span></div><div class="graph-skills"><span class="metric-label">MATCHED SKILLS</span><div class="skill-list">${(candidate.graph_summary?.skills ?? []).map((skill) => `<span class="skill-tag">${escapeHTML(skill)}</span>`).join('')}</div></div><div class="token-note"><span>WHY GRAPH CONTEXT</span><p>Focused retrieval helps each question use the smallest relevant part of the candidate’s work, dramatically reducing LLM token consumption and improving speed.</p><div class="token-note-metric"><b>EFFICIENT</b><span>sample context vs full project</span></div></div></aside></div>`);
  const elements = [
    ...graph.nodes.map((node) => ({ data: { id: node.id, label: node.label, type: node.type, weight: node.weight, color: colorMap[node.type] ?? (darkTheme ? '#94a3b8' : '#64748b') } })),
    ...graph.edges.map((edge, index) => ({ data: { id: `edge-${index}`, source: edge.source, target: edge.target, label: edge.type } }))
  ];
  cytoscape({ container: document.querySelector('#graph-canvas'), elements, layout: { name: 'cose', animate: true, animationDuration: 600, padding: 64, nodeRepulsion: 15000, idealEdgeLength: 175 }, style: [
    { selector: 'node', style: { 'background-color': 'data(color)', label: 'data(label)', color: '#090e0b', 'font-family': 'Manrope, Inter, sans-serif', 'font-size': 14, 'font-weight': 700, 'text-wrap': 'wrap', 'text-max-width': 180, width: 'label', height: 'label', shape: 'round-rectangle', padding: '14px', 'border-width': 3, 'border-color': darkTheme ? '#111a2e' : '#ffffff', 'text-valign': 'center', 'text-halign': 'center', 'text-outline-width': 0 } },
    { selector: 'edge', style: { label: 'data(label)', color: darkTheme ? '#cbd5e1' : '#334155', 'font-family': 'Inter, sans-serif', 'font-size': 12, 'font-weight': 500, 'text-background-color': darkTheme ? '#111a2e' : '#ffffff', 'text-background-opacity': 0.96, 'text-background-padding': 4, 'text-border-width': 1, 'text-border-color': darkTheme ? '#243049' : '#e2e8f0', 'text-border-opacity': 1, width: 2.5, 'line-color': darkTheme ? '#64748b' : '#94a3b8', 'target-arrow-color': darkTheme ? '#94a3b8' : '#64748b', 'target-arrow-shape': 'triangle', 'arrow-scale': 1.4, 'curve-style': 'bezier', opacity: 0.95 } },
    { selector: 'node:selected', style: { 'border-color': darkTheme ? '#818cf8' : '#4338ca', 'border-width': 4, 'overlay-opacity': 0.1, 'overlay-color': darkTheme ? '#818cf8' : '#4338ca' } }
  ] });
}

// Types each visible interviewer message with a restrained terminal cadence.
function typewriterVisible() {
  document.querySelectorAll('.typewriter').forEach((element) => {
    const text = element.textContent;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    element.textContent = '';
    let index = 0;
    const timer = setInterval(() => {
      element.textContent += text[index++] ?? '';
      if (index >= text.length) clearInterval(timer);
    }, 13);
  });
}

// Switches the client between local fixtures and the live API.
async function toggleMode() {
  const nextMode = API.usesMocks() ? 'false' : 'true';
  localStorage.setItem('proofhire-mode', nextMode);
  state.health = null;
  await renderRoute();
}

// Supports quick route navigation and focusing the answer box.
function handleKeyboard(event) {
  if (event.altKey && /^[1-6]$/.test(event.key)) {
    location.hash = `#${routes[Number(event.key) - 1][0]}`;
  }
  if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    event.preventDefault();
    document.querySelector('#candidate-answer')?.focus();
  }
}

// Initializes the API status and current route.
async function initialize() {
  try { state.health = await API.getHealth(); }
  catch { state.health = { status: 'down', llm: { fast: 'down', smart: 'down', local: 'down' } }; }
  await renderRoute();
}

window.addEventListener('hashchange', renderRoute);
window.addEventListener('keydown', handleKeyboard);
initialize();