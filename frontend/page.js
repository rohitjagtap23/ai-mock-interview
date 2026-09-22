const API_URL = 'http://127.0.0.1:5000';
const byId = (id) => document.getElementById(id);
const escHtml = (value) => { const d=document.createElement('div'); d.textContent=value??''; return d.innerHTML; };

async function api(url, options={}) {
    const response = await fetch(url, options);
    let data = {};
    try { data = await response.json(); } catch (_) {}
    if (!response.ok || data.status === 'error') throw new Error(data.message || data.error || `Request failed (${response.status})`);
    return data;
}

async function requireLogin() {
    const { session } = await getSession();
    if (!session) { window.location.href = 'login.html'; return null; }
    return session;
}

function activeNav() {
    const current = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.sidebar-nav a[data-page]').forEach((a) => {
        a.classList.toggle('active', a.dataset.page === current);
    });
}

async function loadDashboard() {
    const session = await requireLogin(); if (!session) return;
    try {
        const data = await api(`${API_URL}/api/dashboard`, {headers:{Authorization:`Bearer ${session.access_token}`}});
        byId('stats').innerHTML = [
            ['Interviews',data.interview_count||0],['Average Score',`${data.average_score||0}/10`],['Skills Tracked',data.skills_tracked||0],['Level',data.career_level||'Beginner']
        ].map(([label,value])=>`<div class="card"><div class="muted">${label}</div><div class="stat">${escHtml(value)}</div></div>`).join('');
        const skills = data.skill_progress || [];
        byId('skills').innerHTML = skills.length ? skills.map(s=>{const score=Number(s.score??s.average_score??0);return `<div style="margin-bottom:16px"><b>${escHtml(s.skill||'Skill')}</b><span style="float:right">${score.toFixed(1)}/10</span><div class="bar"><div style="width:${Math.max(0,Math.min(100,score*10))}%"></div></div></div>`}).join('') : '<div class="empty">Complete an interview to track skills.</div>';
        const latest = data.latest_interview;
        byId('recent').innerHTML = latest ? `<div class="card"><b>${escHtml(latest.role||'Interview')}</b><p>Score: ${escHtml(latest.total_score??0)}/10</p><p class="muted">${latest.created_at ? new Date(latest.created_at).toLocaleString() : ''}</p></div>` : '<div class="empty">No interviews yet.</div>';
    } catch (e) { byId('stats').innerHTML=`<div class="card error">${escHtml(e.message)}</div>`; }
}

async function loadHistory() {
    const session = await requireLogin(); if (!session) return;
    try {
        const data = await api(`${API_URL}/api/interviews`, {headers:{Authorization:`Bearer ${session.access_token}`}});
        const items=data.interviews||[];
        byId('history').innerHTML=items.length?`<div class="table-wrap"><table class="table"><thead><tr><th>Role</th><th>Score</th><th>Date</th><th></th></tr></thead><tbody>${items.map(i=>`<tr><td>${escHtml(i.role||'Interview')}</td><td>${escHtml(i.total_score??0)}/10</td><td>${i.created_at?new Date(i.created_at).toLocaleString():''}</td><td><a class="btn" href="interview-details.html?id=${encodeURIComponent(i.id)}">View</a></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">No interview history yet.</div>';
    } catch(e) { byId('history').innerHTML=`<div class="error">${escHtml(e.message)}</div>`; }
}

async function loadInterviewDetails() {
    const session=await requireLogin(); if(!session)return;
    const id=new URLSearchParams(location.search).get('id'); if(!id){byId('details').textContent='Missing interview id.';return;}
    try { const d=await api(`${API_URL}/api/interviews/${encodeURIComponent(id)}`,{headers:{Authorization:`Bearer ${session.access_token}`}}); byId('details').innerHTML=`<h2>${escHtml(d.role||'Interview')}</h2><p>Score: <b>${escHtml(d.total_score??d.score??0)}/10</b></p><pre style="white-space:pre-wrap">${escHtml(JSON.stringify(d,null,2))}</pre>`; } catch(e){byId('details').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}
}

async function loadProfile() {
    const session=await requireLogin(); if(!session)return;
    const user=await getCurrentUser();
    if(!user)return;
    byId('email').value=user.email||'';
    const profile=await getUserProfile();
    if(profile){byId('name').value=profile.name||'';byId('target_role').value=profile.target_role||'Java Developer';byId('location').value=profile.location||'Pune';byId('experience_level').value=profile.experience_level||'Beginner';}
}

async function saveProfilePage() {
    const result=await saveProfile({name:byId('name').value,target_role:byId('target_role').value,location:byId('location').value,experience_level:byId('experience_level').value,skills:[]});
    byId('profileMessage').textContent=result.error?result.error.message:'Profile saved successfully.';
    byId('profileMessage').className=result.error?'error':'success';
    if(!result.error){localStorage.setItem('career_target_role',byId('target_role').value);localStorage.setItem('career_location',byId('location').value);}
}

async function loadMarket() {
    await requireLogin();
    const role=localStorage.getItem('career_target_role')||'Java Developer'; const location=localStorage.getItem('career_location')||'Pune';
    byId('role').value=role;byId('location').value=location;
}
async function runMarket(){
    byId('marketOut').textContent='Analyzing live jobs...';
    try{const role=byId('role').value.trim();const location=byId('location').value.trim()||'India';const d=await api(`${API_URL}/api/career-intelligence?role=${encodeURIComponent(role)}&location=${encodeURIComponent(location)}`);localStorage.setItem('career_target_role',role);localStorage.setItem('career_location',location);byId('marketOut').innerHTML=`<h2>${escHtml(d.jobs_analyzed||0)} jobs analyzed</h2>${(d.market_skills||[]).map(s=>`<span class="pill">${escHtml(s.skill)} · ${escHtml(s.job_count)}</span>`).join('')}`;}catch(e){byId('marketOut').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}
}

