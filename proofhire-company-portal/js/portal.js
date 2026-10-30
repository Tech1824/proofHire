/* ProofHire company portal: shared data, layout and helpers. Every page loads this file. */
const KEY = "proofhire-company-v1";
const API_BASE = "http://localhost:8000/api";

const SEED = {
  user: { email: "hiring@finleaf.com", name: "Recruiter" },
  jobId: "job_1",
  sel: "cand_arjun",
  cmp: ["cand_arjun", "cand_ravi"],
  theme: "dark",
  isLive: false,
  company: {
    name: "FinLeaf Infrastructure",
    email: "hiring@finleaf.com",
    website: "https://finleaf.com",
    industry: "Fintech & High-Throughput Core",
    size: "51–200",
    location: "New York, NY (Hybrid)",
    about: "FinLeaf builds ultra-low-latency transaction and rate-limiting infrastructure for global fintech applications."
  },
  jobs: [
    { id: "job_1", title: "Senior Distributed Systems Engineer", co: "FinLeaf Infrastructure", track: "Senior", desc: "Design, optimize, and maintain resilient multi-region distributed rate-limiting services, memory caches, and transaction queues.", skills: "python, distributed systems, redis, concurrency, system design", status: "Open", task: "Distributed Rate Limiter", min: 45 },
    { id: "job_2", title: "Backend Intern (High-Throughput APIs)", co: "FinLeaf Infrastructure", track: "Junior", desc: "Build foundational backend services, automated test harnesses, and rate-limiting middleware using Python and FastAPI.", skills: "python, fastapi, rest api, sql", status: "Open", task: "Sliding-Window Limiter & Middleware", min: 45 }
  ],
  assess: [
    { id: 1, title: "Distributed Rate Limiter", job: "job_1", min: 45, type: "Code + Depth", brief: "Per-user sliding window limiter with thread-safety and Redis scaling." },
    { id: 2, title: "Sliding-Window Limiter & Middleware", job: "job_2", min: 45, type: "Code + Depth", brief: "FastAPI rate-limiting middleware with synthetic clock mocks." }
  ],
  apps: [
    {
      id: "cand_arjun",
      name: "Arjun Mehta",
      email: "arjun@example.com",
      github: "arjunmehta-dev",
      job: "job_1",
      exp: 5,
      status: "Shortlisted",
      score: 88,
      conf: 0.91,
      rec: "Strong hire",
      skills: ["python", "distributed systems", "redis", "concurrency"],
      dims: { Understanding: 92, Reasoning: 90, Debugging: 85, Communication: 84 },
      summary: "Verified ownership of the distributed rate limiter. Found a concurrency bug unprompted and proposed a Redis scaling design.",
      turns: [
        { q: "Why a deque over a list for the expiry loop?", a: "A deque gives O(1) popleft, so expiry is O(k).", s: 5, ev: "deque gives O(1) popleft because it's a doubly-linked list internally" },
        { q: "What race condition exists with two threads on one user?", a: "A TOCTOU race between the length check and append. Use a per-user lock.", s: 5, ev: "classic TOCTOU race" },
        { q: "Why is test_window_expiry flaky?", a: "time.sleep is unreliable on CI. Inject a fake clock.", s: 4, ev: "inject a fake clock" }
      ]
    },
    {
      id: "cand_ravi",
      name: "Ravi Kumar",
      email: "ravi.k@example.com",
      github: "ravi-weak",
      job: "job_1",
      exp: 2,
      status: "Rejected",
      score: 39,
      conf: 0.62,
      rec: "Needs more evidence",
      skills: ["python", "concurrency"],
      dims: { Understanding: 42, Reasoning: 36, Debugging: 34, Communication: 64 },
      summary: "Gives general explanations but does not tie them to the submitted implementation. Evident gap between claimed concurrency skills and code answers.",
      turns: [
        { q: "Why a deque over a list for the expiry loop?", a: "It is faster I think.", s: 2, ev: "It is faster I think" }
      ]
    }
  ]
};

let D;
try {
  D = JSON.parse(localStorage.getItem(KEY)) || SEED;
  if (!D.user) D.user = SEED.user;
} catch (e) {
  D = SEED;
}

