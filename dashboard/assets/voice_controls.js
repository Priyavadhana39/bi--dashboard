/**
 * Voice Controls for AI Procurement Agent
 * Implements speech recognition (input) and text-to-speech (output)
 */

// Voice recognition state
let recognition = null;
let isRecognitionSupported = false;
let isRecording = false;

// Text-to-speech state
let speechSynthesis = window.speechSynthesis;
let currentUtterance = null;
let isSpeaking = false;

// Check browser support on page load
document.addEventListener('DOMContentLoaded', function() {
    checkVoiceSupport();
    initializeVoiceControls();
});

/**
 * Check if browser supports speech recognition and synthesis
 */
function checkVoiceSupport() {
    // Check Speech Recognition support (Chrome, Edge, Safari)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    isRecognitionSupported = !!SpeechRecognition;
    
    // Check Speech Synthesis support (all modern browsers)
    const isSynthesisSupported = 'speechSynthesis' in window;
    
    console.log('[Voice] Recognition supported:', isRecognitionSupported);
    console.log('[Voice] Synthesis supported:', isSynthesisSupported);
    
    // Initialize recognition if supported
    if (isRecognitionSupported) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            console.log('[Voice] Recognition started');
            isRecording = true;
            updateMicrophoneButtonState(true);
        };
        
        recognition.onend = function() {
            console.log('[Voice] Recognition ended');
            isRecording = false;
            updateMicrophoneButtonState(false);
        };
        
        recognition.onerror = function(event) {
            console.error('[Voice] Recognition error:', event.error);
            isRecording = false;
            updateMicrophoneButtonState(false);
            
            // Show user-friendly error message
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
                alert('Microphone permission denied. Please allow microphone access in your browser settings.');
            } else if (event.error === 'no-speech') {
                alert('No speech detected. Please try again.');
            }
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            console.log('[Voice] Recognized:', transcript);
            
            // Insert transcript into question input
            const questionInput = document.getElementById('agent-question-input');
            if (questionInput) {
                // Set the value
                questionInput.value = transcript;
                
                // Trigger multiple events to ensure Dash updates
                // 1. Input event (for immediate visual feedback)
                questionInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // 2. Change event (for Dash state update)
                questionInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                // 3. Blur and focus to force Dash to recognize the change
                questionInput.dispatchEvent(new Event('blur', { bubbles: true }));
                questionInput.dispatchEvent(new Event('focus', { bubbles: true }));
                
                console.log('[Voice] Transcript set and events dispatched:', transcript);
            }
        };
    }
}

/**
 * Initialize voice control buttons
 */
