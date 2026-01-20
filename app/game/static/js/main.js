// Initialize Game
const game = new Game('game-canvas');
let currentMode = 'single';
let currentDifficulty = 'medium';

// UI Elements
const menuScreen = document.getElementById('menu-screen');
const lobbyScreen = document.getElementById('lobby-screen');
const gameScreen = document.getElementById('game-screen');
const displayModeTags = {
    single: document.getElementById('display-mode-single'),
    ai: document.getElementById('display-mode-ai')
};
const leaderboardBody = document.querySelector('#leaderboard-table tbody');

// Event Listeners for Difficulty
document.querySelectorAll('.diff-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const diff = e.target.dataset.diff;
        currentDifficulty = diff;
        
        // Update all buttons across screens
        document.querySelectorAll('.diff-btn').forEach(b => {
            if (b.dataset.diff === diff) b.classList.add('active');
            else b.classList.remove('active');
        });
        
        // Update display text
        const diffMap = {
            'easy': '简单',
            'medium': '中等',
            'hard': '困难',
            'expert': '专家'
        };
        const diffText = document.getElementById('current-difficulty');
        if(diffText) diffText.innerText = diffMap[currentDifficulty];
    });
});

// Leaderboard Function
function updateLeaderboard() {
    let leaderboard = [];
    try {
        leaderboard = JSON.parse(localStorage.getItem('snakeLeaderboard') || '[]');
    } catch (e) {
        console.warn('Storage not available', e);
    }
    
    leaderboardBody.innerHTML = '';
    
    if (leaderboard.length === 0) {
        leaderboardBody.innerHTML = '<tr><td colspan="4">暂无数据</td></tr>';
        return;
    }

    leaderboard.forEach((entry, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${entry.name}</td>
            <td>${entry.score}</td>
            <td>${entry.date}</td>
        `;
        leaderboardBody.appendChild(row);
    });
}

// Room ID Generator
function generateRoomId() {
    const roomId = Math.random().toString(36).substring(2, 8).toUpperCase();
    const roomInput = document.getElementById('lobby-room-input');
    if(roomInput) {
        roomInput.value = roomId;
    }
    return roomId;
}

// Bind Generate Button
const generateBtn = document.getElementById('generate-room-btn');
if(generateBtn) {
    generateBtn.addEventListener('click', generateRoomId);
}

// Enforce Uppercase on Input
const roomInputEl = document.getElementById('lobby-room-input');
if(roomInputEl) {
    roomInputEl.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
}

// Start Game Function
function startGame(mode) {
    currentMode = mode;
    
    // Switch Screen
    menuScreen.classList.remove('active');
    setTimeout(() => {
        menuScreen.classList.add('hidden');
        
        if (mode === 'multi') {
             // Show Lobby
             lobbyScreen.classList.remove('hidden');
             void lobbyScreen.offsetWidth;
             lobbyScreen.classList.add('active');
             
             // Generate Random Room ID if empty
             const roomInput = document.getElementById('lobby-room-input');
             if(roomInput && !roomInput.value) {
                 generateRoomId();
             }
        } else {
            // Show Game
            gameScreen.classList.remove('hidden');
            // Force reflow
            void gameScreen.offsetWidth; 
            gameScreen.classList.add('active');
            
            // Start Game Logic
            game.init(mode, currentDifficulty);
            updateModeDisplay(mode);
        }

    }, 500);
}

function startMultiplayerGame() {
    lobbyScreen.classList.remove('active');
    setTimeout(() => {
        lobbyScreen.classList.add('hidden');
        gameScreen.classList.remove('hidden');
        void gameScreen.offsetWidth;
        gameScreen.classList.add('active');
        
        game.init('multi', currentDifficulty);
        updateModeDisplay('multi');
    }, 500);
}

function leaveLobby() {
    lobbyScreen.classList.remove('active');
    setTimeout(() => {
        lobbyScreen.classList.add('hidden');
        menuScreen.classList.remove('hidden');
        void menuScreen.offsetWidth;
        menuScreen.classList.add('active');
    }, 500);
}

function updateModeDisplay(mode) {
    Object.values(displayModeTags).forEach(el => el.classList.remove('active'));
    if (mode === 'single') displayModeTags.single.classList.add('active');
    else if (mode === 'ai') displayModeTags.ai.classList.add('active');
    else {
         displayModeTags.single.innerText = "玩家1";
         displayModeTags.ai.innerText = "玩家2";
         displayModeTags.single.classList.add('active');
         displayModeTags.ai.classList.add('active');
    }
}

function restartGame() {
    game.init(currentMode, currentDifficulty);
}

// Global exposure for Game class buttons
window.runGame = function() {
    game.run();
};
window.restartGame = restartGame;
window.exitGame = exitGame;

function exitGame() {
    game.isRunning = false;
    
    // Switch Screen
    gameScreen.classList.remove('active');
    setTimeout(() => {
        gameScreen.classList.add('hidden');
        menuScreen.classList.remove('hidden');
        void menuScreen.offsetWidth;
        menuScreen.classList.add('active');
        
        // Update Leaderboard
        updateLeaderboard();
    }, 500);
}

function togglePause() {
    game.togglePause();
}

// Keyboard Input
window.addEventListener('keydown', (e) => {
    // Prevent scrolling with arrows/space
    if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].indexOf(e.key) > -1) {
        e.preventDefault();
    }
    game.handleInput(e.key);
});

// Handle Window Resize
window.addEventListener('resize', () => {
    // Optional: Resize canvas dynamically if needed
});

// Init Leaderboard
updateLeaderboard();
