/* ProofHire company portal: shared data, layout and helpers. Every page loads this file. */
const KEY="proofhire-company-v1";
const SEED={user:null,jobId:1,sel:1,cmp:[1,2],theme:"dark",
 company:{name:"FinLeaf",email:"hiring@finleaf.com",website:"https://finleaf.com",industry:"Fintech",size:"51–200",location:"New York, NY",about:"We build reliable infrastructure for modern financial products."},
 jobs:[{id:1,title:"Backend Intern",co:"FinLeaf",track:"Junior",desc:"Build reliable services for a growing financial platform.",skills:"python, rest api, sql",status:"Open",task:"Rate limiter",min:45},
       {id:2,title:"Frontend Developer",co:"PixelNest",track:"Junior",desc:"Build accessible, resilient interface components for a creative collaboration product.",skills:"javascript, html/css, accessibility",status:"Open",task:"Accessible menu",min:45}],
 assess:[{id:1,title:"Rate limiter",job:1,min:45,type:"Code + Depth",brief:"Per-user sliding window limiter with tests."},{id:2,title:"Accessible menu",job:2,min:45,type:"Code + Depth",brief:"Keyboard-friendly dropdown menu."}],
 apps:[
 {id:1,name:"Arjun Mehta",email:"arjun@example.com",github:"arjunmehta-dev",job:1,exp:4,status:"Shortlisted",score:88,conf:.91,rec:"Strong hire",skills:["python","fastapi","redis","sql"],dims:{Understanding:92,Reasoning:90,Debugging:85,Communication:84},summary:"Verified ownership of the rate limiter. Found a concurrency bug unprompted and proposed a Redis scaling design.",
  turns:[{q:"Why a deque over a list for the expiry loop?",a:"A deque gives O(1) popleft, so expiry is O(k).",s:5,ev:"deque gives O(1) popleft because it's a doubly-linked list internally"},{q:"What race condition exists with two threads on one user?",a:"A TOCTOU race between the length check and append. Use a per-user lock.",s:5,ev:"classic TOCTOU race"},{q:"Why is test_window_expiry flaky?",a:"time.sleep is unreliable on CI. Inject a fake clock.",s:4,ev:"inject a fake clock"}]},
 {id:2,name:"Asha Rao",email:"asha@example.com",github:"asha-demo",job:1,exp:2,status:"Interview",score:71,conf:.74,rec:"Hire",skills:["python","sql"],dims:{Understanding:74,Reasoning:70,Debugging:66,Communication:78},summary:"Good basics and correct instincts on concurrency. Answers lacked complexity detail.",
  turns:[{q:"Why a deque over a list for the expiry loop?",a:"Deque pops from the left quickly.",s:3,ev:"Deque pops from the left quickly"},{q:"What race condition exists with two threads on one user?",a:"Two threads could both pass the limit check. A lock would fix it.",s:4,ev:"both pass the limit check"}]},
 {id:3,name:"Rohan Verma",email:"rohan@example.com",github:"rohan-v",job:1,exp:1,status:"Reviewed",score:52,conf:.6,rec:"Needs more evidence",skills:["python"],dims:{Understanding:50,Reasoning:55,Debugging:48,Communication:60},summary:"Could not explain key design choices in his own code.",turns:[{q:"Why a deque over a list for the expiry loop?",a:"It is faster I think.",s:2,ev:"It is faster I think"}]},
 {id:4,name:"Meera Iyer",email:"meera@example.com",github:"meera-i",job:2,exp:0,status:"New",score:0,conf:0,rec:"Not assessed",skills:["javascript","html/css"],dims:{Understanding:0,Reasoning:0,Debugging:0,Communication:0},summary:"Assessment not started.",turns:[]}]};
let D;try{D=JSON.parse(localStorage.getItem(KEY))||SEED}catch(e){D=SEED}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(D))}catch(e){}};
document.documentElement.dataset.theme=D.theme||"dark";

const $=s=>document.querySelector(s),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const jt=id=>(D.jobs.find(j=>j.id==id)||{}).title||"—",st=s=>({Shortlisted:"",Interview:"b",Reviewed:"m",New:"m",Rejected:"n"}[s]||"m");
const bar=v=>`<div class="bar"><i style="width:${v}%"></i></div>`,chips=s=>(Array.isArray(s)?s:s.split(",")).map(x=>`<span class="chip">${esc(x.trim())}</span>`).join("");
const go=p=>location.href=p+".html",pad=n=>String(n).padStart(2,"0");
const toast=m=>{const t=$("#toast");t.textContent=m;t.classList.remove("hide");clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.add("hide"),2200)};
const head=(n,title,lead,btn="")=>`<div class="head"><div><div class="eb">Field notes / ${n} / Recruiter desk</div><h1>${title}<s>.</s></h1><p class="lead">${lead}</p></div>${btn}</div>`;
const sec=(l,r="")=>`<div class="sec"><span>${l}</span><em>${r}</em></div>`;
const foot=()=>`<div class="ft"><div><b>↳ THE SIGNAL IS IN THE EXPLANATION</b>Every recommendation stays connected to what a candidate actually explained.</div><a href="shortlist.html">View shortlist →</a></div>`;
const sel=()=>{const id=+new URLSearchParams(location.search).get("id")||D.sel;return D.apps.find(a=>a.id==id)||D.apps[0]};
const openC=id=>{D.sel=id;save();location.href="candidate.html?id="+id},openR=id=>{D.sel=id;save();location.href="ai-report.html?id="+id};
function setSt(id,s){D.apps.find(a=>a.id==id).status=s;save();toast("Status: "+s);render()}
function logout(){D.user=null;save();go("login")}

