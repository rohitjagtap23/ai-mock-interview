const API_URL = 'http://127.0.0.1:5000';
let questions = [];
let currentQuestion = 0;
let evaluations = [];
let interviewMode = 'text';
let recognition = null;
let isListening = false;
let finalTranscript = '';

const $ = (id) => document.getElementById(id);
const esc = (value) => {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
};
const show = (id, visible = true) => {
    const el = $(id);
    if (el) el.classList.toggle('hidden', !visible);
};
const apiJson = async (url, options = {}) => {
    const response = await fetch(url, options);
    let data;
    try { data = await response.json(); } catch { data = {}; }
    if (!response.ok || data.status === 'error') {
        throw new Error(data.message || data.error || `Request failed (${response.status})`);
    }
    return data;
};

async function startInterview(mode = 'text') {
    interviewMode = mode;
    evaluations = [];
    currentQuestion = 0;
    const role = $('role')?.value.trim() || localStorage.getItem('career_target_role') || 'Java Developer';
    localStorage.setItem('career_target_role', role);
    if ($('startStatus')) $('startStatus').textContent = 'Generating personalized interview...';

    try {
        const data = await apiJson(`${API_URL}/api/interview?role=${encodeURIComponent(role)}`);
        questions = data.questions || [];
        if (!questions.length) throw new Error('No questions were generated. Check the backend and Gemini configuration.');
        show('interviewModeSection', false);
        show('interviewSection', true);
        show('textAnswerSection', mode === 'text');
        show('voiceAnswerSection', mode === 'voice');
        showQuestion();
    } catch (error) {
        console.error(error);
        if ($('startStatus')) {
            $('startStatus').textContent = error.message;
            $('startStatus').className = 'error';
        }
    }
}

function showQuestion() {
    const question = questions[currentQuestion];
    if (!question) return;
    $('questionNumber').textContent = `Question ${currentQuestion + 1} of ${questions.length}`;
    $('questionSkill').textContent = `Skill: ${question.skill || 'General'}`;
    $('question').textContent = question.question || '';
    if ($('answer')) $('answer').value = '';
    if ($('transcript')) $('transcript').textContent = '';
    if ($('voiceStatus')) $('voiceStatus').textContent = 'Ready';
    show('evaluationBox', false);
    show('nextButton', false);
    show('submitAnswer', interviewMode === 'text');
    if ($('submitVoiceButton')) $('submitVoiceButton').disabled = true;
}

async function evaluateCurrentAnswer(answerText) {
    const question = questions[currentQuestion];
    const answer = (answerText || '').trim();
    if (!answer) { alert('Please provide an answer first.'); return false; }

    const submit = $('submitAnswer');
    if (submit) { submit.disabled = true; submit.textContent = 'AI is evaluating...'; }

    try {
        const data = await apiJson(`${API_URL}/api/evaluate`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ question:question.question, answer, skill:question.skill || 'General' })
        });
        const evaluation = data.evaluation || {};
        evaluations.push({ question:question.question, answer, skill:question.skill || 'General', evaluation });
        displayEvaluation(evaluation);
        return true;
    } catch (error) {
        console.error(error);
        alert(error.message);
        return false;
    } finally {
        if (submit) { submit.disabled = false; submit.textContent = 'Submit Answer'; }
    }
}

async function submitTextAnswer() { await evaluateCurrentAnswer($('answer')?.value || ''); }

function displayEvaluation(evaluation) {
    $('score').textContent = `${evaluation.score ?? 0}/10`;
    $('technicalCorrectness').textContent = evaluation.technical_correctness || '';
    $('communication').textContent = evaluation.communication || '';
    $('practicalKnowledge').textContent = evaluation.practical_knowledge || '';
    $('feedback').textContent = evaluation.feedback || '';
    const renderList = (id, values) => {
        $(id).innerHTML = (Array.isArray(values) ? values : []).map((item) => `<li>${esc(item)}</li>`).join('');
    };
    renderList('strengths', evaluation.strengths);
    renderList('missingConcepts', evaluation.missing_concepts);
    show('evaluationBox', true);
    show('nextButton', true);
    show('submitAnswer', false);
}

async function nextQuestion() {
    if (evaluations.length <= currentQuestion) {
        alert('Submit your answer and wait for the evaluation first.');
        return;
    }
    if (currentQuestion < questions.length - 1) {
        currentQuestion += 1;
        showQuestion();
    } else {
        await generateSkillGap();
    }
}

async function generateSkillGap() {
    show('nextButton', false);
    $('question').textContent = 'Analyzing your interview performance...';
    try {
        const data = await apiJson(`${API_URL}/api/skill-gap`, {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ evaluations })
        });
        const profile = data.skill_profile || data.skill_gaps || [];
        localStorage.setItem('latest_skill_gap', JSON.stringify(profile));
        await saveInterviewIfPossible();
        displaySkillGap(profile);
        show('interviewSection', false);
        show('skillGapSection', true);
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

