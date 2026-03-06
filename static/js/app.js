/**
 * app.js — Jarvis 2.0 Web Frontend Logic
 *
 * Handles:
 *  • WebSocket communication with the Flask backend
 *  • Chat rendering
 *  • Voice input via Web Speech API
 *  • Particle background animation
 *  • Orb state management
 */

// ═══════════════════════════════════════════════
//  DOM refs
// ═══════════════════════════════════════════════
const chatLog       = document.getElementById("chat-log");
const commandInput  = document.getElementById("command-input");
const sendBtn       = document.getElementById("send-btn");
const micBtn        = document.getElementById("mic-btn");
const statusDot     = document.getElementById("status-dot");
const statusText    = document.getElementById("status-text");
const orbWrapper    = document.querySelector(".orb-wrapper");
const soundWaves    = document.getElementById("sound-waves");
const commandCount  = document.getElementById("command-count");
const clockEl       = document.getElementById("clock");
const avatarSub     = document.getElementById("avatar-subtitle");
const canvas        = document.getElementById("particles-canvas");

// ═══════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════
let currentState  = "idle";
let isVoiceActive = false;
let recognition   = null;
let cmdCount      = 0;

// ═══════════════════════════════════════════════
//  WebSocket connection
// ═══════════════════════════════════════════════
const socket = io();

socket.on("connect", () => {
    addSystemMessage("Connected to Jarvis backend.");
});

socket.on("disconnect", () => {
    addSystemMessage("Connection lost. Reconnecting…");
    setOrbState("error");
});

socket.on("greeting", (data) => {
    addJarvisMessage(data.message);
});

socket.on("response", (data) => {
    removeTypingIndicator();
    addJarvisMessage(data.message);
    if (data.command_count !== undefined) {
        cmdCount = data.command_count;
        commandCount.textContent = `Commands: ${cmdCount}`;
    }
    // Use browser TTS
    speakTTS(data.message);
});

socket.on("status", (data) => {
    setOrbState(data.status);
});

socket.on("error", (data) => {
    removeTypingIndicator();
    addErrorMessage(data.message);
    setOrbState("error");
});

// ─── Scheduled reminder from server ───
socket.on("reminder", (data) => {
    addJarvisMessage("🔔 " + data.message);
    speakTTS(data.message);
});

// ═══════════════════════════════════════════════
//  Send command
// ═══════════════════════════════════════════════
function sendCommand(text) {
    if (!text || !text.trim()) return;
    text = text.trim();

    addUserMessage(text);
    showTypingIndicator();
    setOrbState("processing");

    // Send via websocket
    socket.emit("command", { command: text });
}

// Event listeners
sendBtn.addEventListener("click", () => {
    sendCommand(commandInput.value);
    commandInput.value = "";
    commandInput.focus();
});

commandInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        sendCommand(commandInput.value);
        commandInput.value = "";
    }
});

// Quick command pills
document.querySelectorAll(".pill").forEach((pill) => {
    pill.addEventListener("click", () => {
        const cmd = pill.dataset.cmd;
        if (cmd) sendCommand(cmd);
    });
});

