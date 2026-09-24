"use strict";

const $ = (selector, root = document) =>
    root.querySelector(selector);

const $$ = (selector, root = document) =>
    Array.from(root.querySelectorAll(selector));

const byId = (id) =>
    document.getElementById(id);


/* ==========================================================================
   CORE DOM
   ========================================================================== */

const resumeInput = byId("resumeInput");
const dropZone = byId("dropZone");
const browseButton = byId("browseButton");

const selectedFile = byId("selectedFile");
const fileName = byId("fileName");
const fileSize = byId("fileSize");
const removeFile = byId("removeFile");

const uploadTitle = byId("uploadTitle");
const uploadText = byId("uploadText");
const uploadIcon = byId("uploadIcon");

const jobDescription = byId("jobDescription");
const characterCount = byId("characterCount");

const analyzeButton = byId("analyzeButton");
const buttonText = byId("buttonText");

const loadingCard = byId("loadingCard");
const loadingMessage = byId("loadingMessage");

const resultsSection = byId("resultsSection");

const scoreValue = byId("scoreValue");
const scoreProgress = byId("scoreProgress");
const scoreTitle = byId("scoreTitle");
const scoreDescription = byId("scoreDescription");

const detectedSkills = byId("detectedSkills");
const missingSkills = byId("missingSkills");

const skillCount = byId("skillCount");
const missingCount = byId("missingCount");

const suggestionsList = byId("suggestionsList");

const newAnalysis = byId("newAnalysis");

const toast = byId("toast");
const toastMessage = byId("toastMessage");

const themeToggle = byId("themeToggle");

let selectedResume = null;
let currentAnalysis = null;
let analysisAbortController = null;
let analysisTimer = null;
let toastTimer = null;


/* ==========================================================================
   CONFIG
   ========================================================================== */

const CONFIG = {
    MAX_FILE_SIZE: 10 * 1024 * 1024,
    MIN_JD_LENGTH: 80,
    MAX_JD_LENGTH: 50000,
    REQUEST_TIMEOUT: 120000,
    HISTORY_KEY: "resumeAIHistory",
    THEME_KEY: "resumeAITheme",
    API_ENDPOINT: "/api/resume/analyze",

    progressSteps: [
        "Reading your resume",
        "Extracting professional intelligence",
        "Detecting skills and keywords",
        "Comparing job requirements",
        "Calculating ATS compatibility",
        "Checking resume structure",
        "Generating AI recommendations"
    ]
};


/* ==========================================================================
   INITIALIZATION
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initializeUpload();
    initializeJobDescription();
    initializeAnalysis();
    initializeTheme();
    initializeKeyboardShortcuts();
    initializeNavigation();
    initializeHistory();

    updateCharacterCount();
    updateJobDescriptionQuality();
});


/* ==========================================================================
   SAFE EVENT LISTENER
   ========================================================================== */

function on(element, event, handler, options = {}) {
    if (!element) return;

    element.addEventListener(event, handler, options);
}


/* ==========================================================================
   FILE UPLOAD
   ========================================================================== */

function initializeUpload() {

    on(browseButton, "click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        if (resumeInput) {
            resumeInput.click();
        }
    });


    on(dropZone, "click", (event) => {

        if (
            event.target.closest("button") ||
            event.target.closest(".selected-file") ||
            event.target.closest("input")
        ) {
            return;
        }

        if (resumeInput) {
            resumeInput.click();
        }
    });


    on(resumeInput, "change", (event) => {

        const file = event.target.files?.[0];

        if (file) {
            handleFile(file);
        }
    });


    on(removeFile, "click", (event) => {

        event.preventDefault();
        event.stopPropagation();

        clearSelectedFile();
    });


    if (!dropZone) return;


    ["dragenter", "dragover"].forEach((eventName) => {

        on(dropZone, eventName, (event) => {

            event.preventDefault();
            event.stopPropagation();

            dropZone.classList.add("dragover");
            dropZone.setAttribute("aria-dropeffect", "copy");
        });
    });


    ["dragleave", "drop"].forEach((eventName) => {

        on(dropZone, eventName, (event) => {

            event.preventDefault();
            event.stopPropagation();

            dropZone.classList.remove("dragover");
            dropZone.removeAttribute("aria-dropeffect");
        });
    });


    on(dropZone, "drop", (event) => {

        const files = event.dataTransfer?.files;

        if (!files || !files.length) {
            return;
        }

        handleFile(files[0]);
    });
}


/* ==========================================================================
   FILE HANDLER
   ========================================================================== */

function handleFile(file) {

    if (!file) {
        return;
    }


    const isPDF =
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");


    if (!isPDF) {

        showToast(
            "Only PDF resumes are supported.",
            true
        );

        clearSelectedFile();
        return;
    }


    if (file.size <= 0) {

        showToast(
            "The selected file appears to be empty.",
            true
        );

        return;
    }


    if (file.size > CONFIG.MAX_FILE_SIZE) {

        showToast(
            "Resume must be smaller than 10MB.",
            true
        );

        return;
    }


    selectedResume = file;


    if (fileName) {
        fileName.textContent = file.name;
    }


    if (fileSize) {
        fileSize.textContent =
            formatFileSize(file.size);
    }


    if (selectedFile) {
        selectedFile.hidden = false;
    }


    if (uploadTitle) {
        uploadTitle.textContent =
            "Resume ready for analysis";
    }


    if (uploadText) {
        uploadText.textContent =
            "PDF validated successfully • Ready for AI analysis";
    }


    if (uploadIcon) {
        uploadIcon.textContent = "✓";
    }


    dropZone?.classList.add("file-selected");


    showToast(
        `${file.name} is ready to analyze.`
    );
}


/* ==========================================================================
   CLEAR FILE
   ========================================================================== */

function clearSelectedFile() {

    selectedResume = null;


    if (resumeInput) {
        resumeInput.value = "";
    }


    if (selectedFile) {
        selectedFile.hidden = true;
    }


    if (uploadTitle) {
        uploadTitle.textContent =
            "Drop your resume here";
    }


    if (uploadText) {
        uploadText.textContent =
            "or click to browse from your computer";
    }


    if (uploadIcon) {
        uploadIcon.textContent = "↑";
    }


    dropZone?.classList.remove("file-selected");


    showToast("Resume removed.");
}


