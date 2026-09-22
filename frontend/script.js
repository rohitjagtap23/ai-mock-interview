const API_URL = 'https://ai-career-interviewer-backend.onrender.com';

let questions = [];
let currentQuestion = 0;
let evaluations = [];
let interviewMode = 'text';

let recognition = null;
let isListening = false;
let finalTranscript = '';



/* =========================================================
   HELPERS
========================================================= */

const $ = (id) => document.getElementById(id);


const esc = (value) => {

    const div = document.createElement('div');

    div.textContent = value ?? '';

    return div.innerHTML;

};


const show = (id, visible = true) => {

    const el = $(id);

    if (el) {
        el.classList.toggle('hidden', !visible);
    }

};



/* =========================================================
   SUPABASE SESSION
========================================================= */

async function getAuthSession() {

    /*
     * auth.js already provides getSession().
     * We use it here so every protected backend
     * request receives the Supabase access token.
     */

    if (typeof getSession !== 'function') {

        throw new Error(
            'Authentication system is not loaded. Please refresh the page.'
        );

    }


    const result = await getSession();


    if (!result) {

        throw new Error(
            'Unable to get Supabase session.'
        );

    }


    const session = result.session;


    if (!session || !session.access_token) {

        throw new Error(
            'Your session has expired. Please log in again.'
        );

    }


    return session;

}



/* =========================================================
   API REQUEST HELPER
========================================================= */

const apiJson = async (
    url,
    options = {},
    requiresAuth = false
) => {

    const requestOptions = {
        ...options,
        headers: {
            ...(options.headers || {})
        }
    };


    /*
     * Protected endpoints receive the current
     * Supabase access token.
     */

    if (requiresAuth) {

        const session =
            await getAuthSession();


        requestOptions.headers.Authorization =
            `Bearer ${session.access_token}`;

    }


    const response =
        await fetch(
            url,
            requestOptions
        );


    let data;

    try {

        data =
            await response.json();

    } catch {

        data = {};

    }


    if (
        !response.ok ||
        data.status === 'error'
    ) {

        throw new Error(
            data.message ||
            data.error ||
            `Request failed (${response.status})`
        );

    }


    return data;

};



/* =========================================================
   START INTERVIEW
========================================================= */

async function startInterview(
    mode = 'text'
) {

    interviewMode = mode;

    evaluations = [];

    currentQuestion = 0;


    const role =
        $('role')?.value.trim() ||
        localStorage.getItem(
            'career_target_role'
        ) ||
        'Java Developer';


    localStorage.setItem(
        'career_target_role',
        role
    );


    if ($('startStatus')) {

        $('startStatus').textContent =
            'Generating personalized interview...';

        $('startStatus').className = '';

    }


    try {

        /*
         * The interview-generation endpoint
         * does not currently require authentication.
         */

        const data =
            await apiJson(
                `${API_URL}/api/interview?role=${encodeURIComponent(role)}`
            );


        questions =
            data.questions || [];


        if (!questions.length) {

            throw new Error(
                'No questions were generated. Check the backend and Gemini configuration.'
            );

        }


        show(
            'interviewModeSection',
            false
        );


        show(
            'interviewSection',
            true
        );


        show(
            'textAnswerSection',
            mode === 'text'
        );


        show(
            'voiceAnswerSection',
            mode === 'voice'
        );


        showQuestion();

    } catch (error) {

        console.error(
            'Start interview error:',
            error
        );


        if ($('startStatus')) {

            $('startStatus').textContent =
                error.message;

            $('startStatus').className =
                'error';

        }

    }

}



/* =========================================================
   SHOW CURRENT QUESTION
========================================================= */

function showQuestion() {

    const question =
        questions[currentQuestion];


    if (!question) {
        return;
    }


    $('questionNumber').textContent =
        `Question ${currentQuestion + 1} of ${questions.length}`;


    $('questionSkill').textContent =
        `Skill: ${question.skill || 'General'}`;


    $('question').textContent =
        question.question || '';


    if ($('answer')) {

        $('answer').value = '';

    }


    if ($('transcript')) {

        $('transcript').textContent = '';

    }


    if ($('voiceStatus')) {

        $('voiceStatus').textContent =
            'Ready';

    }


    show(
        'evaluationBox',
        false
    );


    show(
        'nextButton',
        false
    );


    show(
        'submitAnswer',
        interviewMode === 'text'
    );


    if ($('submitVoiceButton')) {

        $('submitVoiceButton').disabled =
            true;

    }

}



/* =========================================================
   EVALUATE CURRENT ANSWER
========================================================= */