const NAV=[["WORKSPACE",[["dashboard","▦","Dashboard"],["company-profile","+","Company profile"],["jobs","☷","Jobs"],["applicants","◉","Applicants"],["candidate","⌘","Candidate profile"]]],
           ["ASSESSMENT",[["assessments","≡","Assessments"],["ai-report","◉","AI report"],["compare","⌘","Compare"],["shortlist","☷","Shortlist"],["graph","⌘","Knowledge graph"]]]];
const LOGO='<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ProofHire logo"><defs><linearGradient id="phb" x1="0" y1="100" x2="100" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#4f5bff"/><stop offset=".5" stop-color="#ff3d9a"/><stop offset="1" stop-color="#ff8a1e"/></linearGradient><linearGradient id="phl" x1="43" y1="69" x2="75" y2="32" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#a63fe0"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient></defs><rect x="1.5" y="1.5" width="97" height="97" rx="25" fill="#06070a" stroke="url(#phb)" stroke-width="3"/><circle cx="74.6" cy="31.9" r="14.5" fill="none" stroke="#ff8a1e" stroke-opacity=".3" stroke-width="2.5"/><line x1="25.4" y1="51.3" x2="43.4" y2="69.4" stroke="#6a5ae6" stroke-width="5"/><line x1="43.4" y1="69.4" x2="74.6" y2="31.9" stroke="url(#phl)" stroke-width="6.5"/><circle cx="25.4" cy="51.3" r="8" fill="#06070a" stroke="#4f5bff" stroke-width="3"/><circle cx="43.4" cy="69.4" r="8" fill="#06070a" stroke="#b23cd6" stroke-width="3"/><circle cx="74.6" cy="31.9" r="9" fill="#ff8a1e"/></svg>';
let CUR,PAGE;
function shell(){
  const s=$("#side"),t=$("#top");if(!s)return;
  s.innerHTML=`<div class="brand"><a class="logo" href="dashboard.html" aria-label="ProofHire home">${LOGO}</a><b>PROOFHIRE</b><button class="col" onclick="document.body.classList.toggle('mini')" aria-label="Collapse sidebar">‹</button></div>`+
   NAV.map(([g,l])=>`<div class="grp">${g}</div>`+l.map(([k,i,n])=>`<a class="n ${k===PAGE?"on":""}" href="${k}.html"><i>${i}</i><span class="t">${n}</span></a>`).join("")).join("")+
   `<div class="sys"><small>System mode</small><span class="dot"></span><span class="t">Demo mode</span><button class="out t" onclick="logout()">Log out</button></div>`;
  const name=NAV.flatMap(g=>g[1]).find(n=>n[0]===PAGE)[2];
  t.innerHTML=`<div class="crumb"><a class="h" href="dashboard.html">ProofHire</a> › <b>${name}</b> › <span>${esc(jt(D.jobId))}</span><span style="margin-left:12px;font-size:14px">Role</span>
   <select id="role" aria-label="Role" onchange="D.jobId=+this.value;save();render()">${D.jobs.map(j=>`<option value="${j.id}" ${j.id==D.jobId?"selected":""}>${esc(j.title)}</option>`).join("")}</select></div>
   <span class="pill">● Demo</span><button class="ib" onclick="D.theme=D.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=D.theme;save()" aria-label="Toggle theme">☀</button><a class="btn" href="jobs.html">+ Create Job ↗</a>`;
}
function render(){shell();$("#v").innerHTML=CUR();}
function boot(page,fn){PAGE=page;CUR=fn;if(!D.user&&page!=="login"){location.replace("login.html");return}render()}

/* Clickable cards: any element with data-open="c:ID | r:ID | role:ID | page-name" */
function nav(s){const[k,v]=s.split(":");if(k==="c")openC(+v);else if(k==="r")openR(+v);else if(k==="role"){D.jobId=+v;save();go("applicants")}else go(k)}
document.addEventListener("click",e=>{const el=e.target.closest("[data-open]");if(!el||e.target.closest("button,select,a,input,textarea,label"))return;nav(el.dataset.open)});
document.addEventListener("keydown",e=>{if(e.key==="Enter"&&e.target.matches("[data-open]"))nav(e.target.dataset.open)});

/* Knowledge-graph numbers, derived from the portal data (jobs, candidates, skills, experience, projects). */
function gdata(){
 const open=D.jobs.filter(j=>j.status==="Open"),sk={};
 D.apps.forEach(a=>a.skills.forEach(s=>{s=s.trim().toLowerCase();sk[s]=(sk[s]||0)+1}));
 D.jobs.forEach(j=>j.skills.split(",").forEach(s=>{s=s.trim().toLowerCase();if(s&&s!=="—")sk[s]=sk[s]||0}));
 const exp=D.apps.filter(a=>a.exp>0).map(a=>({a,n:Math.ceil(a.exp/2)})),
  proj=D.apps.filter(a=>a.score).map(a=>({a,t:(D.assess.find(x=>x.job==a.job)||{}).title||"Assessment task"}));
 const c={joblead:open.length,candidate:D.apps.length,skill:Object.keys(sk).length,experience:exp.reduce((s,e)=>s+e.n,0),project:proj.length};
 c.total=c.joblead+c.candidate+c.skill+c.experience+c.project;
 return{c,open,sk,exp,proj};
}
