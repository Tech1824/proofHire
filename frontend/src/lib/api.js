import healthExample from '../mocks/health.json';
import jobExample from '../mocks/job.json';
import candidateExample from '../mocks/candidate.json';
import taskExample from '../mocks/task.json';
import depthAnswerExample from '../mocks/depth-answer.json';
import shortlistExample from '../mocks/shortlist.json';

const API_ROOT = 'http://localhost:8000/api';
const extraJob = {
  job_id: 'job_2', title: 'Frontend Developer', company: 'PixelNest',
  description: 'Build accessible, resilient interface components for a creative collaboration product.',
  required_skills: ['javascript', 'html/css', 'accessibility'], seniority: 'junior'
};
const jobs = [structuredClone(jobExample), extraJob];
const candidates = [
  { candidate_id: 'cand_1', name: 'Asha Rao', email: 'asha@example.com', github_url: 'https://github.com/asha-demo', linkedin_text: 'Backend engineer focused on Python APIs and thoughtful data structures.', projects: [], graph_summary: candidateExample.graph_summary },
  { candidate_id: 'cand_2', name: 'Ravi Kumar', email: 'ravi@example.com', github_url: 'https://github.com/ravi-demo', linkedin_text: 'Expert in concurrency and scalable distributed systems.', projects: [], graph_summary: { nodes: 28, edges: 34, skills: ['python', 'concurrency', 'sql'] } }
];
const taskExample = { ...taskExample, brief: 'Build a sliding-window rate limiter for an API. Requests should be accepted only while they remain within the configured limit.', requirements: ['Support per-user request limits', 'Expire timestamps outside the active window', 'Keep the implementation easy to test'], starter_code: 'from collections import defaultdict\n\ndef allow_request(user_id, now, limit, window_seconds):\n    """Return whether this request is within the sliding window."""\n    pass' };
const sessionState = new Map();
let candidateSequence = 3;
let taskSequence = 2;
let submissionSequence = 1;

// Selects mock mode by default, with an optional persisted switch to the API.
export function usesMocks() {
  return (localStorage.getItem('proofhire-mode') ?? import.meta.env.PUBLIC_USE_MOCKS ?? 'true') !== 'false';
}

// Calls the backend and returns JSON, preserving the documented error shape.
async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers }
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body?.error?.message ?? `Request failed (${response.status})`);
  return body;
}

// Adds a small delay so loading states remain visible in the demo.
async function mock(value) {
  await new Promise((resolve) => setTimeout(resolve, 180));
  return structuredClone(value);
}

// Returns system health and model availability.
export function getHealth() {
  return usesMocks() ? mock(healthExample) : request('/health');
}

// Changes whether the backend serves cached demo answers only.
export function setDemoMode(enabled) {
  return usesMocks() ? mock({ demo_mode: enabled }) : request('/config/demo-mode', { method: 'POST', body: JSON.stringify({ enabled }) });
}

// Creates a job listing.
export function createJob(data) {
  if (!usesMocks()) return request('/jobs', { method: 'POST', body: JSON.stringify(data) });
  const job = { ...data, job_id: `job_${jobs.length + 1}` };
  jobs.push(job);
  return mock(job);
}

// Lists available jobs.
export function listJobs() {
  return usesMocks() ? mock({ jobs }) : request('/jobs');
}

// Retrieves one job.
export function getJob(jobId) {
  return usesMocks() ? mock(jobs.find((job) => job.job_id === jobId) ?? jobExample) : request(`/jobs/${jobId}`);
}

// Creates a candidate and builds a lightweight demo graph summary.
export function createCandidate(data) {
  if (!usesMocks()) return request('/candidates', { method: 'POST', body: JSON.stringify(data) });
  const result = { candidate_id: `cand_${candidateSequence++}`, graph_status: 'ready', graph_summary: { nodes: 18 + data.projects.length * 6, edges: 24 + data.projects.length * 8, skills: ['python', 'rest api', 'sql'] } };
  candidates.push({ ...data, ...result });
  return mock(result);
}