async function evaluateCurrentAnswer(
    answerText
) {

    const question =
        questions[currentQuestion];


    const answer =
        (answerText || '').trim();


    if (!answer) {

        alert(
            'Please provide an answer first.'
        );

        return false;

    }


    const submit =
        $('submitAnswer');


    if (submit) {

        submit.disabled = true;

        submit.textContent =
            'AI is evaluating...';

    }


    try {

        const data =
            await apiJson(
                `${API_URL}/api/evaluate`,
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({

                        question:
                            question.question,

                        answer,

                        skill:
                            question.skill ||
                            'General'

                    })

                }
            );


        const evaluation =
            data.evaluation || {};


        evaluations.push({

            question:
                question.question,

            answer,

            skill:
                question.skill ||
                'General',

            evaluation

        });


        displayEvaluation(
            evaluation
        );


        return true;

    } catch (error) {

        console.error(
            'Evaluation error:',
            error
        );


        alert(
            error.message
        );


        return false;

    } finally {

        if (submit) {

            submit.disabled =
                false;

            submit.textContent =
                'Submit Answer';

        }

    }

}



/* =========================================================
   TEXT ANSWER
========================================================= */

async function submitTextAnswer() {

    await evaluateCurrentAnswer(
        $('answer')?.value || ''
    );

}



/* =========================================================
   DISPLAY EVALUATION
========================================================= */

function displayEvaluation(
    evaluation
) {

    if ($('score')) {

        $('score').textContent =
            `${evaluation.score ?? 0}/10`;

    }


    if ($('technicalCorrectness')) {

        $('technicalCorrectness').textContent =
            evaluation.technical_correctness ||
            '';

    }


    if ($('communication')) {

        $('communication').textContent =
            evaluation.communication ||
            '';

    }


    if ($('practicalKnowledge')) {

        $('practicalKnowledge').textContent =
            evaluation.practical_knowledge ||
            '';

    }


    if ($('feedback')) {

        $('feedback').textContent =
            evaluation.feedback ||
            '';

    }


    const renderList =
        (id, values) => {

            const element = $(id);

            if (!element) {
                return;
            }


            element.innerHTML =
                (
                    Array.isArray(values)
                        ? values
                        : []
                )
                .map(
                    (item) =>
                        `<li>${esc(item)}</li>`
                )
                .join('');

        };


    renderList(
        'strengths',
        evaluation.strengths
    );


    renderList(
        'missingConcepts',
        evaluation.missing_concepts
    );


    show(
        'evaluationBox',
        true
    );


    show(
        'nextButton',
        true
    );


    show(
        'submitAnswer',
        false
    );

}



/* =========================================================
   NEXT QUESTION
========================================================= */

async function nextQuestion() {

    if (
        evaluations.length <=
        currentQuestion
    ) {

        alert(
            'Submit your answer and wait for the evaluation first.'
        );

        return;

    }


    if (
        currentQuestion <
        questions.length - 1
    ) {

        currentQuestion += 1;

        showQuestion();

    } else {

        await generateSkillGap();

    }

}



/* =========================================================
   GENERATE SKILL GAP
========================================================= */

async function generateSkillGap() {

    show(
        'nextButton',
        false
    );


    if ($('question')) {

        $('question').textContent =
            'Analyzing your interview performance...';

    }


    try {

        const data =
            await apiJson(
                `${API_URL}/api/skill-gap`,
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({
                        evaluations
                    })

                }
            );


        const profile =
            data.skill_profile ||
            data.skill_gaps ||
            [];


        localStorage.setItem(
            'latest_skill_gap',
            JSON.stringify(profile)
        );


        /*
         * Save the complete interview after
         * the skill-gap calculation succeeds.
         */

        await saveInterviewIfPossible();


        displaySkillGap(
            profile
        );


        show(
            'interviewSection',
            false
        );


        show(
            'skillGapSection',
            true
        );

    } catch (error) {

        console.error(
            'Skill gap error:',
            error
        );


        alert(
            error.message
        );

    }

}



/* =========================================================
   DISPLAY SKILL GAP
========================================================= */

function displaySkillGap(
    profile
) {

    const container =
        $('skillGapContainer');


    if (!container) {
        return;
    }


    if (
        !Array.isArray(profile) ||
        !profile.length
    ) {

        container.innerHTML =
            '<div class="empty">No skill gaps were detected.</div>';

        return;

    }


    container.innerHTML =
        profile
        .map(
            (item) => `

                <div class="gap">

                    <h3>
                        ${esc(item.skill)}
                    </h3>

                    <strong>
                        ${esc(item.average_score)}/10
                    </strong>

                    <p>
                        ${esc(item.level || '')}
                    </p>

                    <p>

                        <b>
                            Missing:
                        </b>

                        ${esc(
                            (
                                item.missing_concepts ||
                                []
                            ).join(', ') ||
                            'None'
                        )}

                    </p>

                </div>

            `
        )
        .join('');

}



