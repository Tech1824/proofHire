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
  error: ''
};
const routes = [
  ['jobs', '01', 'Jobs'], ['candidate', '02', 'Candidate'], ['task', '03', 'Task'],
  ['depth', '04', 'Depth check'], ['shortlist', '05', 'Shortlist'], ['graph', '06', 'Graph']
];

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
  const pageLabel = routes.find(([key]) => key === active)?.[2] ?? 'Jobs';
  const selectedJob = state.jobs.find((job) => job.job_id === state.selectedJobId);
  const workspaceRoutes = routes.filter(([key]) => ['jobs', 'candidate', 'shortlist'].includes(key));
  const assessmentRoutes = routes.filter(([key]) => ['task', 'depth', 'graph'].includes(key));
  const renderNavItem = ([key, number, label]) => `<a href="#${key}" class="nav-link ${active === key ? 'active' : ''}" title="${label}" data-tooltip="${label}"><span class="nav-icon" aria-hidden="true">${({ jobs: '▦', candidate: '＋', task: '≡', depth: '◉', shortlist: '☷', graph: '⌘' })[key]}</span><span class="nav-label">${label}</span></a>`;
  const action = ({ jobs: ['#candidate', 'Add candidate'], candidate: ['#jobs', 'View roles'], task: ['#depth', 'Depth check'], depth: ['#shortlist', 'Review shortlist'], shortlist: ['#candidate', 'Add candidate'], graph: ['#depth', 'Depth check'] })[active];
  const collapsed = localStorage.getItem('proofhire-sidebar-collapsed') === 'true';
  app.innerHTML = `
    <div class="app-frame ${collapsed ? 'sidebar-collapsed' : ''}">
      <aside class="sidebar" aria-label="Workspace navigation">
        <div class="sidebar-brand-row"><a class="brand" href="#jobs" aria-label="ProofHire home"><img class="brand-symbol" src="/proofhire-logo.svg" alt="" aria-hidden="true"><span class="brand-name">PROOFHIRE</span></a><button class="sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Collapse navigation" title="Collapse navigation">‹</button></div>
        <nav class="sidebar-nav" aria-label="Main navigation">
          <div class="nav-group"><span class="nav-group-label">Workspace</span>${workspaceRoutes.map(renderNavItem).join('')}</div>
          <div class="nav-group"><span class="nav-group-label">Assessment</span>${assessmentRoutes.map(renderNavItem).join('')}</div>
        </nav>
        <div class="sidebar-bottom"><span class="sidebar-system-label">SYSTEM MODE</span><button class="mode-switch" id="mode-switch" type="button" title="Switch between local mock data and the API"><i class="switch-dot"></i><span>${API.usesMocks() ? 'Demo mode' : 'Live API'}</span></button></div>
      </aside>
      <div class="workspace">
      <header class="topbar">
        <div class="breadcrumb"><a href="#jobs">ProofHire</a><span aria-hidden="true">›</span><strong>${pageLabel}</strong>${selectedJob ? `<span aria-hidden="true">›</span><span class="breadcrumb-role">${escapeHTML(selectedJob.title)}</span>` : ''}</div>
        <label class="role-switcher"><span>Role</span><select id="role-switcher" aria-label="Selected role">${state.jobs.map((job) => `<option value="${escapeHTML(job.job_id)}" ${job.job_id === state.selectedJobId ? 'selected' : ''}>${escapeHTML(job.title)}</option>`).join('')}</select></label>
        <div class="topbar-right"><span class="mode-badge ${API.usesMocks() ? 'demo' : 'live'}"><i class="status-dot ${API.usesMocks() ? 'caution' : 'verified'}"></i>${API.usesMocks() ? 'Demo' : 'Live'}</span><button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme" title="Switch to ${document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'} theme">${document.documentElement.dataset.theme === 'dark' ? '☀' : '☾'}</button><a class="button button-primary topbar-action" href="${action[0]}">${action[1]} <span aria-hidden="true">↗</span></a></div>
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
  shell(`<section class="page-heading"><div><div class="eyebrow">REQUEST INTERRUPTED</div><h1>Could not load this view</h1></div></section><section class="error-panel"><span class="error-mark">!</span><div><h2>Connection error</h2><p>${escapeHTML(state.error)}</p><button class="button button-quiet" id="retry">↻ Retry</button></div></section>`);
  document.querySelector('#retry')?.addEventListener('click', renderRoute);
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
    if (state.route === 'depth') renderDepth();
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
    return `<article class="job-row"><div class="job-index">0${index + 1}</div><div class="job-main"><div class="job-company">${metaHtml}</div><h2>${escapeHTML(detail.title)}</h2><p>${escapeHTML(detail.description)}</p>${respHtml}<div class="skill-list" style="margin-top: 12px;">${detail.required_skills.map((skill) => `<span class="skill-tag">${escapeHTML(skill)}</span>`).join('')}</div></div><div class="job-metrics"><span class="metric-label">ASSESSMENT</span><strong>Technical Challenge</strong><span class="metric-meta">DYNAMIC TASK · CODE + DEPTH</span><button class="button button-outline open-job" data-job="${escapeHTML(detail.job_id)}">Open role <span>↗</span></button></div></article>`;
  }));
  shell(`${heading('01 / RECRUITER DESK', 'Open roles<span class="heading-dot">.</span>', 'Choose a role to review its practical assessment and evidence-backed shortlist.', '<a class="button button-primary" href="#candidate">＋ Candidate intake</a>')}
    <div class="section-rail"><span>ACTIVE REQUISITIONS</span><span>${String(jobs.length).padStart(2, '0')} OPEN <i class="status-dot online"></i></span></div>
    <section class="jobs-list">${cards.length ? cards.join('') : '<div class="empty-state">No roles yet. Add a role through the API to begin.</div>'}</section>
    <section class="bottom-strip"><div class="strip-sign">↳</div><div><strong>THE SIGNAL IS IN THE EXPLANATION</strong><p>Every recommendation stays connected to what a candidate actually said.</p></div><a href="#shortlist" class="text-link">View shortlist <span>→</span></a></section>`);
  document.querySelectorAll('.open-job').forEach((button) => button.addEventListener('click', () => {
    state.selectedJobId = button.dataset.job;
    localStorage.setItem('proofhire-job', state.selectedJobId);
    location.hash = '#task';
  }));
}

// Draws a candidate profile form and stores submitted project files.
function renderCandidate() {
  const prior = state.candidate;
  shell(`${heading('02 / CANDIDATE INTAKE', 'Show us the work<span class="heading-dot">.</span>', 'Add a profile and project context. LinkedIn is pasted as text; nothing is scraped.')}
    <div class="form-layout"><form class="terminal-form" id="candidate-form">
      <div class="form-topline"><span>NEW CANDIDATE RECORD</span><span>01 — 02</span></div>
      <label>FULL NAME<input name="name" required placeholder="Asha Rao" value="${escapeHTML(prior?.name ?? '')}"></label>
      <div class="form-pair"><label>EMAIL<input name="email" type="email" required placeholder="asha@example.com" value="${escapeHTML(prior?.email ?? '')}"></label><label>GITHUB URL<input name="github_url" type="url" placeholder="https://github.com/username"></label></div>
      <label>LINKEDIN PROFILE TEXT <span class="label-note">PASTE TEXT ONLY</span><textarea name="linkedin_text" rows="4" placeholder="Paste profile summary or experience here...">${escapeHTML(prior?.linkedin_text ?? '')}</textarea></label>
      <div class="field-divider"><span>PROJECT CONTEXT</span><span>02 — 02</span></div>
      <div style="color: #64748b; font-size: 11px; padding: 12px 0;">GitHub handles the rest. We will automatically fetch your top public repositories and build the graph.</div>
      <div class="form-actions"><span class="form-hint"><i class="status-dot online"></i> Builds a local knowledge graph</span><button class="button button-primary" type="submit">Build candidate graph <span>↗</span></button></div>
    </form><aside class="side-note"><div class="side-note-index">INTAKE / NOTE 01</div><div class="note-glyph">⌁</div><h3>Work before words.</h3><p>Project code and profile claims become connected evidence for a focused, fair depth check.</p><div class="note-separator"></div><div class="mini-stat"><span>DATA HANDLING</span><b>LOCAL FIRST</b></div><div class="mini-stat"><span>PROFILE SOURCE</span><b>PASTED BY USER</b></div><div id="candidate-result"></div></aside></div>`);
  document.querySelector('#candidate-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector('[type="submit"]');
    button.disabled = true;
    button.textContent = 'Building graph...';
    try {
      const result = await API.createCandidate({
        name: form.get('name'), email: form.get('email'), github_url: form.get('github_url'), linkedin_text: form.get('linkedin_text'),
        projects: []
      });
      state.candidateId = result.candidate_id;
      localStorage.setItem('proofhire-cand', state.candidateId);
      state.candidate = await API.getCandidate(result.candidate_id);
      localStorage.setItem('proofhire-cand-data', JSON.stringify(state.candidate));
      document.querySelector('#candidate-result').innerHTML = `<div class="result-callout"><i class="status-dot online"></i><strong>GRAPH READY</strong><span>${result.graph_summary.nodes} nodes · ${result.graph_summary.edges} edges</span><a href="#graph">Inspect graph →</a></div>`;
    } catch (error) {
      document.querySelector('#candidate-result').innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`;
    } finally {
      button.disabled = false;
      button.innerHTML = 'Build candidate graph <span>↗</span>';
    }
  });
}