const save = () => {
  try {
    localStorage.setItem(KEY, JSON.stringify(D));
  } catch (e) {}
};

document.documentElement.dataset.theme = D.theme || "dark";

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const jt = id => (D.jobs.find(j => String(j.id) === String(id)) || {}).title || "—";
const st = s => ({ Shortlisted: "", Interview: "b", Reviewed: "m", New: "m", Rejected: "n" }[s] || "m");
const bar = v => `<div class="bar"><i style="width:${Math.min(100, Math.max(0, v))}%"></i></div>`;
const chips = s => (Array.isArray(s) ? s : String(s || "").split(",")).map(x => `<span class="chip">${esc(x.trim())}</span>`).join("");
const go = p => { location.href = p + ".html"; };
const pad = n => String(n).padStart(2, "0");

const toast = m => {
  const t = $("#toast");
  if (!t) return;
  t.textContent = m;
  t.classList.remove("hide");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => t.classList.add("hide"), 2400);
};

const head = (n, title, lead, btn = "") => `
  <div class="head">
    <div>
      <div class="eb">PROOFHIRE / ${n} / HIRING DESK</div>
      <h1>${title}<s>.</s></h1>
      <p class="lead">${lead}</p>
    </div>
    ${btn}
  </div>`;

const sec = (l, r = "") => `<div class="sec"><span>${l}</span><em>${r}</em></div>`;
const foot = () => `
  <div class="ft">
    <div>
      <b>↳ VERIFIED EVIDENCE OVER RESUME POLISH</b>
      Every recommendation links directly to verified quotes and candidate explanations.
    </div>
    <a href="shortlist.html">View Evidence Shortlist →</a>
  </div>`;

const sel = () => {
  const urlId = new URLSearchParams(location.search).get("id");
  const targetId = urlId || D.sel;
  return D.apps.find(a => String(a.id) === String(targetId)) || D.apps[0] || SEED.apps[0];
};

const openC = id => {
  D.sel = id;
  save();
  location.href = "candidate.html?id=" + encodeURIComponent(id);
};

const openR = id => {
  D.sel = id;
  save();
  location.href = "ai-report.html?id=" + encodeURIComponent(id);
};