// Retrieves candidate details.
export function getCandidate(candidateId) {
  return usesMocks() ? mock(candidates.find((candidate) => candidate.candidate_id === candidateId) ?? candidates[0]) : request(`/candidates/${candidateId}`);
}

// Retrieves a candidate's knowledge graph.
export function getCandidateGraph(candidateId) {
  if (!usesMocks()) return request(`/candidates/${candidateId}/graph`);
  return mock({
    nodes: [
      { id: candidateId, type: 'candidate', label: 'Asha Rao', weight: 1 },
      { id: 'project:limiter', type: 'project', label: 'Rate limiter', weight: 0.9 },
      { id: 'file:limiter.py', type: 'file', label: 'limiter.py', weight: 0.8 },
      { id: 'func:allow_request', type: 'function', label: 'allow_request', weight: 0.95 },
      { id: 'skill:python', type: 'skill', label: 'Python', weight: 0.85 },
      { id: 'skill:sql', type: 'skill', label: 'SQL', weight: 0.52 },
      { id: 'skill:rest-api', type: 'skill', label: 'REST API', weight: 0.76 },
      { id: 'claim:api', type: 'claim', label: 'API design', weight: 0.65 }
    ],
    edges: [
      { source: candidateId, target: 'project:limiter', type: 'contains' },
      { source: 'project:limiter', target: 'file:limiter.py', type: 'contains' },
      { source: 'file:limiter.py', target: 'func:allow_request', type: 'contains' },
      { source: 'func:allow_request', target: 'skill:python', type: 'uses' },
      { source: 'project:limiter', target: 'skill:sql', type: 'uses' },
      { source: 'func:allow_request', target: 'skill:rest-api', type: 'uses' },
      { source: candidateId, target: 'claim:api', type: 'claims' },
      { source: 'claim:api', target: 'skill:python', type: 'claims' },
      { source: 'claim:api', target: 'skill:rest-api', type: 'claims' }
    ]
  });
}

// Generates a task tailored to the selected job.
export function generateTask(jobId) {
  if (!usesMocks()) return request('/tasks/generate', { method: 'POST', body: JSON.stringify({ job_id: jobId }) });
  return mock({ ...taskExample, job_id: jobId, task_id: `task_${taskSequence++}` });
}

// Retrieves a generated task.
export function getTask(taskId) {
  return usesMocks() ? mock({ ...taskExample, task_id: taskId }) : request(`/tasks/${taskId}`);
}

// Saves a candidate's task submission.
export function createSubmission(data) {
  if (!usesMocks()) return request('/submissions', { method: 'POST', body: JSON.stringify(data) });
  return mock({ submission_id: `sub_${submissionSequence++}`, graph_updated: true, stats: { files: data.files.length, functions: 4 } });
}

// Starts a depth-check session with a question tied to submitted code.
export function startDepth(submissionId) {
  if (!usesMocks()) return request('/depth/start', { method: 'POST', body: JSON.stringify({ submission_id: submissionId }) });
  const result = { session_id: `sess_${Date.now()}`, max_turns: 6, turn: { turn_number: 1, type: 'question', level: 2, node_ref: 'func:limiter.py::allow_request', text: 'Why did you store timestamps in a list instead of a counter?', code_snippet: { path: 'limiter.py', start_line: 12, code: 'def allow_request(user_id, now, limit, window_seconds): ...' }, expects: 'text' } };
  sessionState.set(result.session_id, { ...result, submission_id: submissionId, status: 'in_progress', turns: [], score: 0 });
  return mock(result);
}