/* =========================================================
   VOICE RECOGNITION
========================================================= */

function startVoiceRecording() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        alert(
            'Speech recognition is not supported in this browser. Use Google Chrome.'
        );

        return;

    }


    if (isListening) {
        return;
    }


    recognition =
        new SpeechRecognition();


    recognition.continuous =
        true;


    recognition.interimResults =
        true;


    recognition.lang =
        'en-IN';


    finalTranscript =
        '';


    isListening =
        true;


    if ($('voiceStatus')) {

        $('voiceStatus').textContent =
            'Listening...';

    }


    if ($('startVoiceButton')) {

        $('startVoiceButton').disabled =
            true;

    }


    if ($('stopVoiceButton')) {

        $('stopVoiceButton').disabled =
            false;

    }


    recognition.onresult =
        (event) => {

            let interim =
                '';


            for (
                let i = event.resultIndex;
                i < event.results.length;
                i += 1
            ) {

                const text =
                    event.results[i][0].transcript;


                if (
                    event.results[i].isFinal
                ) {

                    finalTranscript +=
                        ` ${text}`;

                } else {

                    interim +=
                        ` ${text}`;

                }

            }


            if ($('transcript')) {

                $('transcript').textContent =
                    `${finalTranscript} ${interim}`.trim();

            }

        };


    recognition.onerror =
        (event) => {

            console.error(
                'Voice recognition error:',
                event.error
            );


            if ($('voiceStatus')) {

                $('voiceStatus').textContent =
                    `Voice error: ${event.error}`;

            }

        };


    recognition.onend =
        () => {

            if (isListening) {

                try {

                    recognition.start();

                } catch (_) {

                    /*
                     * Browser may already be restarting.
                     */

                }

            }

        };


    recognition.start();

}



/* =========================================================
   STOP VOICE
========================================================= */

function stopVoiceRecording() {

    isListening =
        false;


    if (recognition) {

        recognition.onend =
            null;


        try {

            recognition.stop();

        } catch (_) {

            /*
             * Recognition may already be stopped.
             */

        }

    }


    if ($('voiceStatus')) {

        $('voiceStatus').textContent =
            'Recording stopped';

    }


    if ($('startVoiceButton')) {

        $('startVoiceButton').disabled =
            false;

    }


    if ($('stopVoiceButton')) {

        $('stopVoiceButton').disabled =
            true;

    }


    if ($('submitVoiceButton')) {

        $('submitVoiceButton').disabled =
            !finalTranscript.trim();

    }

}



/* =========================================================
   SUBMIT VOICE ANSWER
========================================================= */

async function submitVoiceAnswer() {

    stopVoiceRecording();


    const text =
        finalTranscript.trim();


    if (!text) {

        alert(
            'Please record your answer first.'
        );

        return;

    }


    await evaluateCurrentAnswer(
        text
    );

}



/* =========================================================
   ANALYZE LIVE JOB MARKET
========================================================= */