function displaySkillGap(profile) {
    const container = $('skillGapContainer');
    if (!container) return;
    container.innerHTML = profile.length ? profile.map((item) => `
        <div class="gap">
            <h3>${esc(item.skill)}</h3>
            <strong>${esc(item.average_score)}/10</strong>
            <p>${esc(item.level || '')}</p>
            <p><b>Missing:</b> ${esc((item.missing_concepts || []).join(', ') || 'None')}</p>
        </div>
    `).join('') : '<div class="empty">No skill gaps were detected.</div>';
}

function startVoiceRecording() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('Speech recognition is not supported in this browser. Use Google Chrome.');
        return;
    }
    if (isListening) return;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';
    finalTranscript = '';
    isListening = true;
    $('voiceStatus').textContent = 'Listening...';
    $('startVoiceButton').disabled = true;
    $('stopVoiceButton').disabled = false;
    recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const text = event.results[i][0].transcript;
            if (event.results[i].isFinal) finalTranscript += ` ${text}`;
            else interim += ` ${text}`;
        }
        $('transcript').textContent = `${finalTranscript} ${interim}`.trim();
    };
    recognition.onerror = (event) => { $('voiceStatus').textContent = `Voice error: ${event.error}`; };
    recognition.onend = () => {
        if (isListening) {
            try { recognition.start(); } catch (_) { /* browser may already be restarting */ }
        }
    };
    recognition.start();
}

function stopVoiceRecording() {
    isListening = false;
    if (recognition) { recognition.onend = null; recognition.stop(); }
    $('voiceStatus').textContent = 'Recording stopped';
    $('startVoiceButton').disabled = false;
    $('stopVoiceButton').disabled = true;
    $('submitVoiceButton').disabled = !finalTranscript.trim();
}

async function submitVoiceAnswer() {
    stopVoiceRecording();
    const text = finalTranscript.trim();
    if (text) await evaluateCurrentAnswer(text);
}

async function analyzeMarket() {
    const role = $('role').value.trim();
    const location = $('location').value.trim() || 'India';
    if (!role) { alert('Enter a target role.'); return; }
    localStorage.setItem('career_target_role', role);
    localStorage.setItem('career_location', location);
    $('marketMessage').textContent = 'Analyzing live jobs...';
    try {
        const data = await apiJson(`${API_URL}/api/career-intelligence?role=${encodeURIComponent(role)}&location=${encodeURIComponent(location)}`);
        $('jobsFound').textContent = `${data.jobs_analyzed ?? data.jobs_found ?? 0} jobs analyzed`;
        $('skillsContainer').innerHTML = (data.market_skills || []).map((skill) => `<span class="pill">${esc(skill.skill)} · ${esc(skill.job_count)}</span>`).join('');
        $('marketMessage').textContent = 'Market analysis complete.';
        $('marketMessage').className = 'success';
    } catch (error) {
        $('marketMessage').textContent = error.message;
        $('marketMessage').className = 'error';
    }
}

async function saveInterviewIfPossible() {
    try {
        if (typeof getSession !== 'function') return;
        const { session } = await getSession();
        if (!session) return;
        await fetch(`${API_URL}/api/interview/save`, {
            method:'POST',
            headers:{'Content-Type':'application/json',Authorization:`Bearer ${session.access_token}`},
            body:JSON.stringify({ role:localStorage.getItem('career_target_role') || 'Java Developer', evaluations })
        });
    } catch (error) {
        console.warn('Interview save skipped:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if ($('analyzeButton')) $('analyzeButton').addEventListener('click', analyzeMarket);
    if ($('startInterviewButton')) $('startInterviewButton').addEventListener('click', () => startInterview('text'));
    if ($('voiceInterviewButton')) $('voiceInterviewButton').addEventListener('click', () => startInterview('voice'));
    if ($('submitAnswer')) $('submitAnswer').addEventListener('click', submitTextAnswer);
    if ($('nextButton')) $('nextButton').addEventListener('click', nextQuestion);
    if ($('startVoiceButton')) $('startVoiceButton').addEventListener('click', startVoiceRecording);
    if ($('stopVoiceButton')) $('stopVoiceButton').addEventListener('click', stopVoiceRecording);
    if ($('submitVoiceButton')) $('submitVoiceButton').addEventListener('click', submitVoiceAnswer);
    if ($('role') && localStorage.getItem('career_target_role')) $('role').value = localStorage.getItem('career_target_role');
    if ($('location') && localStorage.getItem('career_location')) $('location').value = localStorage.getItem('career_location');
});