// ═══════════════════════════════════════════════
//  Chat message rendering
// ═══════════════════════════════════════════════
function createTimestamp() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addMessage(type, sender, text) {
    const msg = document.createElement("div");
    msg.classList.add("message", type);

    msg.innerHTML = `
        <div class="msg-header">
            <span>${sender}</span>
            <span class="msg-time">${createTimestamp()}</span>
        </div>
        <div class="msg-body">${escapeHtml(text)}</div>
    `;

    chatLog.appendChild(msg);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function addJarvisMessage(text) {
    addMessage("jarvis", "◆ JARVIS", text);
}

function addUserMessage(text) {
    addMessage("user", "YOU", text);
    cmdCount++;
    commandCount.textContent = `Commands: ${cmdCount}`;
}

function addSystemMessage(text) {
    addMessage("system", "⚙ SYSTEM", text);
}

function addErrorMessage(text) {
    addMessage("error", "✖ ERROR", text);
}

function showTypingIndicator() {
    removeTypingIndicator();
    const indicator = document.createElement("div");
    indicator.classList.add("message", "jarvis");
    indicator.id = "typing-indicator";
    indicator.innerHTML = `
        <div class="msg-header">
            <span>◆ JARVIS</span>
        </div>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    chatLog.appendChild(indicator);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function removeTypingIndicator() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════
//  Orb state management
// ═══════════════════════════════════════════════
const STATE_MAP = {
    idle:       { label: "Ready",         dotClass: "" },
    waiting:    { label: "Say \"Hey Jarvis\"…", dotClass: "" },
    listening:  { label: "Listening…",    dotClass: "listening" },
    processing: { label: "Processing…",   dotClass: "processing" },
    speaking:   { label: "Speaking…",     dotClass: "speaking" },
    error:      { label: "Error",         dotClass: "error" },
};

function setOrbState(state) {
    currentState = state;
    const info = STATE_MAP[state] || STATE_MAP.idle;

    // Orb wrapper class
    orbWrapper.className = "orb-wrapper";
    if (state !== "idle") orbWrapper.classList.add(state);

    // Status dot
    statusDot.className = "status-dot";
    if (info.dotClass) statusDot.classList.add(info.dotClass);

    // Status text
    statusText.textContent = info.label;

    // Avatar subtitle
    avatarSub.textContent = info.label;

    // Sound waves
    if (state === "speaking") {
        soundWaves.classList.add("active");
    } else {
        soundWaves.classList.remove("active");
    }
}

// ═══════════════════════════════════════════════
//  Browser Text-to-Speech
// ═══════════════════════════════════════════════
function speakTTS(text) {
    if (!("speechSynthesis" in window)) return;

    setOrbState("speaking");

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Try to pick an English voice
    const voices = speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes("Zira") || v.name.includes("Google UK English Female"));
    if (preferred) utterance.voice = preferred;

    utterance.onend = () => {
        setOrbState(isVoiceActive ? "waiting" : "idle");
    };

    speechSynthesis.speak(utterance);
}

// Load voices
if ("speechSynthesis" in window) {
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
}

// ═══════════════════════════════════════════════
//  Voice Input — Web Speech API
// ═══════════════════════════════════════════════
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Web Speech API not supported");
        return null;
    }

    const rec = new SpeechRecognition();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.continuous = false;

    rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        console.log("[Voice]", transcript);

        sendCommand(transcript);
        // Restart listening after a short pause
        if (isVoiceActive) {
            setTimeout(() => {
                setOrbState("waiting");
                startListening();
            }, 1500);
        }
    };

    rec.onspeechend = () => {
        rec.stop();
    };

    rec.onerror = (event) => {
        console.warn("[Voice Error]", event.error);
        if (event.error === "no-speech" && isVoiceActive) {
            // Silently restart
            startListening();
        } else if (event.error === "not-allowed") {
            addErrorMessage("Microphone permission denied. Please allow microphone access.");
            deactivateVoice();
        }
    };

    rec.onend = () => {
        if (isVoiceActive && currentState !== "processing" && currentState !== "speaking") {
            // Restart listening loop
            setTimeout(() => startListening(), 500);
        }
    };

    return rec;
}

function startListening() {
    if (!recognition || !isVoiceActive) return;
    try {
        setOrbState("listening");
        recognition.start();
    } catch (e) {
        // Already started — ignore
    }
}

function activateVoice() {
    isVoiceActive = true;
    recognition = initSpeechRecognition();
    if (!recognition) {
        addErrorMessage("Voice input not supported in this browser. Use Chrome for best results.");
        isVoiceActive = false;
        return;
    }
    micBtn.classList.add("active");
    addSystemMessage("Voice mode activated. Start speaking…");
    setOrbState("listening");
    startListening();
}

function deactivateVoice() {
    isVoiceActive = false;
    if (recognition) {
        try { recognition.abort(); } catch (e) { /* ignore */ }
        recognition = null;
    }
    micBtn.classList.remove("active");
    setOrbState("idle");
    addSystemMessage("Voice mode deactivated.");
}

micBtn.addEventListener("click", () => {
    if (isVoiceActive) {
        deactivateVoice();
    } else {
        activateVoice();
    }
});

// ═══════════════════════════════════════════════
//  Clock
// ═══════════════════════════════════════════════
function updateClock() {
    const now = new Date();
    const options = { weekday: "long", month: "short", day: "numeric" };
    const date = now.toLocaleDateString("en-US", options);
    const time = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    clockEl.textContent = `${date}  •  ${time}`;
}

updateClock();
setInterval(updateClock, 30000);

// ═══════════════════════════════════════════════
//  Particle Background
// ═══════════════════════════════════════════════
(function initParticles() {
    const ctx = canvas.getContext("2d");
    let particles = [];
    const PARTICLE_COUNT = 60;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            size: Math.random() * 2 + 0.5,
            opacity: Math.random() * 0.4 + 0.1,
        };
    }

    function init() {
        resize();
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push(createParticle());
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach((p) => {
            p.x += p.vx;
            p.y += p.vy;

            // Wrap around
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 212, 255, ${p.opacity})`;
            ctx.fill();
        });

        // Draw lines between close particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 212, 255, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }

    window.addEventListener("resize", resize);
    init();
    draw();
})();

// ═══════════════════════════════════════════════
//  Keyboard shortcut: Ctrl+M to toggle mic
// ═══════════════════════════════════════════════
document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "m") {
        e.preventDefault();
        micBtn.click();
    }
});

// Focus input on load
commandInput.focus();
