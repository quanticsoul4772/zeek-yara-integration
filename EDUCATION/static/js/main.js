// Security Learning Platform JavaScript

// Global variables
let ws = null;
let currentSession = null;
let currentQuizQuestion = 1;
let quizAnswers = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Security Learning Platform loaded');
    initializeInteractiveElements();
});

// Initialize interactive elements
function initializeInteractiveElements() {
    // Initialize quiz functionality
    setupQuizHandlers();
    
    // Initialize exercise handlers
    setupExerciseHandlers();
    
    // Initialize traffic simulation
    setupTrafficSimulation();
    
    // Initialize hint system
    setupHintSystem();
}

// WebSocket connection for real-time features
function initWebSocket(sessionId) {
    if (ws) {
        ws.close();
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionId}`);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        currentSession = sessionId;
        localStorage.setItem('current_session', sessionId);
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
            if (currentSession) {
                initWebSocket(currentSession);
            }
        }, 5000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'progress_update':
            updateProgressDisplay(data.progress);
            break;
        case 'hint':
            displayHint(data.hints);
            break;
        case 'achievement':
            showAchievement(data.achievement);
            break;
        case 'pong':
            // Keep-alive response
            break;
    }
}

// Update progress display
function updateProgressDisplay(progress) {
    const progressElements = document.querySelectorAll('.progress-indicator');
    progressElements.forEach(el => {
        if (progress.steps_completed) {
            el.textContent = `${progress.steps_completed.length} steps completed`;
        }
    });
}

// Network traffic simulation
function startTrafficDemo() {
    const display = document.getElementById('traffic-display');
    if (!display) return;
    
    display.innerHTML = '<div class="traffic-header"><h4>🌐 Live Network Traffic Simulation</h4></div>';
    
    const packets = [
        {time: '10:30:15', src: '192.168.1.100', dst: 'google.com', proto: 'HTTPS', info: 'Web browsing', normal: true},
        {time: '10:30:16', src: '192.168.1.100', dst: 'mail.company.com', proto: 'SMTP', info: 'Sending email', normal: true},
        {time: '10:30:17', src: '192.168.1.100', dst: 'cdn.example.com', proto: 'HTTP', info: 'Loading images', normal: true},
        {time: '10:30:18', src: '203.0.113.15', dst: '192.168.1.100', proto: 'TCP', info: '🚨 Port scan attempt', normal: false},
        {time: '10:30:19', src: '192.168.1.100', dst: 'suspicious-site.ru', proto: 'HTTPS', info: '⚠️ Large file upload', normal: false},
        {time: '10:30:20', src: '192.168.1.100', dst: 'update.microsoft.com', proto: 'HTTPS', info: 'Windows update', normal: true}
    ];
    
    const table = document.createElement('table');
    table.className = 'traffic-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Protocol</th>
                <th>Information</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    display.appendChild(table);
    
    const tbody = table.querySelector('tbody');
    
    packets.forEach((packet, index) => {
        setTimeout(() => {
            const row = document.createElement('tr');
            row.className = packet.normal ? 'normal-traffic' : 'suspicious-traffic';
            row.innerHTML = `
                <td>${packet.time}</td>
                <td>${packet.src}</td>
                <td>${packet.dst}</td>
                <td>${packet.proto}</td>
                <td>${packet.info}</td>
            `;
            tbody.appendChild(row);
            
            // Highlight suspicious traffic
            if (!packet.normal) {
                row.style.backgroundColor = '#fef2f2';
                row.style.borderLeft = '4px solid #ef4444';
                row.style.fontWeight = '600';
            }
            
            // Scroll to new row
            row.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, index * 1000);
    });
    
    // Add explanation after simulation
    setTimeout(() => {
        const explanation = document.createElement('div');
        explanation.className = 'traffic-explanation';
        explanation.innerHTML = `
            <h5>💡 What You Just Saw:</h5>
            <ul>
                <li>✅ <strong>Normal traffic:</strong> Web browsing, email, updates</li>
                <li>🚨 <strong>Suspicious activity:</strong> Port scans and unusual uploads</li>
                <li>🔍 <strong>Detection principle:</strong> Security tools monitor for these patterns</li>
            </ul>
        `;
        display.appendChild(explanation);
    }, packets.length * 1000 + 1000);
}

// EICAR file creation simulation
async function createEicarFile() {
    const statusEl = document.getElementById('create-status');
    const detectionEl = document.getElementById('detection-display');
    const resultsEl = document.getElementById('results-panel');
    
    if (!statusEl) return;
    
    // Step 1: Creating file
    statusEl.innerHTML = '🔄 Creating EICAR test file...';
    statusEl.className = 'step-status creating';
    
    await sleep(1500);
    
    statusEl.innerHTML = '✅ EICAR test file created successfully!';
    statusEl.className = 'step-status success';
    
    // Step 2: Detection simulation
    if (detectionEl) {
        detectionEl.innerHTML = `
            <div class="scanning-status active">
                🔍 YARA scanner processing file...
                <div class="scanning-dots">
                    <span>.</span><span>.</span><span>.</span>
                </div>
            </div>
            <div class="detection-progress">
                <div class="progress-bar">
                    <div class="progress-fill scanning"></div>
                </div>
            </div>
        `;
    }
    
    await sleep(2000);
    
    // Step 3: Show detection results
    if (detectionEl) {
        detectionEl.innerHTML = `
            <div class="detection-alert">
                🚨 MALWARE DETECTED!
                <div class="alert-details">
                    <strong>File:</strong> eicar_test.txt<br>
                    <strong>Rule:</strong> EICAR_Test_File<br>
                    <strong>Severity:</strong> <span class="severity-high">HIGH</span><br>
                    <strong>Status:</strong> <span class="status-quarantined">QUARANTINED</span>
                </div>
            </div>
        `;
    }
    
    await sleep(1000);
    
    if (resultsEl) {
        resultsEl.innerHTML = `
            <div class="detection-results">
                <h4>🔍 Detection Analysis Report</h4>
                <div class="result-grid">
                    <div class="result-field">
                        <strong>File Path:</strong> /extracted_files/eicar_test.txt
                    </div>
                    <div class="result-field">
                        <strong>File Size:</strong> 68 bytes
                    </div>
                    <div class="result-field">
                        <strong>YARA Rule:</strong> EICAR_Test_File
                    </div>
                    <div class="result-field">
                        <strong>Rule Author:</strong> Security Education Team
                    </div>
                    <div class="result-field">
                        <strong>Threat Type:</strong> Test File / Malware Signature
                    </div>
                    <div class="result-field">
                        <strong>Threat Family:</strong> EICAR-Test-File
                    </div>
                    <div class="result-field">
                        <strong>Confidence:</strong> 100% (Perfect Match)
                    </div>
                    <div class="result-field">
                        <strong>Risk Level:</strong> <span class="risk-high">HIGH</span>
                    </div>
                    <div class="result-field">
                        <strong>Detection Time:</strong> ${new Date().toLocaleTimeString()}
                    </div>
                    <div class="result-field">
                        <strong>Recommended Action:</strong> File quarantined automatically
                    </div>
                </div>
                <div class="success-message">
                    🎉 <strong>Congratulations!</strong> You've successfully detected your first "threat" using YARA rules!
                </div>
            </div>
        `;
    }
}

// Quiz functionality
function setupQuizHandlers() {
    // Enable quiz navigation when answer is selected
    document.addEventListener('change', function(e) {
        if (e.target.type === 'radio' && e.target.name.startsWith('q')) {
            const nextButton = document.getElementById('quiz-next');
            const submitButton = document.getElementById('quiz-submit');
            
            if (nextButton && !nextButton.style.display) {
                nextButton.disabled = false;
                nextButton.classList.add('btn-enabled');
            }
            
            if (submitButton && submitButton.style.display !== 'none') {
                submitButton.disabled = false;
                submitButton.classList.add('btn-enabled');
            }
        }
    });
}

function nextQuestion() {
    const currentQ = document.querySelector(`[data-question="${currentQuizQuestion}"]`);
    const selectedAnswer = document.querySelector(`input[name="q${currentQuizQuestion}"]:checked`);
    
    if (!selectedAnswer) {
        showNotification('Please select an answer before continuing.', 'warning');
        return;
    }
    
    quizAnswers[`q${currentQuizQuestion}`] = selectedAnswer.value;
    currentQ.style.display = 'none';
    
    currentQuizQuestion++;
    const nextQ = document.querySelector(`[data-question="${currentQuizQuestion}"]`);
    
    if (nextQ) {
        nextQ.style.display = 'block';
        const nextButton = document.getElementById('quiz-next');
        if (nextButton) {
            nextButton.disabled = true;
            nextButton.classList.remove('btn-enabled');
        }
    } else {
        // Show submit button
        const nextButton = document.getElementById('quiz-next');
        const submitButton = document.getElementById('quiz-submit');
        
        if (nextButton) nextButton.style.display = 'none';
        if (submitButton) {
            submitButton.style.display = 'inline-block';
            submitButton.disabled = true;
        }
    }
}

function submitQuiz() {
    const lastQuestion = document.querySelector(`[data-question="${currentQuizQuestion}"]`);
    const selectedAnswer = document.querySelector(`input[name="q${currentQuizQuestion}"]:checked`);
    
    if (!selectedAnswer) {
        showNotification('Please select an answer before submitting.', 'warning');
        return;
    }
    
    quizAnswers[`q${currentQuizQuestion}`] = selectedAnswer.value;
    
    // Hide last question
    if (lastQuestion) lastQuestion.style.display = 'none';
    
    // Calculate score
    const correctAnswers = {q1: 'b', q2: 'b', q3: 'c'};
    let score = 0;
    
    Object.keys(correctAnswers).forEach(question => {
        if (quizAnswers[question] === correctAnswers[question]) {
            score++;
        }
    });
    
    // Show results
    const resultsDiv = document.querySelector('.quiz-results');
    const scoreDiv = document.getElementById('quiz-score');
    const feedbackDiv = document.getElementById('quiz-feedback');
    
    if (resultsDiv) resultsDiv.style.display = 'block';
    
    if (scoreDiv) {
        const percentage = Math.round(score / 3 * 100);
        scoreDiv.innerHTML = `
            <div class="score-display">
                <div class="score-number">${score}/3</div>
                <div class="score-percentage">${percentage}%</div>
            </div>
        `;
    }
    
    if (feedbackDiv) {
        let feedbackClass = '';
        let feedbackText = '';
        
        if (score === 3) {
            feedbackClass = 'excellent';
            feedbackText = '🎉 <strong>Excellent!</strong> Perfect score! You have a solid understanding of network security fundamentals.';
        } else if (score >= 2) {
            feedbackClass = 'good';
            feedbackText = '👏 <strong>Good job!</strong> You understand the key concepts. Review the areas you missed for even better understanding.';
        } else {
            feedbackClass = 'needs-improvement';
            feedbackText = '📚 <strong>Keep learning!</strong> Review the tutorial material and try to understand the concepts better.';
        }
        
        feedbackDiv.innerHTML = `<p class="${feedbackClass}">${feedbackText}</p>`;
    }
    
    // Show completion section
    setTimeout(() => {
        const completionSection = document.getElementById('completion-section');
        if (completionSection) {
            completionSection.style.display = 'block';
            completionSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Award achievement for completing quiz
        if (score >= 2) {
            showAchievement('Quiz Master - Passed Network Security Fundamentals quiz!');
        }
    }, 2000);
}

// Exercise handlers
function setupExerciseHandlers() {
    // Threat identification exercise
    document.addEventListener('click', function(e) {
        if (e.target.closest('.log-entry')) {
            const entry = e.target.closest('.log-entry');
            
            // Skip if already selected
            if (entry.classList.contains('selected')) return;
            
            const isThreat = entry.dataset.threat === 'true';
            const threatType = entry.dataset.threatType || 'unknown';
            const feedbackEl = document.getElementById('exercise-feedback');
            
            entry.classList.add('selected');
            
            if (isThreat) {
                entry.classList.add('correct-selection');
                const threatExplanations = {
                    'port_scan': 'This shows a port scan - an attacker probing for open services.',
                    'data_exfiltration': 'This shows potential data exfiltration - a large file being uploaded to a suspicious domain.'
                };
                
                const explanation = threatExplanations[threatType] || 'This is suspicious network activity.';
                
                if (feedbackEl) {
                    feedbackEl.innerHTML += `
                        <div class="feedback-item correct">
                            ✅ <strong>Correct!</strong> ${explanation}
                        </div>
                    `;
                }
            } else {
                entry.classList.add('incorrect-selection');
                if (feedbackEl) {
                    feedbackEl.innerHTML += `
                        <div class="feedback-item incorrect">
                            ❌ <strong>Normal Activity:</strong> This is typical network traffic.
                        </div>
                    `;
                }
            }
            
            // Disable further clicks on this entry
            entry.style.pointerEvents = 'none';
            
            // Check if exercise is complete
            checkExerciseCompletion();
        }
    });
}

function checkExerciseCompletion() {
    const totalThreats = document.querySelectorAll('.log-entry[data-threat="true"]').length;
    const foundThreats = document.querySelectorAll('.log-entry.correct-selection').length;
    const falsePotitives = document.querySelectorAll('.log-entry.incorrect-selection').length;
    
    if (foundThreats === totalThreats) {
        setTimeout(() => {
            const completionMessage = document.createElement('div');
            completionMessage.className = 'exercise-completion';
            completionMessage.innerHTML = `
                <h4>🎯 Exercise Complete!</h4>
                <p><strong>Threats Found:</strong> ${foundThreats}/${totalThreats}</p>
                <p><strong>False Positives:</strong> ${falsePotitives}</p>
                ${falsePotitives <= 1 ? 
                    '<p class="success">🌟 <strong>Excellent work!</strong> You have a good eye for spotting security threats.</p>' :
                    '<p class="warning">⚠️ <strong>Good effort!</strong> Try to be more selective - focus on truly suspicious activities.</p>'
                }
            `;
            
            const feedbackEl = document.getElementById('exercise-feedback');
            if (feedbackEl) {
                feedbackEl.appendChild(completionMessage);
            }
            
            // Award achievement
            if (falsePotitives <= 1) {
                showAchievement('Threat Hunter - Excellent threat detection skills!');
            }
        }, 1000);
    }
}

// Traffic simulation setup
function setupTrafficSimulation() {
    // Auto-start traffic demo if button exists
    const startButton = document.querySelector('button[onclick*="startTrafficDemo"]');
    if (startButton) {
        startButton.addEventListener('click', startTrafficDemo);
    }
}

// Hint system
function setupHintSystem() {
    window.requestHint = async function() {
        const hintDisplay = document.getElementById('hint-display');
        if (!hintDisplay) return;
        
        hintDisplay.style.display = 'block';
        
        const hints = [
            '💡 Take your time to read and understand each concept thoroughly',
            '🔍 Try clicking on the interactive elements to enhance your learning',
            '📚 Review the learning objectives if you feel lost',
            '🎯 Focus on the key concepts highlighted in bold or colored text',
            '🤔 Think about how this applies to real-world security scenarios',
            '💪 Don\'t worry if it seems complex - you\'re building expertise step by step!'
        ];
        
        const randomHint = hints[Math.floor(Math.random() * hints.length)];
        hintDisplay.innerHTML = `<p>${randomHint}</p>`;
        
        // Auto-hide hint after 10 seconds
        setTimeout(() => {
            hintDisplay.style.display = 'none';
        }, 10000);
    };
}

// Achievement system
function showAchievement(achievementText) {
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    notification.innerHTML = `🏆 ${achievementText}`;
    document.body.appendChild(notification);
    
    // Add sound effect (if audio is enabled)
    playNotificationSound();
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

// Utility functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function playNotificationSound() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmUeCkaU2unJeSscJG7A7uGVRAkSVKvz7adUGAZNnuPwtmMeC0CK3OnEgC4SJ2m98OGUSAgNW7Pr66hVGwlNn+Twu2QdCjyEz+nJeCgZJWu68N+OPwdBltbtzZgXBCpXr+HqpFEaCECHzePCgS0SJW28z99OPwdBlNXTzYEaByVRr+PrpFIaBjiEzePFhC4TJWm88N+QQQgPXLzu4axGFAZCiM3hw4EtEyZ2vMfejkcTDVq87eKsRhMCVqPm7KhXGQcJhdHr0ZsxBAA=');
        audio.volume = 0.3;
        audio.play().catch(() => {}); // Ignore errors if audio can't play
    } catch (e) {
        // Ignore audio errors
    }
}

// API helpers
async function completeStep(tutorialId, stepId, sessionId) {
    try {
        const response = await fetch(`/api/tutorial/${tutorialId}/step/${stepId}/complete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessionId || currentSession})
        });
        
        if (!response.ok) throw new Error('Failed to complete step');
        
        const data = await response.json();
        
        if (data.achievements && data.achievements.length > 0) {
            data.achievements.forEach(achievement => {
                showAchievement(achievement);
            });
        }
        
        return data;
    } catch (error) {
        console.error('Failed to complete step:', error);
        showNotification('Failed to save progress. Please try again.', 'error');
        return null;
    }
}

