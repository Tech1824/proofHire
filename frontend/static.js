(() => {
  const app = document.querySelector('#app');
  const savedTheme = localStorage.getItem('proofhire-theme');
  document.documentElement.dataset.theme = savedTheme ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const pages = [
    ['jobs', '01', 'Jobs'], ['candidate', '02', 'Candidate'], ['task', '03', 'Task'],
    ['depth', '04', 'Depth check'], ['shortlist', '05', 'Shortlist'], ['graph', '06', 'Graph']
  ];
  const data = {
    jobs: [
      { id: 'job_1', title: 'Backend Intern', company: 'FinLeaf', level: 'junior', skills: ['python', 'rest api', 'sql'], assessment: 'Build a rate limiter' },
      { id: 'job_2', title: 'Frontend Developer', company: 'PixelNest', level: 'junior', skills: ['javascript', 'html/css', 'accessibility'], assessment: 'Build an accessible menu' }
    ],
    candidates: [
      { id: 'cand_1', name: 'Asha Rao', score: 82, confidence: 78, recommendation: 'strong yes', strength: 'Explained why a sliding window beats a fixed counter.', concern: 'Did not mention thread safety.', quote: 'I remove timestamps older than the window before checking the limit.', profile: [4.2, 3.8, 4.0, 4.5, 4.0, 3.9] },
      { id: 'cand_2', name: 'Ravi Kumar', score: 39, confidence: 62, recommendation: 'no', strength: 'Communicates confidently.', concern: 'Could not explain the concurrency claim.', quote: 'I used this because it is the best practice.', profile: [2.1, 1.8, 1.7, 2.0, 1.6, 3.2] }
    ]
  };
  const state = { page: 'jobs', jobId: 'job_1', candidateId: 'cand_1', session: false, turn: 1, score: 0, quote: '', answer: '', task: false, collapsed: localStorage.getItem('proofhire-sidebar-collapsed') === 'true' };
  const escape = (text) => String(text ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);

  function header() {
    const navItem = ([id, number, label]) => `<a href="#${id}" class="nav sidebar-nav-item ${state.page === id ? 'selected' : ''}" title="${label}" data-tooltip="${label}"><span class="nav-icon" aria-hidden="true">${({ jobs: '▦', candidate: '＋', task: '≡', depth: '◉', shortlist: '☷', graph: '⌘' })[id]}</span><span class="nav-label">${label}</span></a>`;
    const workspacePages = pages.filter(([id]) => ['jobs', 'candidate', 'shortlist'].includes(id));
    const assessmentPages = pages.filter(([id]) => ['task', 'depth', 'graph'].includes(id));
    return `<aside class="sidebar" aria-label="Workspace navigation"><div class="sidebar-brand-row"><a class="brand" href="#jobs" aria-label="ProofHire home"><span class="brand-mark" aria-hidden="true">PH</span><strong>ProofHire</strong></a><button class="sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Collapse navigation" title="Collapse navigation">‹</button></div><nav class="sidebar-nav" aria-label="Main navigation"><div class="nav-group"><span class="nav-group-label">Workspace</span>${workspacePages.map(navItem).join('')}</div><div class="nav-group"><span class="nav-group-label">Assessment</span>${assessmentPages.map(navItem).join('')}</div></nav><div class="sidebar-bottom"><span class="sidebar-system-label">SYSTEM MODE</span><span class="sidebar-mode"><i></i><span>Demo mode</span></span></div></aside>`;
  }

  function topbar() {
    const activePage = pages.find(([id]) => id === state.page)?.[2] ?? 'Jobs';
    const activeJob = data.jobs.find((job) => job.id === state.jobId) ?? data.jobs[0];
    const action = ({ jobs: ['#candidate', 'Add candidate'], candidate: ['#jobs', 'View roles'], task: ['#depth', 'Depth check'], depth: ['#shortlist', 'Review shortlist'], shortlist: ['#candidate', 'Add candidate'], graph: ['#depth', 'Depth check'] })[state.page];
    const isDark = document.documentElement.dataset.theme === 'dark';
    return `<header class="topbar"><div class="breadcrumb"><a href="#jobs">ProofHire</a><span aria-hidden="true">›</span><strong>${activePage}</strong><span aria-hidden="true">›</span><span class="breadcrumb-role">${activeJob.title}</span></div><label class="role-switcher"><span>Role</span><select id="global-job-choice" aria-label="Selected role">${data.jobs.map((job) => `<option value="${job.id}" ${job.id === state.jobId ? 'selected' : ''}>${job.title}</option>`).join('')}</select></label><div class="topbar-status"><span class="mode-badge"><i></i>Demo</span><button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch to ${isDark ? 'light' : 'dark'} theme" title="Switch to ${isDark ? 'light' : 'dark'} theme">${isDark ? '☀' : '☾'}</button></div><a class="button primary topbar-action" href="${action[0]}">${action[1]} <span aria-hidden="true">↗</span></a></header>`;
  }

  function heading(section, title, copy, action = '') {
    return `<div class="page-heading"><div><div class="eyebrow">${section}</div><h1>${title}<span>.</span></h1><p>${copy}</p></div>${action}</div>`;
  }

  function jobsPage() {
    return `${heading('01 / RECRUITER DESK', 'Open roles', 'Choose a role to review its practical assessment and evidence-backed shortlist.', '<a class="button primary" href="#candidate">＋ Candidate intake</a>')}<div class="rail"><span>ACTIVE REQUISITIONS</span><span>02 OPEN <i class="live"></i></span></div>${data.jobs.map((job, index) => `<article class="job-row"><span class="index">0${index + 1}</span><div><div class="company">${job.company} <span>/</span> ${job.level} track</div><h2>${job.title}</h2><p>${job.company === 'FinLeaf' ? 'Build reliable services for a growing financial platform.' : 'Create accessible, resilient interface components for a collaboration product.'}</p><div class="tags">${job.skills.map((skill) => `<span>${skill}</span>`).join('')}</div></div><aside class="job-side"><small>ASSESSMENT</small><b>${job.assessment}</b><small>45 MIN · CODE + DEPTH</small><a class="button outline" href="#task" data-job="${job.id}">Open role <span>↗</span></a></aside></article>`).join('')}<div class="bottom-note"><span>↳</span><div><b>THE SIGNAL IS IN THE EXPLANATION</b><p>Every recommendation stays connected to what a candidate actually said.</p></div><a href="#shortlist">View shortlist →</a></div>`;
  }

  function candidatePage() {
    return `${heading('02 / CANDIDATE INTAKE', 'Show us the work', 'Add a profile and project context. LinkedIn is pasted as text; nothing is scraped.')}<div class="columns"><form class="panel form" id="candidate-form"><div class="panel-head"><span>NEW CANDIDATE RECORD</span><span>01 — 03</span></div><label>FULL NAME<input name="name" required placeholder="Asha Rao" value="${escape(state.candidateName ?? '')}"></label><div class="two"><label>EMAIL<input name="email" type="email" required placeholder="asha@example.com"></label><label>GITHUB URL<input name="github" placeholder="https://github.com/username"></label></div><label>LINKEDIN PROFILE TEXT <small>PASTE TEXT ONLY</small><textarea name="linkedin" rows="3" placeholder="Paste profile summary or experience..."></textarea></label><div class="divider">PROJECT CONTEXT <span>02 — 03</span></div><label>PROJECT NAME<input name="project" value="TaskTracker API"></label><label>PROJECT DESCRIPTION<input name="description" value="REST API for tasks"></label><label>CODE SAMPLE <small>OPTIONAL</small><textarea name="code" class="code" rows="6" placeholder="Paste a representative function..."></textarea></label><div class="form-actions"><span><i class="live"></i> Builds a local knowledge graph</span><button class="button primary">Build candidate graph ↗</button></div><div id="candidate-result"></div></form><aside class="side-note"><small>INTAKE / NOTE 01</small><div class="glyph">⌁</div><h3>Work before words.</h3><p>Project code and profile claims become connected evidence for a focused, fair depth check.</p><hr><div class="stat"><span>DATA HANDLING</span><b>LOCAL FIRST</b></div><div class="stat"><span>PROFILE SOURCE</span><b>PASTED BY USER</b></div></aside></div>`;
  }

  function taskPage() {
    const job = data.jobs.find((item) => item.id === state.jobId) || data.jobs[0];
    return `${heading('03 / PRACTICAL ASSESSMENT', 'Task desk', 'A company-specific exercise that leads into a conversation about the candidate’s own solution.', '<button class="button outline" id="generate-task">↻ Generate task</button>')}<div class="task-grid"><section class="panel padded"><div class="panel-head"><span>ASSESSMENT BRIEF</span><span class="company">${job.company}</span></div><label class="inline-label">ROLE<select id="job-choice">${data.jobs.map((item) => `<option value="${item.id}" ${item.id === job.id ? 'selected' : ''}>${item.title} — ${item.company}</option>`).join('')}</select></label>${state.task ? `<div class="task-title"><small>PYTHON / 45 MIN</small><h2>${job.assessment}</h2><p>Build a sliding-window rate limiter for an API. Requests should be accepted only while they remain within the configured limit.</p></div><div class="divider">REQUIREMENTS</div><ul class="requirements"><li>Support per-user request limits</li><li>Expire timestamps outside the active window</li><li>Keep the implementation easy to test</li></ul>` : '<div class="empty">Generate the role-specific task to load its brief.</div>'}<div class="divider">RUBRIC <span>PYTHON · REASONING · EDGE CASES</span></div></section><section class="panel padded"><div class="panel-head"><span>SUBMISSION CONSOLE</span><small>NO CODE EXECUTION</small></div><label>SOLUTION SOURCE<textarea id="solution" class="code solution" rows="14" placeholder="Paste the candidate’s solution here...">${state.task ? 'from collections import defaultdict\n\ndef allow_request(user_id, now, limit, window_seconds):\n    """Return whether this request is within the sliding window."""\n    pass' : ''}</textarea></label><label>CANDIDATE NOTES<textarea id="notes" rows="3" placeholder="Approach, trade-offs, assumptions..."></textarea></label><div class="form-actions"><span>${escape(state.candidateId)} profile · local demo</span><button class="button primary" id="save-submission" ${state.task ? '' : 'disabled'}>Save submission ↗</button></div><div id="submission-result"></div></section></div>`;
  }

  function depthPage() {
    const question = state.turn === 1 ? 'Why did you store timestamps in a list instead of a counter?' : state.turn % 2 ? 'What trade-off would you expect if one user made ten times as many requests?' : 'Which line removes timestamps outside the active window, and what happens if none remain?';
    const score = state.score;
    return `${heading('04 / TECHNICAL CONVERSATION', 'Depth check', 'Questions follow the candidate’s own work. Scores stay attached to exact answer evidence.', state.session ? '<button class="button quiet" id="finish">Finish session</button>' : '')}<div class="depth-grid"><section class="panel chat"><div class="panel-head"><span><i class="${state.session ? 'live' : 'offline'}"></i> ${state.session ? 'SESSION ACTIVE' : 'SESSION NOT STARTED'}</span><span>${state.session ? `TURN ${state.turn} / 6` : 'WAITING'}</span></div><div id="transcript" class="transcript">${state.session ? `${state.answer ? `<div class="message candidate"><small>CANDIDATE / TURN ${state.turn - 1}</small><p>${escape(state.answer)}</p><b>SCORE ${state.lastPoints}/5 · ${state.vague ? 'VAGUE' : 'NO FLAGS'}</b></div>` : ''}<div class="message interviewer"><small>PROOFHIRE / INTERVIEWER</small><p class="typing">${question}</p><pre>limiter.py:12\ndef allow_request(user_id, now, limit, window_seconds): ...</pre></div>` : '<div class="chat-empty"><code>$ depth-check --start</code><h2>Ready to test understanding.</h2><p>Start with the submitted solution, then follow the evidence one answer at a time.</p><button class="button primary" id="start">Start depth check ↗</button><button class="text-button" id="demo">Use demo submission</button></div>'}</div>${state.session ? `<form id="answer-form" class="answer-form"><label for="answer">YOUR RESPONSE</label><textarea id="answer" rows="3" placeholder="Explain your reasoning, referring to the submitted code..."></textarea><div class="form-actions"><span>LOCAL EVALUATION · ENTER TO SEND</span><button class="button primary">Send answer ↗</button></div></form>` : ''}</section><aside class="panel evidence"><div class="panel-head"><span>LIVE EVIDENCE</span><small>● VERIFIED QUOTE</small></div>${state.answer ? `<div class="score-row"><div><small>RUNNING SCORE</small><strong>${score}<em>/100</em></strong></div><div><small>CONFIDENCE</small><strong class="amber">${Math.min(94, 45 + state.turn * 7)}<em>%</em></strong></div></div><div class="ascii">[${'█'.repeat(Math.round(score / 10))}${'░'.repeat(10 - Math.round(score / 10))}] ${score}</div><blockquote>“${escape(state.quote)}”</blockquote><p class="reasoning">Answer evaluated for specificity and connection to the submitted code.</p><div class="meter-head">TOKEN SAVINGS <b>94% less context</b></div><div class="token-row"><span>GRAPH CONTEXT <b>412 tokens</b></span><span>FULL PROJECT <b>6,800 tokens</b></span></div><div class="token-track"><i></i></div><div class="flag ${state.vague ? 'warn' : ''}">${state.vague ? 'VAGUE' : 'NO RISK FLAGS'}</div>` : '<div class="evidence-empty"><b>[ ]</b><h3>Evidence will appear here.</h3><p>Each answer is evaluated on its own. Every score links to a quote.</p></div>'}<div class="evidence-footer">HUMAN REVIEW REQUIRED</div></aside></div>`;
  }

  function shortlistPage() {
    return `${heading('05 / EVIDENCE REVIEW', 'Shortlist', 'Backend Intern / FinLeaf · Ranked by evidence, not resume polish.', '<span class="review">● HUMAN REVIEW</span>')}<div class="rail"><span>RANKED CANDIDATES</span><span>UPDATED OCT 01</span></div><div class="list-controls"><label><span>SEARCH CANDIDATES</span><input id="candidate-search" type="search" placeholder="Name, skill or evidence..."></label><label><span>RECOMMENDATION</span><select id="recommendation-filter"><option value="all">All recommendations</option><option value="strong yes">Strong yes</option><option value="no">No</option></select></label><b id="match-count">02 CANDIDATES</b></div>${data.candidates.map((candidate, index) => `<article class="short-row" data-recommendation="${escape(candidate.recommendation)}"><div class="rank"><small>RANK</small><b>#${index + 1}</b></div><div class="candidate"><div class="candidate-title"><h2>${candidate.name}</h2><span class="badge ${index ? 'negative' : ''}">${candidate.recommendation}</span></div><div class="score-track"><i style="width:${candidate.score}%"></i></div><div class="candidate-meta"><b>${candidate.score}<small> / 100</small></b><span>${candidate.confidence}% confidence</span><span>${candidate.id}</span></div><p>${candidate.name === 'Asha Rao' ? 'Asha explains her implementation choices with specific references to the submitted limiter. Evidence suggests strong ownership; thread safety remains worth exploring.' : 'Ravi gives general explanations but does not tie them to the submitted implementation. The depth check surfaced a gap between the concurrency claim and the evidence.'}</p><div class="signals"><div><small>STRENGTH SIGNAL</small><p>${candidate.strength}</p></div><div><small>OPEN QUESTION</small><p>${candidate.concern}</p></div></div><details><summary>Evidence quotes <span>1 VERIFIED ＋</span></summary><blockquote>“${candidate.quote}”<footer>UNDERSTANDING · TURN 01 · ${index ? '1' : '4'}/5</footer></blockquote></details></div><aside class="profile"><small>SKILL PROFILE</small>${['understanding', 'reasoning', 'debugging', 'modification', 'ownership', 'communication'].map((label, skillIndex) => `<div><span>${label}</span><b>${candidate.profile[skillIndex].toFixed(1)}</b></div>`).join('')}</aside></article>`).join('')}<div id="no-candidates" class="empty-filter" hidden>No candidates match these filters.</div><div class="footnote">↳ Scores are calculated from individual answer evaluations. Final hiring decisions remain human.</div>`;
  }

  function graphPage() {
    return `${heading('06 / KNOWLEDGE MAP', 'Work graph', 'A compact map of code, skills, and profile claims used to find relevant questions.', '<a class="button outline" href="#depth">Open depth check ↗</a>')}<div class="graph-grid"><section class="panel graph-panel"><div class="panel-head"><span>NODE-LINK VIEW / ASHA RAO</span><span>7 NODES · 7 EDGES</span></div><div class="node-map"><div class="node candidate-node">Asha Rao</div><div class="node project-node">Rate limiter</div><div class="node file-node">limiter.py</div><div class="node function-node">allow_request()</div><div class="node skill-one">Python</div><div class="node skill-two">SQL</div><div class="node claim-node">API design</div><div class="edge-label edge-a">contains</div><div class="edge-label edge-b">contains</div><div class="edge-label edge-c">contains</div><div class="edge-label edge-d">uses</div><div class="edge-label edge-e">claims</div></div><div class="legend"><span>● CANDIDATE</span><span>● PROJECT</span><span>● FILE / FUNCTION</span><span>● SKILL</span><span>● CLAIM</span></div></section><aside class="panel graph-aside"><div class="panel-head"><span>GRAPH SUMMARY</span><span class="company">READY</span></div><div class="big-stat"><b>42</b><span>nodes indexed</span></div><div class="big-stat"><b>61</b><span>relationships found</span></div><div class="divider">MATCHED SKILLS</div><div class="tags"><span>python</span><span>fastapi</span><span>sql</span></div><div class="graph-note"><small>WHY GRAPH CONTEXT</small><p>Focused retrieval helps each question use the smallest relevant part of a candidate’s work.</p><b>−94%</b><span>sample context vs full project</span></div></aside></div>`;
  }

  function render() {
    state.page = location.hash.slice(1) || 'jobs';
    if (!pages.some(([id]) => id === state.page)) state.page = 'jobs';
    const view = { jobs: jobsPage, candidate: candidatePage, task: taskPage, depth: depthPage, shortlist: shortlistPage, graph: graphPage }[state.page]();
    app.innerHTML = `<div class="frame ${state.collapsed ? 'sidebar-collapsed' : ''}">${header()}<div class="workspace">${topbar()}<main>${view}</main><footer class="footer"><span>PROOFHIRE <b>0.1.0</b></span><span>UNDERSTANDING OVER POLISH</span><span><i class="live"></i> LOCAL DEMO MODE</span></footer></div></div>`;
    if (state.page === 'shortlist') {
      const activeJob = data.jobs.find((job) => job.id === state.jobId) ?? data.jobs[0];
      const subtitle = document.querySelector('.page-heading p');
      subtitle.textContent = `${activeJob.title} / ${activeJob.company} · Ranked by evidence, not resume polish.`;
    }
    wire();
  }

  function wire() {
    document.querySelector('#theme-toggle')?.addEventListener('click', toggleTheme);
    document.querySelectorAll('.candidate-title .badge').forEach((badge) => {
      const recommendation = badge.textContent.trim().toLowerCase();
      badge.textContent = `Suggested: ${recommendation === 'no' ? 'needs stronger evidence' : recommendation}`;
    });
    document.querySelectorAll('.candidate-meta span:nth-child(2)').forEach((confidence) => {
      const confidencePercent = Number(confidence.textContent.match(/\d+/)?.[0] ?? 0);
      const confidenceLabel = confidencePercent >= 80 ? 'High' : confidencePercent >= 55 ? 'Moderate' : 'Low';
      confidence.textContent = `${confidenceLabel} confidence · ${confidencePercent}%`;
    });
    document.querySelector('#sidebar-toggle')?.addEventListener('click', () => { state.collapsed = !state.collapsed; localStorage.setItem('proofhire-sidebar-collapsed', String(state.collapsed)); render(); });
    document.querySelector('#global-job-choice')?.addEventListener('change', (event) => { state.jobId = event.target.value; state.task = false; render(); });
    document.querySelectorAll('[data-job]').forEach((link) => link.addEventListener('click', () => { state.jobId = link.dataset.job; }));
    document.querySelector('#candidate-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      state.candidateName = form.get('name');
      state.candidateId = 'cand_local';
      document.querySelector('#candidate-result').innerHTML = `<div class="result"><i class="live"></i><b>GRAPH READY</b><span>24 nodes · 32 edges</span><a href="#graph">Inspect graph →</a></div>`;
    });
    document.querySelector('#generate-task')?.addEventListener('click', () => { state.task = true; render(); });
    document.querySelector('#job-choice')?.addEventListener('change', (event) => { state.jobId = event.target.value; state.task = false; render(); });
    document.querySelector('#save-submission')?.addEventListener('click', () => {
      if (!state.task) return;
      document.querySelector('#submission-result').innerHTML = '<div class="result"><i class="live"></i><b>SUBMISSION SAVED</b><span>1 file · 4 functions indexed</span><a href="#depth">Start depth check →</a></div>';
    });
    document.querySelector('#start')?.addEventListener('click', startSession);
    document.querySelector('#demo')?.addEventListener('click', startSession);
    document.querySelector('#answer-form')?.addEventListener('submit', submitAnswer);
    document.querySelector('#finish')?.addEventListener('click', () => { state.session = false; state.turn = 1; render(); });
    document.querySelector('#candidate-search')?.addEventListener('input', filterCandidates);
    document.querySelector('#recommendation-filter')?.addEventListener('change', filterCandidates);
    const jobChoice = document.querySelector('#job-choice');
    if (jobChoice) jobChoice.value = state.jobId;
    if (state.page === 'shortlist') filterCandidates();
  }

  function toggleTheme() {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem('proofhire-theme', nextTheme);
    const button = document.querySelector('#theme-toggle');
    button.textContent = nextTheme === 'dark' ? '☀' : '☾';
    button.setAttribute('aria-label', `Switch to ${nextTheme === 'dark' ? 'light' : 'dark'} theme`);
    button.title = `Switch to ${nextTheme === 'dark' ? 'light' : 'dark'} theme`;
  }

  function filterCandidates() {
    const query = document.querySelector('#candidate-search').value.trim().toLowerCase();
    const recommendation = document.querySelector('#recommendation-filter').value;
    const hasSeededCandidates = state.jobId === 'job_1';
    let visibleCount = 0;
    document.querySelectorAll('.short-row').forEach((row) => {
      const matchesSearch = hasSeededCandidates && row.textContent.toLowerCase().includes(query);
      const matchesRecommendation = recommendation === 'all' || row.dataset.recommendation === recommendation;
      row.hidden = !(matchesSearch && matchesRecommendation);
      if (!row.hidden) visibleCount += 1;
    });
    document.querySelector('#match-count').textContent = `${String(visibleCount).padStart(2, '0')} ${visibleCount === 1 ? 'CANDIDATE' : 'CANDIDATES'}`;
    const emptyState = document.querySelector('#no-candidates');
    const activeJob = data.jobs.find((job) => job.id === state.jobId) ?? data.jobs[0];
    emptyState.textContent = hasSeededCandidates ? 'No candidates match these filters.' : `No completed depth checks for ${activeJob.title} yet.`;
    emptyState.hidden = visibleCount > 0;
  }

  function startSession() {
    state.session = true;
    state.turn = 1;
    state.score = 0;
    state.lastPoints = 0;
    state.quote = '';
    state.answer = '';
    render();
  }

  function submitAnswer(event) {
    event.preventDefault();
    const box = document.querySelector('#answer');
    const answer = box.value.trim();
    if (!answer) { box.focus(); return; }
    state.answer = answer;
    state.vague = answer.length < 55 || /best practice|it is faster|not sure/i.test(answer);
    const points = answer ? (state.vague ? 2 : 4) : 0;
    state.lastPoints = points;
    state.score = Math.min(100, Math.round((state.score * (state.turn - 1) + points * 20) / state.turn));
    state.quote = answer.split(/\s+/).slice(0, 18).join(' ');
    state.turn += 1;
    render();
    document.querySelector('.typing')?.classList.add('typed');
  }

  function keyboard(event) {
    if (event.altKey && /^[1-6]$/.test(event.key)) location.hash = `#${pages[Number(event.key) - 1][0]}`;
  }

  window.addEventListener('hashchange', render);
  window.addEventListener('keydown', keyboard);
  render();
})();