/* ==========================================================================
   FILE SIZE
   ========================================================================== */

function formatFileSize(bytes) {

    if (!Number.isFinite(bytes)) {
        return "Unknown size";
    }


    if (bytes < 1024) {
        return `${bytes} B`;
    }


    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }


    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}


/* ==========================================================================
   JOB DESCRIPTION
   ========================================================================== */

function initializeJobDescription() {

    on(jobDescription, "input", () => {

        updateCharacterCount();
        updateJobDescriptionQuality();
    });
}


/* ==========================================================================
   CHARACTER COUNT
   ========================================================================== */

function updateCharacterCount() {

    if (!jobDescription) {
        return;
    }


    const count = jobDescription.value.length;


    if (characterCount) {

        characterCount.textContent =
            `${count.toLocaleString()} characters`;
    }
}


/* ==========================================================================
   JOB DESCRIPTION QUALITY
   ========================================================================== */

function updateJobDescriptionQuality() {

    if (!jobDescription) {
        return;
    }


    const text =
        jobDescription.value.trim();


    const length = text.length;


    let quality = 0;


    if (length >= 80) quality += 25;
    if (length >= 250) quality += 20;
    if (length >= 500) quality += 15;


    const hasResponsibilities =
        /responsibilit|what you.?ll do|role/i.test(text);

    const hasRequirements =
        /requirement|qualifications|skills|experience/i.test(text);

    const hasTech =
        /python|javascript|react|node|sql|java|aws|docker|api|fastapi|django/i.test(text);


    if (hasResponsibilities) quality += 15;
    if (hasRequirements) quality += 15;
    if (hasTech) quality += 10;


    quality = Math.min(100, quality);


    const meter =
        byId("jdQualityMeter");

    const value =
        byId("jdQualityValue");

    const label =
        byId("jdQualityLabel");


    if (meter) {

        meter.style.width =
            `${quality}%`;
    }


    if (value) {

        value.textContent =
            `${quality}%`;
    }


    if (label) {

        if (quality >= 80) {

            label.textContent =
                "Excellent job description";

        } else if (quality >= 55) {

            label.textContent =
                "Good job description";

        } else if (length > 0) {

            label.textContent =
                "Add more role and skill details";

        } else {

            label.textContent =
                "Waiting for job description";
        }
    }
}


/* ==========================================================================
   ANALYSIS
   ========================================================================== */

function initializeAnalysis() {

    on(analyzeButton, "click", analyzeResume);
}


/* ==========================================================================
   ANALYZE RESUME
   ========================================================================== */