async function analyzeMarket() {

    const role =
        $('role')?.value.trim();


    const location =
        $('location')?.value.trim() ||
        'India';


    if (!role) {

        alert(
            'Enter a target role.'
        );

        return;

    }


    localStorage.setItem(
        'career_target_role',
        role
    );


    localStorage.setItem(
        'career_location',
        location
    );


    if ($('marketMessage')) {

        $('marketMessage').textContent =
            'Analyzing live jobs...';

        $('marketMessage').className =
            '';

    }


    const analyzeButton =
        $('analyzeButton');


    if (analyzeButton) {

        analyzeButton.disabled =
            true;

        analyzeButton.textContent =
            'Analyzing...';

    }


    try {

        /*
         * IMPORTANT:
         *
         * /api/career-intelligence is protected
         * by Supabase authentication.
         *
         * apiJson(..., true) automatically adds:
         *
         * Authorization: Bearer <access_token>
         */

        const data =
            await apiJson(
                `${API_URL}/api/career-intelligence` +
                `?role=${encodeURIComponent(role)}` +
                `&location=${encodeURIComponent(location)}`,
                {
                    method: 'GET'
                },
                true
            );


        console.log(
            'Career Intelligence Response:',
            data
        );


        /*
         * The backend currently returns live_jobs.
         * Keep compatibility with older response names.
         */

        const jobCount =
            data.live_jobs ??
            data.jobs_analyzed ??
            data.jobs_found ??
            0;


        if ($('jobsFound')) {

            $('jobsFound').textContent =
                `${jobCount} jobs analyzed`;

        }


        /*
         * Render market skills.
         */

        const marketSkills =
            Array.isArray(
                data.market_skills
            )
                ? data.market_skills
                : [];


        if ($('skillsContainer')) {

            $('skillsContainer').innerHTML =
                marketSkills
                .map(
                    (skill) => `

                        <span class="pill">

                            ${esc(skill.skill)}

                            ·

                            ${esc(skill.job_count)}

                        </span>

                    `
                )
                .join('');

        }


        if ($('marketMessage')) {

            $('marketMessage').textContent =
                'Market analysis complete.';

            $('marketMessage').className =
                'success';

        }


    } catch (error) {

        console.error(
            'Career Intelligence error:',
            error
        );


        if ($('marketMessage')) {

            $('marketMessage').textContent =
                error.message;

            $('marketMessage').className =
                'error';

        }


        /*
         * Send the user to login if the
         * Supabase session has expired.
         */

        if (
            error.message.includes(
                'session has expired'
            )
        ) {

            setTimeout(
                () => {

                    window.location.href =
                        'login.html';

                },
                1200
            );

        }

    } finally {

        if (analyzeButton) {

            analyzeButton.disabled =
                false;

            analyzeButton.textContent =
                'Analyze Live Job Market';

        }

    }

}



/* =========================================================
   SAVE INTERVIEW
========================================================= */

async function saveInterviewIfPossible() {

    try {

        /*
         * Get the logged-in Supabase session.
         */

        const session =
            await getAuthSession();


        /*
         * Send the access token to Flask.
         */

        const response =
            await fetch(
                `${API_URL}/api/interview/save`,
                {
                    method: 'POST',

                    headers: {

                        'Content-Type':
                            'application/json',

                        'Authorization':
                            `Bearer ${session.access_token}`

                    },

                    body: JSON.stringify({

                        role:
                            localStorage.getItem(
                                'career_target_role'
                            ) ||
                            'Java Developer',

                        evaluations

                    })

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch {

            data = {};

        }


        if (!response.ok) {

            console.warn(
                'Interview save failed:',
                data
            );

            /*
             * Do not break the interview UI
             * if saving fails.
             */

            return false;

        }


        console.log(
            'Interview saved successfully:',
            data
        );


        return true;

    } catch (error) {

        console.warn(
            'Interview save skipped:',
            error
        );


        return false;

    }

}



/* =========================================================
   DOM INITIALIZATION
========================================================= */

document.addEventListener(
    'DOMContentLoaded',
    () => {

        /*
         * Live market analysis
         */

        if ($('analyzeButton')) {

            $('analyzeButton')
                .addEventListener(
                    'click',
                    analyzeMarket
                );

        }


        /*
         * Text interview
         */

        if ($('startInterviewButton')) {

            $('startInterviewButton')
                .addEventListener(
                    'click',
                    () =>
                        startInterview('text')
                );

        }


        /*
         * Voice interview
         */

        if ($('voiceInterviewButton')) {

            $('voiceInterviewButton')
                .addEventListener(
                    'click',
                    () =>
                        startInterview('voice')
                );

        }


        /*
         * Text answer
         */

        if ($('submitAnswer')) {

            $('submitAnswer')
                .addEventListener(
                    'click',
                    submitTextAnswer
                );

        }


        /*
         * Next question
         */

        if ($('nextButton')) {

            $('nextButton')
                .addEventListener(
                    'click',
                    nextQuestion
                );

        }


        /*
         * Voice controls
         */

        if ($('startVoiceButton')) {

            $('startVoiceButton')
                .addEventListener(
                    'click',
                    startVoiceRecording
                );

        }


        if ($('stopVoiceButton')) {

            $('stopVoiceButton')
                .addEventListener(
                    'click',
                    stopVoiceRecording
                );

        }


        if ($('submitVoiceButton')) {

            $('submitVoiceButton')
                .addEventListener(
                    'click',
                    submitVoiceAnswer
                );

        }


        /*
         * Restore target role.
         */

        if (
            $('role') &&
            localStorage.getItem(
                'career_target_role'
            )
        ) {

            $('role').value =
                localStorage.getItem(
                    'career_target_role'
                );

        }


        /*
         * Restore location.
         */

        if (
            $('location') &&
            localStorage.getItem(
                'career_location'
            )
        ) {

            $('location').value =
                localStorage.getItem(
                    'career_location'
                );

        }

    }
);