async function runJobMatch(){
    const session=await requireLogin();if(!session)return;byId('matchOut').textContent='Finding matching jobs...';
    try{const d=await api(`${API_URL}/api/jobs/match`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${session.access_token}`},body:JSON.stringify({role:byId('role').value,location:byId('location').value})});const jobs=d.matches||d.jobs||[];byId('matchOut').innerHTML=jobs.length?jobs.map(j=>`<div class="card"><h3>${escHtml(j.job_title||j.title||'Job')}</h3><p>${escHtml(j.company||'')} · ${escHtml(j.location||'')}</p><p>Match: ${escHtml(j.match_score??0)}%</p>${j.job_url?`<a class="btn" target="_blank" rel="noopener" href="${escHtml(j.job_url)}">View Job</a>`:''}</div>`).join(''):'<div class="empty">No matches found.</div>';}catch(e){byId('matchOut').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}
}

function renderSkillGap(){const a=JSON.parse(localStorage.getItem('latest_skill_gap')||'[]');byId('gapOut').innerHTML=a.length?a.map(x=>`<div class="gap"><h3>${escHtml(x.skill)}</h3><p>Score: <b>${escHtml(x.average_score??0)}/10</b> — ${escHtml(x.level||'')}</p><p><b>Missing concepts:</b> ${escHtml((x.missing_concepts||[]).join(', ')||'None')}</p><p>${escHtml(x.feedback||'')}</p></div>`).join(''):'<div class="empty">Complete an interview first to generate skill gaps.</div>';}

async function runRoadmap(){const gaps=JSON.parse(localStorage.getItem('latest_skill_gap')||'[]');if(!gaps.length){byId('roadmapOut').innerHTML='<div class="empty">Complete an interview first.</div>';return;}byId('roadmapOut').textContent='Generating roadmap...';try{const d=await api(`${API_URL}/api/roadmap`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:localStorage.getItem('career_target_role')||'Java Developer',skill_gaps:gaps})});localStorage.setItem('latest_roadmap',JSON.stringify(d));const weeks=d.weeks||d.roadmap||[];byId('roadmapOut').innerHTML=weeks.map(w=>`<div class="card"><h2>Week ${escHtml(w.week??'')} — ${escHtml(w.title||'')}</h2><p>${escHtml(w.goal||w.learning_focus||'')}</p><p><b>Why it matters:</b> ${escHtml(w.why_it_matters||w.why||'')}</p><p><b>Practice:</b> ${escHtml(w.practice_task||'')}</p></div>`).join('');}catch(e){byId('roadmapOut').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}}

async function runResources(){const session=await requireLogin();if(!session)return;const skill=byId('skill').value.trim()||'Java';byId('resourceOut').textContent='Searching...';try{const d=await api(`${API_URL}/api/resources?skill=${encodeURIComponent(skill)}`);const items=d.resources||[];byId('resourceOut').innerHTML=items.length?items.map(r=>`<div class="card"><h3>${escHtml(r.title||r.name||'Resource')}</h3><p>${escHtml(r.description||'')}</p>${r.url?`<a class="btn" target="_blank" rel="noopener" href="${escHtml(r.url)}">Open Resource</a>`:''}</div>`).join(''):'<div class="empty">No resources returned.</div>';}catch(e){byId('resourceOut').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}}

async function analyzeResume(){const file=byId('resumeFile').files[0];if(!file){byId('resumeOut').textContent='Choose a PDF first.';return;}const session=await requireLogin();if(!session)return;byId('resumeOut').textContent='Reading resume...';try{const buffer=await file.arrayBuffer();const pdf=await pdfjsLib.getDocument({data:buffer}).promise;let text='';for(let i=1;i<=pdf.numPages;i+=1){const page=await pdf.getPage(i);const content=await page.getTextContent();text+=content.items.map(x=>x.str).join(' ')+'\n';}const d=await api(`${API_URL}/api/resume/analyze`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${session.access_token}`},body:JSON.stringify({resume_text:text,target_role:localStorage.getItem('career_target_role')||'Java Developer'})});byId('resumeOut').innerHTML=`<h2>Resume Score: ${escHtml(d.score??d.resume_score??0)}/100</h2><p><b>Detected skills:</b> ${escHtml((d.skills||d.detected_skills||[]).join(', ')||'None')}</p><p><b>Missing market skills:</b> ${escHtml((d.missing_market_skills||[]).join(', ')||'None')}</p>`;}catch(e){byId('resumeOut').innerHTML=`<div class="error">${escHtml(e.message)}</div>`;}}

document.addEventListener('DOMContentLoaded',()=>{
    activeNav();
    const page=document.body.dataset.page;
    if(page==='dashboard')loadDashboard();
    if(page==='history')loadHistory();
    if(page==='details')loadInterviewDetails();
    if(page==='profile')loadProfile();
    if(page==='market')loadMarket();
    if(page==='skill-gap')renderSkillGap();
    if(page==='resources'){}
    if(page==='roadmap')runRoadmap();
    if(byId('saveProfileButton'))byId('saveProfileButton').addEventListener('click',saveProfilePage);
    if(byId('marketButton'))byId('marketButton').addEventListener('click',runMarket);
    if(byId('matchButton'))byId('matchButton').addEventListener('click',runJobMatch);
    if(byId('roadmapButton'))byId('roadmapButton').addEventListener('click',runRoadmap);
    if(byId('resourceButton'))byId('resourceButton').addEventListener('click',runResources);
    if(byId('resumeButton'))byId('resumeButton').addEventListener('click',analyzeResume);
});