async function analyzeResume() {

    if (!selectedResume) {

        showToast(
            "Please upload your resume first.",
            true
        );

        return;
    }


    const jd =
        jobDescription?.value.trim() || "";


    if (!jd) {

        showToast(
            "Please enter the target job description.",
            true
        );

        jobDescription?.focus();

        return;
    }


    if (jd.length < CONFIG.MIN_JD_LENGTH) {

        showToast(
            `Job description should contain at least ${CONFIG.MIN_JD_LENGTH} characters.`,
            true
        );

        jobDescription?.focus();

        return;
    }


    if (jd.length > CONFIG.MAX_JD_LENGTH) {

        showToast(
            "Job description is too long.",
            true
        );

        return;
    }


    const formData =
        new FormData();


    formData.append(
        "resume",
        selectedResume
    );


    formData.append(
        "job_description",
        jd
    );


    setAnalysisState(true);


    startProgressAnimation();


    analysisAbortController =
        new AbortController();


    const timeout =
        setTimeout(() => {

            analysisAbortController?.abort();

        }, CONFIG.REQUEST_TIMEOUT);


    try {

        const response =
            await fetch(
                CONFIG.API_ENDPOINT,
                {
                    method: "POST",
                    body: formData,
                    signal: analysisAbortController.signal,
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        clearTimeout(timeout);


        const data =
            await parseJSONResponse(response);


        if (!response.ok) {

            throw new Error(
                extractErrorMessage(data)
            );
        }


        currentAnalysis = normalizeAnalysis(data);


        displayResults(
            currentAnalysis
        );


        saveHistory(
            currentAnalysis
        );


        showToast(
            "Resume intelligence analysis completed."
        );


    } catch (error) {

        clearTimeout(timeout);


        let message =
            "Analysis failed. Please try again.";


        if (error?.name === "AbortError") {

            message =
                "Analysis timed out. Please try again.";

        } else if (error?.message) {

            message =
                error.message;
        }


        showToast(
            message,
            true
        );


    } finally {

        stopProgressAnimation();

        setAnalysisState(false);

        analysisAbortController = null;
    }
}


/* ==========================================================================
   PARSE RESPONSE
   ========================================================================== */

async function parseJSONResponse(response) {

    const contentType =
        response.headers.get("content-type") || "";


    if (contentType.includes("application/json")) {

        return await response.json();
    }


    const text =
        await response.text();


    return {
        detail:
            text ||
            "Server returned an unexpected response."
    };
}


/* ==========================================================================
   ERROR EXTRACTION
   ========================================================================== */

function extractErrorMessage(data) {

    if (!data) {
        return "Analysis failed.";
    }


    if (typeof data === "string") {
        return data;
    }


    if (data.detail) {

        if (typeof data.detail === "string") {
            return data.detail;
        }

        if (Array.isArray(data.detail)) {

            return data.detail
                .map(item =>
                    item.msg || item.message || "Validation error"
                )
                .join(", ");
        }
    }


    return (
        data.message ||
        data.error ||
        "Analysis failed."
    );
}


/* ==========================================================================
   ANALYSIS STATE
   ========================================================================== */

function setAnalysisState(isAnalyzing) {

    if (analyzeButton) {
        analyzeButton.disabled =
            isAnalyzing;
    }


    if (buttonText) {

        buttonText.textContent =
            isAnalyzing
                ? "Analyzing Resume..."
                : "Analyze Resume";
    }


    if (loadingCard) {
        loadingCard.hidden =
            !isAnalyzing;
    }


    if (resultsSection && isAnalyzing) {
        resultsSection.hidden = true;
    }
}


/* ==========================================================================
   PROGRESS ENGINE
   ========================================================================== */

function startProgressAnimation() {

    let index = 0;


    setProgressStep(0);


    if (loadingMessage) {

        loadingMessage.textContent =
            CONFIG.progressSteps[0];
    }


    analysisTimer =
        setInterval(() => {

            index =
                Math.min(
                    index + 1,
                    CONFIG.progressSteps.length - 1
                );


            setProgressStep(index);


            if (loadingMessage) {

                loadingMessage.textContent =
                    CONFIG.progressSteps[index];
            }

        }, 1200);
}


/* ==========================================================================
   STOP PROGRESS
   ========================================================================== */

function stopProgressAnimation() {

    if (analysisTimer) {

        clearInterval(
            analysisTimer
        );

        analysisTimer = null;
    }
}


/* ==========================================================================
   PROGRESS STEP UI
   ========================================================================== */

function setProgressStep(index) {

    const steps =
        $$(".analysis-step");


    steps.forEach((step, stepIndex) => {

        step.classList.toggle(
            "active",
            stepIndex === index
        );


        step.classList.toggle(
            "complete",
            stepIndex < index
        );
    });
}


/* ==========================================================================
   NORMALIZE API RESPONSE
   ========================================================================== */

function normalizeAnalysis(data) {

    const score =
        toNumber(
            firstValue(
                data.overall_score,
                data.match_percentage,
                data.score,
                0
            )
        );


    const breakdown =
        data.score_breakdown ||
        data.breakdown ||
        {};


    const skills =
        normalizeArray(
            firstValue(
                data.detected_skills,
                data.skills,
                data.matched_skills,
                []
            )
        );


    const missing =
        normalizeArray(
            firstValue(
                data.missing_skills,
                data.skill_gaps,
                []
            )
        );


    const suggestions =
        normalizeRecommendations(
            firstValue(
                data.suggestions,
                data.recommendations,
                []
            )
        );


    return {
        ...data,

        filename:
            data.filename ||
            selectedResume?.name ||
            "Resume",

        overall_score:
            clamp(score),

        match_percentage:
            clamp(
                toNumber(
                    firstValue(
                        data.match_percentage,
                        score,
                        0
                    )
                )
            ),

        skills:
            skills,

        detected_skills:
            skills,

        missing_skills:
            missing,

        suggestions:
            suggestions,

        score_breakdown:
            breakdown,

        strengths:
            normalizeArray(
                data.strengths
            ),

        weaknesses:
            normalizeArray(
                data.weaknesses
            ),

        insights:
            normalizeArray(
                data.insights
            ),

        detected_keywords:
            normalizeArray(
                data.detected_keywords
            ),

        missing_keywords:
            normalizeArray(
                data.missing_keywords
            ),

        sections:
            normalizeObject(
                data.sections
            ),

        recommendations:
            suggestions
    };
}


/* ==========================================================================
   DISPLAY RESULTS
   ========================================================================== */

function displayResults(data) {

    if (!resultsSection) {
        return;
    }


    resultsSection.hidden = false;


    renderMainScore(data);


    renderDetectedSkills(data);


    renderMissingSkills(data);


    renderSuggestions(data);


    renderScoreBreakdown(data);


    renderKeywordIntelligence(data);


    renderSectionHealth(data);


    renderContentHealth(data);


    renderStrengths(data);


    renderWeaknesses(data);


    renderInsights(data);


    renderRecommendations(data);


    renderActionPlan(data);


    renderImprovementEstimate(data);


    renderMetadata(data);


    initializeResultInteractions();


    requestAnimationFrame(() => {

        resultsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    });
}


/* ==========================================================================
   MAIN SCORE
   ========================================================================== */

function renderMainScore(data) {

    const score =
        clamp(
            data.overall_score ||
            data.match_percentage ||
            0
        );


    animateScore(score);


    const classification =
        getScoreClassification(score);


    if (scoreTitle) {

        scoreTitle.textContent =
            classification.title;
    }


    if (scoreDescription) {

        scoreDescription.textContent =
            classification.description;
    }


    const scoreLabel =
        byId("scoreLabel");


    if (scoreLabel) {

        scoreLabel.textContent =
            classification.label;
    }


    const scoreStatus =
        byId("scoreStatus");


    if (scoreStatus) {

        scoreStatus.textContent =
            classification.status;
    }
}


/* ==========================================================================
   SCORE ANIMATION
   ========================================================================== */

function animateScore(score) {

    if (!scoreValue) {
        return;
    }


    const target =
        Math.round(
            clamp(score)
        );


    scoreValue.textContent =
        "0";


    if (scoreProgress) {

        const radius =
            Number(
                scoreProgress.getAttribute("r")
            ) || 52;


        const circumference =
            2 * Math.PI * radius;


        scoreProgress.style.strokeDasharray =
            `${circumference}`;


        scoreProgress.style.strokeDashoffset =
            `${circumference}`;


        setTimeout(() => {

            scoreProgress.style.strokeDashoffset =
                `${circumference * (1 - target / 100)}`;

        }, 80);
    }


    let current = 0;


    const increment =
        Math.max(
            1,
            Math.ceil(target / 35)
        );


    const interval =
        setInterval(() => {

            current += increment;


            if (current >= target) {

                current = target;

                clearInterval(interval);
            }


            scoreValue.textContent =
                current;
        }, 28);
}


/* ==========================================================================
   SCORE CLASSIFICATION
   ========================================================================== */

function getScoreClassification(score) {

    if (score >= 90) {

        return {
            title: "Exceptional Match",
            label: "TOP TIER",
            status: "Highly competitive",
            description:
                "Your resume is strongly aligned with the target role and should perform well in ATS screening."
        };
    }


    if (score >= 80) {

        return {
            title: "Excellent Match",
            label: "EXCELLENT",
            status: "Strong alignment",
            description:
                "Your resume strongly matches the target role with only a few areas worth optimizing."
        };
    }


    if (score >= 70) {

        return {
            title: "Strong Match",
            label: "STRONG",
            status: "Good alignment",
            description:
                "Your resume has strong alignment with the role, but targeted improvements can make it more competitive."
        };
    }


    if (score >= 60) {

        return {
            title: "Good Match",
            label: "GOOD",
            status: "Solid alignment",
            description:
                "Your resume has a solid foundation, but tailoring keywords and evidence can improve your match."
        };
    }


    if (score >= 40) {

        return {
            title: "Moderate Match",
            label: "MODERATE",
            status: "Needs optimization",
            description:
                "Your resume has relevant experience, but it needs stronger alignment with the target job."
        };
    }


    return {
        title: "Needs Improvement",
        label: "LOW",
        status: "High optimization opportunity",
        description:
            "Your resume currently has weak alignment with this role. Focus on skills, keywords, achievements and structure."
    };
}


/* ==========================================================================
   DETECTED SKILLS
   ========================================================================== */

function renderDetectedSkills(data) {

    if (!detectedSkills) {
        return;
    }


    const skills =
        data.detected_skills || [];


    if (skillCount) {

        skillCount.textContent =
            skills.length;
    }


    detectedSkills.innerHTML =
        "";


    if (!skills.length) {

        detectedSkills.innerHTML =
            createEmptyState(
                "No recognized skills detected",
                "Add relevant technical and professional skills to your resume."
            );

        return;
    }


    skills.forEach((skill) => {

        const tag =
            document.createElement("span");


        tag.className =
            "skill-tag premium-skill";


        tag.textContent =
            skill;


        detectedSkills.appendChild(tag);
    });
}


/* ==========================================================================
   MISSING SKILLS
   ========================================================================== */

function renderMissingSkills(data) {

    if (!missingSkills) {
        return;
    }


    const missing =
        data.missing_skills || [];


    if (missingCount) {

        missingCount.textContent =
            missing.length;
    }


    missingSkills.innerHTML =
        "";


    if (!missing.length) {

        missingSkills.innerHTML =
            createEmptyState(
                "No major skill gaps detected",
                "Your detected skills cover the important requirements found in the job description."
            );

        return;
    }


    missing.forEach((skill, index) => {

        const tag =
            document.createElement("span");


        tag.className =
            "skill-tag missing-tag";


        tag.textContent =
            skill;


        tag.title =
            `Priority skill gap #${index + 1}`;


        missingSkills.appendChild(tag);
    });
}


/* ==========================================================================
   SUGGESTIONS
   ========================================================================== */

function renderSuggestions(data) {

    if (!suggestionsList) {
        return;
    }


    const suggestions =
        data.suggestions || [];


    suggestionsList.innerHTML =
        "";


    if (!suggestions.length) {

        suggestionsList.innerHTML =
            createEmptyState(
                "No additional recommendations",
                "Your resume is already well optimized according to the current analysis."
            );

        return;
    }


    suggestions
        .slice(0, 20)
        .forEach((suggestion, index) => {

            const item =
                createRecommendationCard(
                    suggestion,
                    index
                );


            suggestionsList.appendChild(item);
        });
}


/* ==========================================================================
   RECOMMENDATION CARD
   ========================================================================== */

function createRecommendationCard(
    suggestion,
    index = 0
) {

    const item =
        document.createElement("article");


    item.className =
        "suggestion premium-recommendation";


    if (typeof suggestion === "string") {

        item.innerHTML = `
            <div class="recommendation-index">
                ${String(index + 1).padStart(2, "0")}
            </div>

            <div class="recommendation-content">
                <div class="recommendation-title">
                    Priority recommendation
                </div>

                <div class="recommendation-description">
                    ${escapeHTML(suggestion)}
                </div>
            </div>
        `;

        return item;
    }


    const priority =
        suggestion.priority ||
        "medium";


    const category =
        suggestion.category ||
        "Resume Optimization";


    const title =
        suggestion.title ||
        "Improve your resume";


    const description =
        suggestion.description ||
        suggestion.action ||
        "";


    const action =
        suggestion.action ||
        "";


    const impact =
        suggestion.impact ||
        "";


    item.innerHTML = `
        <div class="recommendation-index">
            ${String(index + 1).padStart(2, "0")}
        </div>

        <div class="recommendation-content">

            <div class="recommendation-meta">

                <span class="recommendation-category">
                    ${escapeHTML(category)}
                </span>

                <span class="recommendation-priority priority-${escapeAttribute(priority)}">
                    ${escapeHTML(priority)}
                </span>

            </div>

            <h4 class="recommendation-title">
                ${escapeHTML(title)}
            </h4>

            <p class="recommendation-description">
                ${escapeHTML(description)}
            </p>

            ${
                action
                    ? `
                    <div class="recommendation-action">
                        <strong>Action:</strong>
                        ${escapeHTML(action)}
                    </div>
                    `
                    : ""
            }

            ${
                impact
                    ? `
                    <div class="recommendation-impact">
                        <strong>Impact:</strong>
                        ${escapeHTML(impact)}
                    </div>
                    `
                    : ""
            }

        </div>
    `;


    return item;
}


/* ==========================================================================
   SCORE BREAKDOWN
   ========================================================================== */

function renderScoreBreakdown(data) {

    const breakdown =
        data.score_breakdown ||
        data.breakdown ||
        {};


    const mappings = {

        skills_score: [
            "skills_score",
            "skills",
            "skill_alignment"
        ],

        keyword_score: [
            "keyword_score",
            "keywords",
            "keyword_coverage"
        ],

        semantic_score: [
            "semantic_score",
            "semantic",
            "relevance"
        ],

        section_score: [
            "section_score",
            "sections",
            "structure"
        ],

        achievement_score: [
            "achievement_score",
            "achievements",
            "evidence"
        ],

        contact_score: [
            "contact_score",
            "contact",
            "profile"
        ],

        content_score: [
            "content_score",
            "content",
            "quality"
        ]
    };


    Object.entries(mappings)
        .forEach(([key, aliases]) => {

            const value =
                findNestedValue(
                    data,
                    aliases
                );


            updateScoreElement(
                key,
                value
            );
        });
}


/* ==========================================================================
   SCORE ELEMENT
   ========================================================================== */

function updateScoreElement(
    key,
    value
) {

    if (value === undefined || value === null) {
        return;
    }


    const score =
        clamp(
            toNumber(value)
        );


    const candidates = [
        byId(key),
        byId(
            `${key.replace("_score", "")}Score`
        ),
        $(`[data-score="${key}"]`)
    ].filter(Boolean);


    candidates.forEach((element) => {

        const valueElement =
            element.querySelector(
                ".score-value, .metric-value, [data-score-value]"
            );


        const progressElement =
            element.querySelector(
                ".score-fill, .progress-fill, .metric-progress"
            );


        if (valueElement) {

            valueElement.textContent =
                `${Math.round(score)}`;
        }


        if (progressElement) {

            progressElement.style.width =
                `${score}%`;
        }


        if (
            element.matches(
                "progress"
            )
        ) {

            element.value =
                score;
        }


        if (
            element.dataset
        ) {

            element.dataset.score =
                score;
        }
    });
}


/* ==========================================================================
   KEYWORD INTELLIGENCE
   ========================================================================== */

function renderKeywordIntelligence(data) {

    renderArrayInto(
        [
            byId("detectedKeywords"),
            byId("keywordMatches"),
            byId("matchedKeywords")
        ],
        data.detected_keywords,
        "keyword-tag"
    );


    renderArrayInto(
        [
            byId("missingKeywords"),
            byId("keywordGaps")
        ],
        data.missing_keywords,
        "keyword-tag missing-keyword"
    );


    const coverage =
        firstValue(
            data.keyword_coverage,
            data.keyword_score,
            data.keyword_analysis?.coverage,
            null
        );


    if (coverage !== null) {

        setText(
            [
                byId("keywordCoverage"),
                byId("keywordCoverageValue")
            ],
            `${Math.round(clamp(toNumber(coverage)))}%`
        );
    }
}


/* ==========================================================================
   SECTION HEALTH
   ========================================================================== */

function renderSectionHealth(data) {

    const sections =
        data.sections;


    if (!sections) {
        return;
    }


    const container =
        byId("sectionHealth") ||
        byId("sectionsHealth");


    if (!container) {
        return;
    }


    container.innerHTML =
        "";


    if (Array.isArray(sections)) {

        sections.forEach(
            (section) => {

                const name =
                    section.name ||
                    section.title ||
                    "Section";


                const score =
                    clamp(
                        toNumber(
                            section.score ||
                            section.value ||
                            0
                        )
                    );


                container.appendChild(
                    createHealthRow(
                        name,
                        score
                    )
                );
            }
        );

        return;
    }


    Object.entries(sections)
        .forEach(([name, value]) => {

            const score =
                typeof value === "object"
                    ? toNumber(
                        value.score ||
                        value.value ||
                        0
                    )
                    : toNumber(value);


            container.appendChild(
                createHealthRow(
                    formatLabel(name),
                    clamp(score)
                )
            );
        });
}


/* ==========================================================================
   HEALTH ROW
   ========================================================================== */

function createHealthRow(
    name,
    score
) {

    const row =
        document.createElement("div");


    row.className =
        "health-row";


    row.innerHTML = `
        <div class="health-row-header">

            <span>
                ${escapeHTML(name)}
            </span>

            <strong>
                ${Math.round(score)}
            </strong>

        </div>

        <div class="health-progress">
            <span
                class="health-progress-fill"
                style="width:${score}%"
            ></span>
        </div>
    `;


    return row;
}


/* ==========================================================================
   CONTENT HEALTH
   ========================================================================== */

function renderContentHealth(data) {

    const content =
        data.content_analysis ||
        data.content ||
        data.resume_health;


    if (!content) {
        return;
    }


    const container =
        byId("contentHealth") ||
        byId("resumeHealth");


    if (!container) {
        return;
    }


    if (Array.isArray(content)) {

        renderHealthCards(
            container,
            content
        );

        return;
    }


    const entries =
        Object.entries(content);


    if (!entries.length) {
        return;
    }


    container.innerHTML =
        "";


    entries.forEach(([key, value]) => {

        if (
            typeof value !== "number" &&
            typeof value !== "string" &&
            typeof value !== "boolean"
        ) {
            return;
        }


        const card =
            document.createElement("div");


        card.className =
            "health-card";


        card.innerHTML = `
            <span class="health-card-label">
                ${escapeHTML(formatLabel(key))}
            </span>

            <strong class="health-card-value">
                ${
                    typeof value === "boolean"
                        ? value
                            ? "✓"
                            : "—"
                        : escapeHTML(String(value))
                }
            </strong>
        `;


        container.appendChild(card);
    });
}


/* ==========================================================================
   HEALTH CARDS
   ========================================================================== */

function renderHealthCards(
    container,
    items
) {

    container.innerHTML =
        "";


    items.forEach((item) => {

        const card =
            document.createElement("div");


        card.className =
            "health-card";


        card.innerHTML = `
            <span class="health-card-label">
                ${escapeHTML(
                    item.title ||
                    item.name ||
                    "Health Check"
                )}
            </span>

            <strong class="health-card-value">
                ${escapeHTML(
                    String(
                        item.value ??
                        item.score ??
                        "—"
                    )
                )}
            </strong>
        `;


        container.appendChild(card);
    });
}


/* ==========================================================================
   STRENGTHS
   ========================================================================== */

function renderStrengths(data) {

    renderInsightList(
        [
            byId("strengths"),
            byId("strengthList")
        ],
        data.strengths,
        "strength-item",
        "No major strengths detected yet."
    );
}


/* ==========================================================================
   WEAKNESSES
   ========================================================================== */

function renderWeaknesses(data) {

    renderInsightList(
        [
            byId("weaknesses"),
            byId("weaknessList")
        ],
        data.weaknesses,
        "weakness-item",
        "No major weaknesses detected."
    );
}


/* ==========================================================================
   INSIGHTS
   ========================================================================== */

function renderInsights(data) {

    renderInsightList(
        [
            byId("insights"),
            byId("insightList"),
            byId("aiInsights")
        ],
        data.insights,
        "insight-item",
        "No additional insights available."
    );
}


/* ==========================================================================
   INSIGHT LIST
   ========================================================================== */

function renderInsightList(
    containers,
    values,
    className,
    emptyMessage
) {

    const validContainers =
        containers.filter(Boolean);


    if (!validContainers.length) {
        return;
    }


    const items =
        normalizeArray(values);


    validContainers.forEach((container) => {

        container.innerHTML =
            "";


        if (!items.length) {

            container.innerHTML =
                createEmptyState(
                    emptyMessage
                );

            return;
        }


        items.forEach((value) => {

            const item =
                document.createElement("div");


            item.className =
                className;


            if (typeof value === "object") {

                item.textContent =
                    value.text ||
                    value.title ||
                    value.description ||
                    JSON.stringify(value);

            } else {

                item.textContent =
                    value;
            }


            container.appendChild(item);
        });
    });
}


/* ==========================================================================
   ADVANCED RECOMMENDATIONS
   ========================================================================== */

function renderRecommendations(data) {

    const containers = [
        byId("recommendations"),
        byId("recommendationList"),
        byId("aiRecommendations")
    ].filter(Boolean);


    if (!containers.length) {
        return;
    }


    const recommendations =
        normalizeRecommendations(
            data.recommendations ||
            data.suggestions
        );


    containers.forEach((container) => {

        container.innerHTML =
            "";


        recommendations
            .slice(0, 12)
            .forEach((item, index) => {

                container.appendChild(
                    createRecommendationCard(
                        item,
                        index
                    )
                );
            });
    });
}


/* ==========================================================================
   ACTION PLAN
   ========================================================================== */

function renderActionPlan(data) {

    const container =
        byId("actionPlan");


    if (!container) {
        return;
    }


    let actions =
        data.action_plan ||
        data.actionPlan ||
        [];


    if (!Array.isArray(actions)) {

        if (typeof actions === "object") {

            actions =
                Object.values(actions);
        } else {

            actions = [];
        }
    }


    container.innerHTML =
        "";


    if (!actions.length) {

        container.innerHTML =
            createEmptyState(
                "Your action plan will appear here.",
                "Run another analysis after updating your resume."
            );

        return;
    }


    actions.forEach((action, index) => {

        const item =
            document.createElement("div");


        item.className =
            "action-plan-item";


        const title =
            typeof action === "string"
                ? action
                : action.title ||
                  action.action ||
                  action.description ||
                  "Optimization step";


        item.innerHTML = `
            <div class="action-number">
                ${String(index + 1).padStart(2, "0")}
            </div>

            <div class="action-content">
                <strong>
                    ${escapeHTML(title)}
                </strong>

                ${
                    typeof action === "object" &&
                    action.description &&
                    action.description !== title
                        ? `
                        <p>
                            ${escapeHTML(
                                action.description
                            )}
                        </p>
                        `
                        : ""
                }
            </div>
        `;


        container.appendChild(item);
    });
}


/* ==========================================================================
   IMPROVEMENT ESTIMATE
   ========================================================================== */

function renderImprovementEstimate(data) {

    const estimate =
        firstValue(
            data.improvement_estimate,
            data.estimated_improvement,
            data.potential_gain,
            null
        );


    if (estimate === null) {
        return;
    }


    const numeric =
        toNumber(
            typeof estimate === "object"
                ? estimate.score ||
                  estimate.points ||
                  estimate.value ||
                  0
                : estimate
        );


    setText(
        [
            byId("improvementEstimate"),
            byId("potentialGain")
        ],
        `+${Math.round(numeric)} pts`
    );
}


/* ==========================================================================
   METADATA
   ========================================================================== */

function renderMetadata(data) {

    setText(
        [
            byId("resultFilename"),
            byId("analysisFilename")
        ],
        data.filename || "Resume"
    );


    setText(
        [
            byId("targetRole"),
            byId("roleTitle")
        ],
        data.role_title ||
        data.roleTitle ||
        "Target Role"
    );


    setText(
        [
            byId("analysisId")
        ],
        data.id ||
        data.analysis_id ||
        "—"
    );


    setText(
        [
            byId("analysisTime")
        ],
        new Date().toLocaleString()
    );
}


/* ==========================================================================
   RESULT INTERACTIONS
   ========================================================================== */

function initializeResultInteractions() {

    $$(".result-tab").forEach((tab) => {

        on(tab, "click", () => {

            const target =
                tab.dataset.target;


            if (!target) {
                return;
            }


            $$(".result-tab")
                .forEach(item =>
                    item.classList.remove("active")
                );


            tab.classList.add("active");


            const section =
                byId(target);


            section?.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        });
    });


    $$("[data-copy]").forEach((button) => {

        on(button, "click", async () => {

            const selector =
                button.dataset.copy;


            const target =
                $(selector);


            if (!target) {
                return;
            }


            try {

                await navigator.clipboard.writeText(
                    target.innerText
                );


                showToast(
                    "Copied to clipboard."
                );

            } catch {

                showToast(
                    "Unable to copy.",
                    true
                );
            }
        });
    });


    on(byId("printReport"), "click", () => {

        window.print();
    });


    on(byId("downloadReport"), "click", () => {

        window.print();
    });
}


/* ==========================================================================
   NEW ANALYSIS
   ========================================================================== */

on(newAnalysis, "click", () => {

    if (resultsSection) {
        resultsSection.hidden = true;
    }


    clearSelectedFile();


    if (jobDescription) {
        jobDescription.focus();
    }


    const analyzer =
        byId("analyzer");


    if (analyzer) {

        analyzer.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } else {

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }
});


/* ==========================================================================
   TOAST
   ========================================================================== */

function showToast(
    message,
    error = false
) {

    if (!toast || !toastMessage) {

        console[
            error
                ? "error"
                : "log"
        ](message);

        return;
    }


    toastMessage.textContent =
        message;


    toast.classList.toggle(
        "error",
        error
    );


    toast.classList.add(
        "show"
    );


    if (toastTimer) {

        clearTimeout(
            toastTimer
        );
    }


    toastTimer =
        setTimeout(() => {

            toast.classList.remove(
                "show"
            );

        }, 4000);
}


/* ==========================================================================
   HISTORY
   ========================================================================== */

function initializeHistory() {

    const history =
        getHistory();


    renderHistory(
        history
    );
}


/* ==========================================================================
   SAVE HISTORY
   ========================================================================== */

function saveHistory(data) {

    const history =
        getHistory();


    const entry = {

        id:
            data.id ||
            data.analysis_id ||
            cryptoRandomId(),

        filename:
            data.filename ||
            "Resume",

        score:
            Math.round(
                data.overall_score ||
                data.match_percentage ||
                0
            ),

        role:
            data.role_title ||
            data.roleTitle ||
            "Target Role",

        date:
            new Date().toISOString()
    };


    const filtered =
        history.filter(
            item =>
                item.id !== entry.id
        );


    filtered.unshift(
        entry
    );


    localStorage.setItem(
        CONFIG.HISTORY_KEY,
        JSON.stringify(
            filtered.slice(0, 15)
        )
    );


    renderHistory(
        filtered.slice(0, 15)
    );
}


/* ==========================================================================
   GET HISTORY
   ========================================================================== */

function getHistory() {

    try {

        const value =
            localStorage.getItem(
                CONFIG.HISTORY_KEY
            );


        if (!value) {
            return [];
        }


        const parsed =
            JSON.parse(value);


        return Array.isArray(parsed)
            ? parsed
            : [];

    } catch {

        return [];
    }
}


/* ==========================================================================
   RENDER HISTORY
   ========================================================================== */

function renderHistory(history) {

    const containers = [
        byId("historyList"),
        byId("recentHistory")
    ].filter(Boolean);


    if (!containers.length) {
        return;
    }


    containers.forEach((container) => {

        container.innerHTML =
            "";


        if (!history.length) {

            container.innerHTML =
                createEmptyState(
                    "No analysis history yet.",
                    "Your completed resume analyses will appear here."
                );

            return;
        }


        history.forEach((item) => {

            const row =
                document.createElement("div");


            row.className =
                "history-item";


            const score =
                Number(item.score) || 0;


            row.innerHTML = `
                <div class="history-file">
                    <strong>
                        ${escapeHTML(
                            item.filename ||
                            "Resume"
                        )}
                    </strong>

                    <span>
                        ${escapeHTML(
                            item.role ||
                            "Target Role"
                        )}
                    </span>
                </div>

                <div class="history-score">
                    ${score}
                </div>

                <div class="history-date">
                    ${escapeHTML(
                        formatDate(
                            item.date
                        )
                    )}
                </div>
            `;


            container.appendChild(row);
        });
    });
}


/* ==========================================================================
   THEME
   ========================================================================== */

function initializeTheme() {

    const savedTheme =
        localStorage.getItem(
            CONFIG.THEME_KEY
        );


    if (
        savedTheme === "light" ||
        savedTheme === "dark"
    ) {

        document.body.classList.toggle(
            "light-mode",
            savedTheme === "light"
        );
    }


    on(themeToggle, "click", () => {

        const isLight =
            document.body.classList.toggle(
                "light-mode"
            );


        localStorage.setItem(
            CONFIG.THEME_KEY,
            isLight
                ? "light"
                : "dark"
        );


        showToast(
            isLight
                ? "Light theme enabled."
                : "Dark theme enabled."
        );
    });
}


/* ==========================================================================
   NAVIGATION
   ========================================================================== */

function initializeNavigation() {

    $$("[data-scroll]").forEach((button) => {

        on(button, "click", () => {

            const target =
                byId(
                    button.dataset.scroll
                );


            target?.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        });
    });
}


/* ==========================================================================
   KEYBOARD SHORTCUTS
   ========================================================================== */

function initializeKeyboardShortcuts() {

    on(document, "keydown", (event) => {

        if (
            (event.ctrlKey ||
                event.metaKey) &&
            event.key.toLowerCase() === "enter"
        ) {

            event.preventDefault();


            if (
                analyzeButton &&
                !analyzeButton.disabled
            ) {

                analyzeResume();
            }
        }


        if (event.key === "Escape") {

            if (
                analysisAbortController
            ) {

                analysisAbortController.abort();
            }
        }
    });
}


/* ==========================================================================
   ARRAY NORMALIZER
   ========================================================================== */

function normalizeArray(value) {

    if (value === null || value === undefined) {
        return [];
    }


    if (Array.isArray(value)) {

        return value
            .map(item => {

                if (
                    typeof item === "object" &&
                    item !== null
                ) {

                    return (
                        item.name ||
                        item.title ||
                        item.text ||
                        item.skill ||
                        item.keyword ||
                        item.description ||
                        ""
                    );
                }

                return String(item);
            })
            .filter(Boolean);
    }


    if (typeof value === "string") {

        return value
            .split(/[,\n|;]/)
            .map(item => item.trim())
            .filter(Boolean);
    }


    return [];
}


/* ==========================================================================
   RECOMMENDATION NORMALIZER
   ========================================================================== */

function normalizeRecommendations(value) {

    if (!Array.isArray(value)) {

        if (typeof value === "string") {
            return normalizeArray(value);
        }

        return [];
    }


    return value.map(item => {

        if (typeof item === "string") {
            return item;
        }


        return {
            priority:
                item.priority ||
                "medium",

            category:
                item.category ||
                "Resume",

            title:
                item.title ||
                item.name ||
                "Improve your resume",

            description:
                item.description ||
                item.reason ||
                "",

            action:
                item.action ||
                "",

            impact:
                item.impact ||
                "",

            related_items:
                item.related_items ||
                []
        };
    });
}


/* ==========================================================================
   OBJECT NORMALIZER
   ========================================================================== */

function normalizeObject(value) {

    if (
        value &&
        typeof value === "object" &&
        !Array.isArray(value)
    ) {
        return value;
    }


    return {};
}


/* ==========================================================================
   ARRAY RENDERER
   ========================================================================== */

function renderArrayInto(
    containers,
    values,
    className
) {

    const items =
        normalizeArray(values);


    containers
        .filter(Boolean)
        .forEach((container) => {

            container.innerHTML =
                "";


            if (!items.length) {

                container.innerHTML =
                    createEmptyState(
                        "No items detected."
                    );

                return;
            }


            items.forEach((item) => {

                const tag =
                    document.createElement("span");


                tag.className =
                    className;


                tag.textContent =
                    item;


                container.appendChild(
                    tag
                );
            });
        });
}


/* ==========================================================================
   EMPTY STATE
   ========================================================================== */

function createEmptyState(
    title,
    description = ""
) {

    return `
        <div class="empty-result premium-empty">

            <div class="empty-result-icon">
                ✦
            </div>

            <strong>
                ${escapeHTML(title)}
            </strong>

            ${
                description
                    ? `
                    <span>
                        ${escapeHTML(
                            description
                        )}
                    </span>
                    `
                    : ""
            }

        </div>
    `;
}


/* ==========================================================================
   SET TEXT
   ========================================================================== */

function setText(
    elements,
    value
) {

    elements
        .filter(Boolean)
        .forEach((element) => {

            element.textContent =
                value;
        });
}


/* ==========================================================================
   FIND NESTED VALUE
   ========================================================================== */

function findNestedValue(
    data,
    aliases
) {

    for (const alias of aliases) {

        if (
            data &&
            data[alias] !== undefined &&
            data[alias] !== null
        ) {

            return extractScoreValue(
                data[alias]
            );
        }


        if (
            data?.score_breakdown &&
            data.score_breakdown[alias] !== undefined
        ) {

            return extractScoreValue(
                data.score_breakdown[alias]
            );
        }


        if (
            data?.breakdown &&
            data.breakdown[alias] !== undefined
        ) {

            return extractScoreValue(
                data.breakdown[alias]
            );
        }
    }


    return undefined;
}


/* ==========================================================================
   EXTRACT SCORE
   ========================================================================== */

function extractScoreValue(value) {

    if (
        typeof value === "number"
    ) {
        return value;
    }


    if (
        typeof value === "string"
    ) {

        return toNumber(value);
    }


    if (
        value &&
        typeof value === "object"
    ) {

        return toNumber(
            value.score ??
            value.value ??
            value.percentage ??
            0
        );
    }


    return 0;
}


/* ==========================================================================
   FIRST VALUE
   ========================================================================== */

function firstValue(...values) {

    for (const value of values) {

        if (
            value !== undefined &&
            value !== null &&
            value !== ""
        ) {

            return value;
        }
    }


    return undefined;
}


/* ==========================================================================
   NUMBER
   ========================================================================== */

function toNumber(value) {

    if (
        typeof value === "number" &&
        Number.isFinite(value)
    ) {

        return value;
    }


    if (
        typeof value === "string"
    ) {

        const parsed =
            parseFloat(
                value.replace(
                    /[^0-9.-]/g,
                    ""
                )
            );


        return Number.isFinite(parsed)
            ? parsed
            : 0;
    }


    return 0;
}


/* ==========================================================================
   CLAMP
   ========================================================================== */

function clamp(value) {

    return Math.min(
        100,
        Math.max(
            0,
            toNumber(value)
        )
    );
}


/* ==========================================================================
   LABEL FORMATTER
   ========================================================================== */

function formatLabel(value) {

    return String(value)
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );
}


/* ==========================================================================
   DATE FORMATTER
   ========================================================================== */

function formatDate(value) {

    if (!value) {
        return "Recently";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);
    }


    return date.toLocaleString(
        undefined,
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );
}