// Draws task details and accepts a code submission for the selected job.
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
    try { state.task = await API.generateTask(state.selectedJobId); renderTask(); }
    catch (error) { showError(error); }
  });
  document.querySelector('#submit-solution').addEventListener('click', async () => {
    if (!state.task) return;
    const button = document.querySelector('#submit-solution');
    button.disabled = true;
    button.textContent = 'Saving...';
    try {
      const result = await API.createSubmission({ candidate_id: state.candidateId, task_id: state.task.task_id, files: [{ path: state.task.language === 'python' ? 'limiter.py' : 'menu.js', content: document.querySelector('#submission-code').value }], notes: document.querySelector('#submission-notes').value });
      state.submissionId = result.submission_id;
      localStorage.setItem('proofhire-sub', state.submissionId);
      document.querySelector('#submission-result').innerHTML = `<div class="result-callout"><i class="status-dot online"></i><strong>SUBMISSION SAVED</strong><span>${result.stats.files} file · ${result.stats.functions} functions indexed</span><a href="#depth">Start depth check →</a></div>`;
    } catch (error) { document.querySelector('#submission-result').innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`; }
    finally { button.disabled = false; button.innerHTML = 'Save submission <span>↗</span>'; }
  });
}

// Draws the chat and live evidence panel for a depth-check session.
function renderDepth() {
  const session = state.sessionId;
  const turn = state.turn;
  const result = state.answerResult;
  shell(`${heading('04 / TECHNICAL CONVERSATION', 'Depth check<span class="heading-dot">.</span>', 'Questions follow the candidate’s own work. Scores stay attached to exact answer evidence.', session ? `<button class="button button-quiet" id="end-session">Finish session</button>` : '')}
    <div class="depth-layout"><section class="chat-panel panel"><div class="panel-topline"><span><i class="status-dot ${session ? 'online' : 'offline'}"></i> ${session ? `SESSION ${escapeHTML(session.slice(-8))}` : 'SESSION NOT STARTED'}</span><span>${turn ? `TURN ${turn.turn_number} / 6` : 'WAITING'}</span></div>
      <div class="chat-scroll" id="chat-scroll">${session ? `<div class="chat-message system-message"><span class="message-stamp">PROOFHIRE / INTERVIEWER</span><p class="typewriter">${escapeHTML(turn?.text ?? (result?.status === 'done' ? 'Depth check complete. Your answers are ready for recruiter review.' : 'Session complete.'))}</p>${turn?.code_snippet ? `<pre class="snippet"><span>${escapeHTML(turn.code_snippet.path)}:${turn.code_snippet.start_line}</span><code>${escapeHTML(turn.code_snippet.code)}</code></pre>` : ''}</div>${result ? `<div class="chat-message answer-message"><span class="message-stamp">CANDIDATE / TURN ${result.evaluation.turn_number}</span><p>${escapeHTML(result.evaluation.evidence_quote || 'No answer provided.')}</p><span class="answer-score">SCORE ${result.evaluation.score}/5 · ${escapeHTML(result.evaluation.flags.join(', ') || 'NO FLAGS')}</span></div><div class="chat-message system-message follow-up"><span class="message-stamp">PROOFHIRE / NEXT</span><p class="typewriter">${escapeHTML(result.next?.text ?? 'Depth check complete. The evidence is ready for recruiter review.')}</p></div>` : ''}` : '<div class="chat-empty"><div class="terminal-prompt">$ depth-check --start</div><h2>Ready to test understanding.</h2><p>Start with the submitted solution, then follow the evidence one answer at a time.</p><button class="button button-primary" id="start-session">Start depth check <span>↗</span></button></div>'}</div>
      ${session && result?.status !== 'done' ? `<form id="answer-form" class="answer-form"><label for="candidate-answer">${turn?.expects === 'code' ? 'CODE RESPONSE' : 'YOUR RESPONSE'}</label>${turn?.expects === 'code' ? '<textarea id="candidate-answer" name="answer" class="code-input" rows="4" placeholder="Write or paste a small code change..."></textarea>' : '<textarea id="candidate-answer" name="answer" rows="3" placeholder="Explain your reasoning, referring to the submitted code..."></textarea>'}<div class="answer-controls"><span class="form-hint">ENTER TO SEND · SHIFT+ENTER FOR NEW LINE</span><button class="button button-primary" type="submit">Send answer <span>↗</span></button></div></form>` : session ? '<div class="session-complete"><i class="status-dot online"></i> SESSION COMPLETE · EVIDENCE SAVED</div>' : ''}</section>
    <aside class="evidence-panel panel"><div class="panel-topline"><span>LIVE EVIDENCE</span><span class="evidence-lock">● VERIFIED QUOTE</span></div>${result ? `<div class="score-overview"><div><span class="metric-label">RUNNING SCORE</span><div class="score-number">${result.running.score_100}<small>/100</small></div></div><div class="confidence-block"><span class="metric-label">CONFIDENCE</span><strong>${Math.round(result.running.confidence * 100)}<small>%</small></strong></div></div><div class="ascii-bar" aria-label="Score ${result.running.score_100} out of 100">[${'█'.repeat(Math.round(result.running.score_100 / 10))}${'░'.repeat(10 - Math.round(result.running.score_100 / 10))}] ${result.running.score_100}</div><div class="evidence-quote"><div class="quote-head"><span>ANSWER ${String(result.evaluation.turn_number).padStart(2, '0')} / EVIDENCE</span><span>SCORE ${result.evaluation.score}/5</span></div><blockquote>“${escapeHTML(result.evaluation.evidence_quote || 'No evidence quote available.') }”</blockquote><p>${escapeHTML(result.evaluation.reasoning)}</p></div><div class="dimension-list">${Object.entries(result.running.dimensions).map(([name, score]) => `<div class="dimension-row"><span>${escapeHTML(name)}</span><div class="dimension-track"><i style="width:${Math.min(100, Number(score) * 20)}%"></i></div><b>${Number(score).toFixed(1)}</b></div>`).join('')}</div><div class="token-meter"><div class="token-head"><span>TOKEN SAVINGS</span><b>${Math.max(0, Math.round((1 - result.meta.context_tokens / result.meta.full_context_tokens) * 100))}% less context</b></div><div class="token-comparison"><div><span>GRAPH CONTEXT</span><b>${result.meta.context_tokens.toLocaleString()} <small>tokens</small></b></div><div><span>FULL PROJECT</span><b>${result.meta.full_context_tokens.toLocaleString()} <small>tokens</small></b></div></div><div class="token-track"><i style="width:${Math.max(4, result.meta.context_tokens / result.meta.full_context_tokens * 100)}%"></i></div></div>${result.evaluation.flags.length ? `<div class="flag-row">${result.evaluation.flags.map((flag) => `<span class="flag-tag">${escapeHTML(flag)}</span>`).join('')}</div>` : '<div class="clean-eval">NO RISK FLAGS</div>'}` : '<div class="evidence-empty"><div class="evidence-mark">[ ]</div><h3>Evidence will appear here.</h3><p>Each answer is evaluated on its own. Scores are calculated separately from the model response.</p><div class="empty-meter"><span></span></div></div>'}<div class="evidence-footer"><span>LLM IS NOT THE HIRING DECISION</span><span>HUMAN REVIEW REQUIRED</span></div></aside></div>`);
  if (session) document.querySelector('#chat-scroll').innerHTML = chatTranscript();
  document.querySelector('#start-session')?.addEventListener('click', () => beginDepth(state.submissionId));
  document.querySelector('#end-session')?.addEventListener('click', async () => { await API.finishDepth(state.sessionId); state.answerResult = { ...(state.answerResult ?? {}), status: 'done', next: null }; state.turn = null; renderDepth(); });
  document.querySelector('#answer-form')?.addEventListener('submit', sendAnswer);
  const confidenceLabel = document.querySelector('.confidence-block .metric-label');
  if (confidenceLabel && result) confidenceLabel.textContent = `${result.running.confidence >= 0.8 ? 'High' : result.running.confidence >= 0.55 ? 'Moderate' : 'Low'} confidence`;
  typewriterVisible();
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
  try {
    const started = await API.startDepth(submissionId);
    state.sessionId = started.session_id;
    localStorage.setItem('proofhire-session', state.sessionId);
    state.turn = started.turn;
    state.answerResult = null;
    state.chatHistory = [{ kind: 'question', turn: started.turn }];
    renderDepth();
  } catch (error) { showError(error); }
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
  try {
    state.answerResult = await API.submitDepthAnswer(state.sessionId, answer, state.turn?.expects === 'code' ? answer : null);
    state.chatHistory.push({ kind: 'answer', answer, evaluation: state.answerResult.evaluation });
    state.turn = state.answerResult.next;
    if (state.turn) state.chatHistory.push({ kind: 'question', turn: state.turn });
    if (state.answerResult.status === 'done') await API.finishDepth(state.sessionId);
    renderDepth();
  } catch (error) { showError(error); }
}

// Loads and draws candidates with expandable evidence on the shortlist.
async function renderShortlist() {
  const [job, list] = await Promise.all([API.getJob(state.selectedJobId), API.getShortlist(state.selectedJobId)]);
  const cards = list.candidates.map((candidate) => `<article class="candidate-row"><div class="rank-cell"><span>RANK</span><strong>#${candidate.rank}</strong></div><div class="candidate-overview"><div class="candidate-name-row"><h2>${escapeHTML(candidate.name)}</h2><span class="recommendation rec-${escapeHTML(candidate.recommendation)}">${escapeHTML(candidate.recommendation.replaceAll('_', ' '))}</span></div><div class="score-track"><i style="width:${candidate.overall_score}%"></i></div><div class="candidate-meta"><span>${candidate.overall_score}<small> / 100</small></span><span>${Math.round(candidate.confidence * 100)}% confidence</span><span>${escapeHTML(candidate.candidate_id)}</span></div><p class="candidate-summary">${escapeHTML(candidate.summary)}</p><div class="strength-concerns"><div><span class="list-label">STRENGTH SIGNAL</span><p>${escapeHTML(candidate.strengths[0] ?? 'No strengths recorded')}</p></div><div><span class="list-label">OPEN QUESTION</span><p>${escapeHTML(candidate.concerns[0] ?? 'No concerns recorded')}</p></div></div><details class="evidence-details"><summary><span>Evidence quotes</span><span>${candidate.evidence.length} VERIFIED <b>＋</b></span></summary><div class="evidence-list">${candidate.evidence.map((item) => `<blockquote><p>“${escapeHTML(item.quote)}”</p><footer><span>${escapeHTML(item.claim)}</span><span>TURN ${String(item.turn_number).padStart(2, '0')} · ${item.score}/5</span></footer></blockquote>`).join('')}</div></details></div><div class="candidate-profile"><span class="metric-label">SKILL PROFILE</span>${Object.entries(candidate.skill_profile).map(([skill, value]) => `<div class="profile-row"><span>${escapeHTML(skill)}</span><b>${Number(value).toFixed(1)}</b></div>`).join('')}</div></article>`);
  shell(`${heading('05 / EVIDENCE REVIEW', 'Shortlist<span class="heading-dot">.</span>', `${escapeHTML(job.title)} / ${escapeHTML(job.company)} · Ranked by evidence, not resume polish.`, '<span class="review-stamp"><i class="status-dot online"></i> HUMAN REVIEW</span>')}
    <div class="section-rail"><span>RANKED CANDIDATES</span><span>UPDATED ${new Date(list.generated_at).toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).toUpperCase()}</span></div>
    <section class="shortlist-list">${cards.length ? cards.join('') : '<div class="empty-state">No completed depth checks yet. Finish a session to include a candidate here.</div>'}</section>
    <div class="shortlist-footnote"><span>↳</span><p>Scores are computed from individual answer evaluations. Every claim above links to a candidate quote. Final hiring decisions remain human.</p></div>`);
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
    { selector: 'node', style: { 'background-color': 'data(color)', label: 'data(label)', color: darkTheme ? '#e6eaf2' : '#0f172a', 'font-family': 'Manrope, Inter, sans-serif', 'font-size': 14, 'font-weight': 600, 'text-wrap': 'wrap', 'text-max-width': 145, width: 'mapData(weight, 0.4, 1, 112, 160)', height: 'mapData(weight, 0.4, 1, 62, 82)', shape: 'round-rectangle', padding: 12, 'border-width': 3, 'border-color': darkTheme ? '#111a2e' : '#ffffff', 'text-valign': 'center', 'text-halign': 'center', 'text-outline-width': 0 } },
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