async function setSt(id, s) {
  const app = D.apps.find(a => String(a.id) === String(id));
  if (app) app.status = s;
  save();
  toast("Updated status: " + s);
  try {
    await fetch(`${API_BASE}/company/candidates/${encodeURIComponent(id)}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: s })
    });
  } catch (err) {}
  render();
}

function logout() {
  D.user = null;
  save();
  go("login");
}

/* ATS Navigation Structure: Workspace, Benchmarks, Settings */
const NAV = [
  ["HIRING DESK", [
    ["dashboard", "▦", "Dashboard"],
    ["jobs", "☷", "Jobs"],
    ["applicants", "◉", "Applicants"],
    ["shortlist", "★", "Shortlist"]
  ]],
  ["EVALUATION & BENCHMARKS", [
    ["compare", "⇄", "Compare"],
    ["assessments", "≡", "Assessments"],
    ["graph", "🕸", "Knowledge graph"]
  ]],
  ["ORGANIZATION", [
    ["company-profile", "🏢", "Company profile"]
  ]]
];

const LOGO = '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ProofHire logo"><defs><linearGradient id="phb" x1="0" y1="100" x2="100" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#4f5bff"/><stop offset=".5" stop-color="#ff3d9a"/><stop offset="1" stop-color="#ff8a1e"/></linearGradient><linearGradient id="phl" x1="43" y1="69" x2="75" y2="32" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#a63fe0"/><stop offset=".5" stop-color="#ff3d9a"/></linearGradient></defs><rect x="1.5" y="1.5" width="97" height="97" rx="25" fill="#06070a" stroke="url(#phb)" stroke-width="3"/><circle cx="74.6" cy="31.9" r="14.5" fill="none" stroke="#ff8a1e" stroke-opacity=".3" stroke-width="2.5"/><line x1="25.4" y1="51.3" x2="43.4" y2="69.4" stroke="#6a5ae6" stroke-width="5"/><line x1="43.4" y1="69.4" x2="74.6" y2="31.9" stroke="url(#phl)" stroke-width="6.5"/><circle cx="25.4" cy="51.3" r="8" fill="#06070a" stroke="#4f5bff" stroke-width="3"/><circle cx="43.4" cy="69.4" r="8" fill="#06070a" stroke="#b23cd6" stroke-width="3"/><circle cx="74.6" cy="31.9" r="9" fill="#ff8a1e"/></svg>';

let CUR, PAGE;

function shell() {
  const s = $("#side");
  const t = $("#top");
  if (!s || !t) return;

  s.innerHTML = `
    <div class="brand">
      <a class="logo" href="dashboard.html" aria-label="ProofHire home">${LOGO}</a>
      <b>PROOFHIRE</b>
      <button class="col" onclick="document.body.classList.toggle('mini')" aria-label="Collapse sidebar">‹</button>
    </div>` +
    NAV.map(([g, l]) =>
      `<div class="grp">${g}</div>` +
      l.map(([k, i, n]) => `<a class="n ${k === PAGE ? "on" : ""}" href="${k}.html"><i>${i}</i><span class="t">${n}</span></a>`).join("")
    ).join("") +
    `<div class="sys">
      <small>System Mode</small>
      <span class="dot" style="background:${D.isLive ? 'var(--ok, #19c37d)' : 'var(--warn, #ff9a3d)'}"></span>
      <span class="t">${D.isLive ? 'Live API' : 'Demo mode'}</span>
      <button class="out t" onclick="logout()">Log out</button>
    </div>`;

  const navMatch = NAV.flatMap(g => g[1]).find(n => n[0] === PAGE);
  const name = navMatch ? navMatch[2] : (PAGE === "candidate" ? "Candidate Profile" : PAGE === "ai-report" ? "AI Evaluation Report" : "Workspace");

  t.innerHTML = `
    <div class="crumb">
      <a class="h" href="dashboard.html">ProofHire</a> › 
      <b>${name}</b> › 
      <span>${esc(jt(D.jobId))}</span>
      <span style="margin-left:14px;font-size:12px;color:var(--dim,#888);">Role Filter</span>
      <select id="role" aria-label="Role" onchange="D.jobId=this.value;save();render()">
        ${D.jobs.map(j => `<option value="${j.id}" ${String(j.id) === String(D.jobId) ? "selected" : ""}>${esc(j.title)}</option>`).join("")}
      </select>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <a class="btn g s" href="http://localhost:4321" target="_blank" title="Preview Candidate Portal" style="display:inline-flex;align-items:center;gap:4px;">
        👤 Candidate Desk ↗
      </a>
      <span class="pill" style="border:1px solid ${D.isLive ? '#19c37d' : '#ff9a3d'}; color:${D.isLive ? '#19c37d' : '#ff9a3d'}; background:${D.isLive ? 'rgba(25,195,125,0.1)' : 'rgba(255,154,61,0.1)'}">
        ● ${D.isLive ? 'Live API' : 'Demo'}
      </span>
      <button class="ib" onclick="D.theme=D.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=D.theme;save()" aria-label="Toggle theme">
        ${D.theme === 'dark' ? '☀' : '☾'}
      </button>
      <a class="btn" href="jobs.html">+ Create Job ↗</a>
    </div>`;
}

function render() {
  shell();
  const v = $("#v");
  if (v && CUR) v.innerHTML = CUR();
}

async function syncWithBackend() {
  try {
    const res = await fetch(`${API_BASE}/company/dashboard`);
    if (!res.ok) return;
    const data = await res.json();
    D.isLive = true;

    if (data.company) {
      D.company = { ...D.company, ...data.company };
    }

    if (data.jobs && data.jobs.length > 0) {
      D.jobs = data.jobs.map(j => ({
        id: j.job_id,
        title: j.title,
        co: j.company || D.company.name,
        track: j.seniority || "Senior",
        desc: j.description || "",
        skills: Array.isArray(j.required_skills) ? j.required_skills.join(", ") : (j.required_skills || "python"),
        status: j.status || "Open",
        task: "Distributed Practical Code + Depth Check",
        min: 45
      }));
      if (!D.jobs.some(j => String(j.id) === String(D.jobId))) {
        D.jobId = D.jobs[0].id;
      }
    }

    const rawCandidates = data.applicants || data.recent_applicants || [];
    if (rawCandidates.length > 0) {
      const mergedApps = rawCandidates.map(c => {
        const skillProfile = c.skill_profile || {};
        const dims = c.dims || {
          Understanding: Math.round((skillProfile.understanding || 3.5) * 20),
          Reasoning: Math.round((skillProfile.reasoning || 3.5) * 20),
          Debugging: Math.round((skillProfile.debugging || 3.2) * 20),
          Communication: Math.round((skillProfile.communication || 4.0) * 20)
        };
        const turns = (c.evidence || []).map(ev => ({
          q: ev.claim || "Implementation choice",
          a: ev.quote || "Code explanation provided",
          s: ev.score || 4,
          ev: ev.quote || "",
          disputed: ev.disputed || false,
          dispute_reason: ev.dispute_reason || ""
        }));
        return {
          id: c.candidate_id,
          name: c.name || "Candidate",
          email: c.email || "applicant@example.com",
          github: (c.github_url || "").replace("https://github.com/", "") || (c.name ? c.name.toLowerCase().replace(/\s+/g, "-") : "dev"),
          job: c.job_id || D.jobId,
          exp: c.years_experience || 3,
          status: c.status || "New",
          score: c.overall_score || c.score || 0,
          conf: c.confidence || 0,
          rec: c.recommendation || (c.overall_score >= 80 ? "Strong hire" : c.overall_score >= 60 ? "Hire" : "Needs more evidence"),
          skills: c.skills || (skillProfile ? Object.keys(skillProfile) : ["python", "redis"]),
          dims: dims,
          summary: c.summary || "Assessment on file with verified code reasoning.",
          turns: turns
        };
      });

      // Keep seed apps if not yet in database so demo remains rich
      for (const seedApp of SEED.apps) {
        if (!mergedApps.some(a => String(a.id) === String(seedApp.id))) {
          mergedApps.push(seedApp);
        }
      }
      D.apps = mergedApps;
    }

    save();
    render();
  } catch (err) {
    // Keep local cache
  }
}

function boot(page, fn) {
  PAGE = page;
  CUR = fn;
  if (!D.user && page !== "login") {
    location.replace("login.html");
    return;
  }
  render();
  syncWithBackend();
}

/* Clickable elements helper */
function nav(s) {
  const [k, v] = s.split(":");
  if (k === "c") openC(v);
  else if (k === "r") openR(v);
  else if (k === "role") {
    D.jobId = v;
    save();
    go("applicants");
  } else go(k);
}

document.addEventListener("click", e => {
  const el = e.target.closest("[data-open]");
  if (!el || e.target.closest("button,select,a,input,textarea,label")) return;
  nav(el.dataset.open);
});

document.addEventListener("keydown", e => {
  if (e.key === "Enter" && e.target.matches("[data-open]")) nav(e.target.dataset.open);
});

/* Knowledge-graph statistics */
function gdata() {
  const open = D.jobs.filter(j => j.status === "Open");
  const sk = {};
  D.apps.forEach(a => (a.skills || []).forEach(s => {
    s = s.trim().toLowerCase();
    sk[s] = (sk[s] || 0) + 1;
  }));
  D.jobs.forEach(j => (j.skills || "").split(",").forEach(s => {
    s = s.trim().toLowerCase();
    if (s && s !== "—") sk[s] = sk[s] || 0;
  }));
  const exp = D.apps.filter(a => a.exp > 0).map(a => ({ a, n: Math.ceil(a.exp / 2) }));
  const proj = D.apps.filter(a => a.score).map(a => ({ a, t: (D.assess.find(x => String(x.job) === String(a.job)) || {}).title || "Assessment task" }));
  const c = {
    joblead: open.length,
    candidate: D.apps.length,
    skill: Object.keys(sk).length,
    experience: exp.reduce((s, e) => s + e.n, 0),
    project: proj.length
  };
  c.total = c.joblead + c.candidate + c.skill + c.experience + c.project;
  return { c, open, sk, exp, proj };
}