async function startTutorial(tutorialId) {
    try {
        const response = await fetch(`/api/tutorial/${tutorialId}/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to start tutorial');
        
        const data = await response.json();
        
        if (data.session_id) {
            currentSession = data.session_id;
            localStorage.setItem(`tutorial_session_${tutorialId}`, data.session_id);
            
            // Initialize WebSocket connection
            initWebSocket(data.session_id);
            
            // Navigate to first step
            window.location.href = `/tutorial/${tutorialId}/step/intro`;
        }
    } catch (error) {
        console.error('Failed to start tutorial:', error);
        showNotification('Failed to start tutorial. Please try again.', 'error');
    }
}

// Global functions for template use
window.startTrafficDemo = startTrafficDemo;
window.createEicarFile = createEicarFile;
window.nextQuestion = nextQuestion;
window.submitQuiz = submitQuiz;
window.requestHint = setupHintSystem;
window.startTutorial = startTutorial;
window.completeStep = completeStep;

// Auto-complete step functionality
function setupAutoComplete() {
    // Auto-complete step after user interaction
    const stepContent = document.querySelector('.step-content');
    if (stepContent) {
        let interactionCount = 0;
        const requiredInteractions = 2;
        
        // Track clicks and scrolling as interactions
        stepContent.addEventListener('click', () => {
            interactionCount++;
            checkAutoComplete();
        });
        
        // Track scrolling
        let scrollTimer;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => {
                interactionCount++;
                checkAutoComplete();
            }, 1000);
        });
        
        function checkAutoComplete() {
            if (interactionCount >= requiredInteractions) {
                const tutorialId = window.location.pathname.split('/')[2];
                const stepId = window.location.pathname.split('/')[4];
                
                if (tutorialId && stepId && currentSession) {
                    completeStep(tutorialId, stepId, currentSession);
                }
            }
        }
        
        // Also auto-complete after time spent on page
        setTimeout(() => {
            checkAutoComplete();
        }, 10000); // 10 seconds
    }
}

// Initialize auto-complete when page loads
document.addEventListener('DOMContentLoaded', setupAutoComplete);

console.log('Security Learning Platform JavaScript initialized successfully!');