/* ==========================================================================
   RANDOM ID
   ========================================================================== */

function cryptoRandomId() {

    if (
        window.crypto &&
        typeof window.crypto.randomUUID === "function"
    ) {

        return window.crypto.randomUUID();
    }


    return (
        Date.now().toString(36) +
        Math.random()
            .toString(36)
            .slice(2)
    );
}


/* ==========================================================================
   ESCAPE HTML
   ========================================================================== */

function escapeHTML(value) {

    const div =
        document.createElement("div");


    div.textContent =
        String(
            value ?? ""
        );


    return div.innerHTML;
}


/* ==========================================================================
   ESCAPE ATTRIBUTE
   ========================================================================== */

function escapeAttribute(value) {

    return escapeHTML(value)
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#39;"
        );
}


/* ==========================================================================
   PAGE VISIBILITY
   ========================================================================== */

document.addEventListener(
    "visibilitychange",
    () => {

        if (
            document.hidden &&
            analysisAbortController
        ) {
            /*
             * Do not cancel automatically.
             * Analysis should continue if the user
             * temporarily changes tabs.
             */
        }
    }
);


/* ==========================================================================
   GLOBAL ERROR SAFETY
   ========================================================================== */

window.addEventListener(
    "error",
    (event) => {

        console.error(
            "ResumeAI frontend error:",
            event.error || event.message
        );
    }
);


window.addEventListener(
    "unhandledrejection",
    (event) => {

        console.error(
            "ResumeAI async error:",
            event.reason
        );
    }
);


/* ==========================================================================
   EXPORT DEBUG API
   ========================================================================== */

window.ResumeAI = {

    getCurrentAnalysis: () =>
        currentAnalysis,

    getHistory: () =>
        getHistory(),

    clearHistory: () => {

        localStorage.removeItem(
            CONFIG.HISTORY_KEY
        );

        renderHistory([]);
    },

    reset: () => {

        clearSelectedFile();

        if (jobDescription) {
            jobDescription.value = "";
        }

        updateCharacterCount();
        updateJobDescriptionQuality();

        if (resultsSection) {
            resultsSection.hidden = true;
        }
    }
};


console.log(
    "%cResumeAI Ultra Pro Engine Loaded",
    "font-weight:700;font-size:14px"
);