function initializeVoiceControls() {
    // Use MutationObserver to detect when page5 is loaded
    const observer = new MutationObserver(function(mutations) {
        const questionInput = document.getElementById('agent-question-input');
        if (questionInput && !document.getElementById('voice-input-btn')) {
            addVoiceInputButton();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

/**
 * Add microphone button to question input area
 */
function addVoiceInputButton() {
    const questionInput = document.getElementById('agent-question-input');
    if (!questionInput || !isRecognitionSupported) {
        return;
    }
    
    // Find the parent container
    const inputContainer = questionInput.parentElement;
    if (!inputContainer) {
        return;
    }
    
    // Create microphone button
    const micButton = document.createElement('button');
    micButton.id = 'voice-input-btn';
    micButton.innerHTML = '🎤';
    micButton.title = 'Click to speak your question';
    micButton.style.cssText = `
        position: absolute;
        right: 12px;
        top: 12px;
        background-color: #3b82f6;
        color: white;
        border: none;
        width: 44px;
        height: 44px;
        border-radius: 8px;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 10;
    `;
    
    // Position input container relatively
    inputContainer.style.position = 'relative';
    
    // Add hover effect
    micButton.addEventListener('mouseenter', function() {
        if (!isRecording) {
            micButton.style.backgroundColor = '#2563eb';
            micButton.style.transform = 'scale(1.05)';
        }
    });
    
    micButton.addEventListener('mouseleave', function() {
        if (!isRecording) {
            micButton.style.backgroundColor = '#3b82f6';
            micButton.style.transform = 'scale(1)';
        }
    });
    
    // Add click handler
    micButton.addEventListener('click', function(e) {
        e.preventDefault();
        toggleVoiceRecording();
    });
    
    // Add to container
    inputContainer.appendChild(micButton);
    
    console.log('[Voice] Microphone button added');
}

/**
 * Toggle voice recording
 */
function toggleVoiceRecording() {
    if (!recognition) {
        return;
    }
    
    if (isRecording) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error('[Voice] Failed to start recognition:', e);
        }
    }
}

/**
 * Update microphone button visual state
 */
function updateMicrophoneButtonState(recording) {
    const micButton = document.getElementById('voice-input-btn');
    if (!micButton) {
        return;
    }
    
    if (recording) {
        micButton.innerHTML = '⏹️';
        micButton.title = 'Click to stop recording';
        micButton.style.backgroundColor = '#ef4444';
        micButton.style.animation = 'pulse 1.5s infinite';
    } else {
        micButton.innerHTML = '🎤';
        micButton.title = 'Click to speak your question';
        micButton.style.backgroundColor = '#3b82f6';
        micButton.style.animation = 'none';
    }
}

/**
 * Add speaker button to response area
 */
function addSpeakerButton(responseDiv, answerText) {
    if (!responseDiv || !answerText) {
        return;
    }
    
    // Don't add if already exists
    if (responseDiv.querySelector('.voice-speaker-btn')) {
        return;
    }
    
    // Create speaker controls container
    const speakerControls = document.createElement('div');
    speakerControls.className = 'voice-speaker-controls';
    speakerControls.style.cssText = `
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        gap: 10px;
        align-items: center;
    `;
    
    // Create speaker button
    const speakerButton = document.createElement('button');
    speakerButton.className = 'voice-speaker-btn';
    speakerButton.innerHTML = '🔊 Play Answer';
    speakerButton.title = 'Listen to the answer';
    speakerButton.style.cssText = `
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    `;
    
    speakerButton.addEventListener('mouseenter', function() {
        speakerButton.style.backgroundColor = '#2563eb';
    });
    
    speakerButton.addEventListener('mouseleave', function() {
        speakerButton.style.backgroundColor = '#3b82f6';
    });
    
    speakerButton.addEventListener('click', function() {
        if (isSpeaking) {
            stopSpeech();
        } else {
            speakText(answerText, speakerButton);
        }
    });
    
    speakerControls.appendChild(speakerButton);
    responseDiv.appendChild(speakerControls);
    
    console.log('[Voice] Speaker button added');
}

/**
 * Speak text using text-to-speech
 */
function speakText(text, button) {
    if (!speechSynthesis || !text) {
        return;
    }
    
    // Stop any ongoing speech
    stopSpeech();
    
    // Clean markdown formatting from text
    const cleanText = text
        .replace(/[#*_`~]/g, '')  // Remove markdown symbols
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')  // Remove links but keep text
        .replace(/\n+/g, '. ')  // Replace newlines with periods
        .trim();
    
    // Create utterance
    currentUtterance = new SpeechSynthesisUtterance(cleanText);
    currentUtterance.lang = 'en-US';
    currentUtterance.rate = 1.0;
    currentUtterance.pitch = 1.0;
    currentUtterance.volume = 1.0;
    
    currentUtterance.onstart = function() {
        isSpeaking = true;
        if (button) {
            button.innerHTML = '⏸️ Stop';
            button.style.backgroundColor = '#ef4444';
        }
    };
    
    currentUtterance.onend = function() {
        isSpeaking = false;
        if (button) {
            button.innerHTML = '🔊 Play Answer';
            button.style.backgroundColor = '#3b82f6';
        }
    };
    
    currentUtterance.onerror = function(event) {
        console.error('[Voice] Speech synthesis error:', event.error);
        isSpeaking = false;
        if (button) {
            button.innerHTML = '🔊 Play Answer';
            button.style.backgroundColor = '#3b82f6';
        }
    };
    
    speechSynthesis.speak(currentUtterance);
    console.log('[Voice] Speaking:', cleanText.substring(0, 100) + '...');
}

/**
 * Stop current speech
 */
function stopSpeech() {
    if (speechSynthesis && isSpeaking) {
        speechSynthesis.cancel();
        isSpeaking = false;
    }
}

/**
 * Monitor for new responses and add speaker buttons
 */
const responseObserver = new MutationObserver(function(mutations) {
    // Look for agent response area updates
    const responseArea = document.getElementById('agent-response-area');
    if (!responseArea) {
        return;
    }
    
    // Find answer divs (successful responses have green background)
    const successDivs = responseArea.querySelectorAll('div[style*="rgb(240, 253, 244)"], div[style*="#f0fdf4"]');
    
    successDivs.forEach(function(div) {
        // Check if this div contains an answer
        const answerHeader = div.querySelector('h3');
        if (answerHeader && answerHeader.textContent.includes('Answer')) {
            // Find the markdown content
            const markdown = div.querySelector('.dash-markdown');
            if (markdown && !div.querySelector('.voice-speaker-btn')) {
                const answerText = markdown.textContent;
                addSpeakerButton(div, answerText);
            }
        }
    });
});

// Start observing response area
document.addEventListener('DOMContentLoaded', function() {
    const targetNode = document.body;
    responseObserver.observe(targetNode, {
        childList: true,
        subtree: true
    });
});

// Add CSS animation for pulsing effect
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }
`;
document.head.appendChild(style);

console.log('[Voice Controls] Initialized');