// Evaluates one answer and returns the running score, evidence, and next turn.
export function submitDepthAnswer(sessionId, answer, code = null) {
  if (!usesMocks()) return request('/depth/answer', { method: 'POST', body: JSON.stringify({ session_id: sessionId, answer, code }) });
  const session = sessionState.get(sessionId);
  if (!session) return Promise.reject(new Error('Depth session not found. Start a new session.'));
  const turnNumber = session.turn.turn_number;
  const vague = answer.trim().length < 55 || /best practice|it is faster|not sure/i.test(answer);
  const score = answer.trim() ? (vague ? 2 : 4) : 0;
  const quote = answer.trim().split(/\s+/).slice(0, 18).join(' ');
  const evaluation = { turn_number: turnNumber, score, confidence: vague ? 0.56 : 0.84, dimensions: { understanding: score, reasoning: Math.max(1, score - 1), communication: 4 }, evidence_quote: quote, reasoning: vague ? 'The answer stays general and does not connect the choice to a concrete behavior in the submitted code.' : 'The answer connects a concrete implementation choice to the behavior of the submitted code.', flags: vague ? ['vague'] : [] };
  session.turns.push({ turn: session.turn, answer, evaluation });
  session.score = Math.round((session.score * (turnNumber - 1) + score * 20) / turnNumber);
  const done = turnNumber >= 6;
  const next = done ? null : { turn_number: turnNumber + 1, type: turnNumber >= 3 ? 'modify' : 'question', level: Math.min(5, (session.turn.level ?? 2) + (score >= 4 ? 1 : 0)), node_ref: 'func:limiter.py::allow_request', text: vague ? 'Which line removes timestamps that are outside the active window, and what happens if none remain?' : 'What trade-off would you expect if one user made ten times as many requests?', code_snippet: turnNumber >= 3 ? { path: 'limiter.py', start_line: 12, code: 'def allow_request(user_id, now, limit, window_seconds): ...' } : null, expects: turnNumber >= 3 ? 'code' : 'text' };
  session.turn = next;
  session.status = done ? 'done' : 'in_progress';
  const result = {
    evaluation,
    running: { score_100: Math.min(100, session.score), confidence: Math.min(0.95, 0.45 + turnNumber * 0.07), turns_done: turnNumber, dimensions: { understanding: score, reasoning: Math.max(1, score - 1), communication: 4 } },
    meta: { ...depthAnswerExample.meta, context_tokens: 412 + turnNumber * 19, full_context_tokens: 6800 },
    status: session.status,
    next
  };
  return mock(result);
}

// Retrieves all turns from a depth-check session.
export function getDepthSession(sessionId) {
  return usesMocks() ? mock(sessionState.get(sessionId) ?? { session_id: sessionId, submission_id: 'sub_1', status: 'done', turns: [] }) : request(`/depth/${sessionId}`);
}

// Ends a session and creates its final profile.
export function finishDepth(sessionId) {
  if (!usesMocks()) return request(`/depth/${sessionId}/finish`, { method: 'POST' });
  const session = sessionState.get(sessionId);
  if (session) session.status = 'done';
  return mock({ status: 'done' });
}

// Returns the evidence-ranked shortlist for one job.
export function getShortlist(jobId) {
  if (!usesMocks()) return request(`/shortlist/${jobId}`);
  if (jobId !== 'job_1') return mock({ ...shortlistExample, job_id: jobId, candidates: [] });
  const weak = {
    ...shortlistExample.candidates[0], rank: 2, candidate_id: 'cand_2', name: 'Ravi Kumar', overall_score: 39, confidence: 0.62,
    recommendation: 'no', skill_profile: { understanding: 2.1, reasoning: 1.8, debugging: 1.7, modification: 2.0, ownership: 1.6, communication: 3.2 },
    strengths: ['Communicates confidently'], concerns: ['Could not explain the concurrency claim'],
    evidence: [{ claim: 'Ownership of the submitted solution', quote: 'I used this because it is the best practice.', turn_number: 2, score: 1 }],
    summary: 'Ravi gives general explanations but does not tie them to the submitted implementation. The depth check surfaced a gap between the concurrency claim and the evidence reviewed. More concrete evidence would be needed for a stronger recommendation.'
  };
  return mock({ ...shortlistExample, job_id: jobId, candidates: shortlistExample.candidates.concat(weak) });
}