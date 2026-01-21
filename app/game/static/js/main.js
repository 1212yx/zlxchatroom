// Initialize Socket
console.log("Loading main.js...");
let socket;
try {
    if (typeof io !== 'undefined') {
        socket = io('/game');
        socket.on('connect', () => {
            console.log('Connected to game server');
        });

        socket.on('player_joined', (data) => {
            console.log('Player joined:', data);
            // Optional: Notification
            const feedback = document.createElement('div');
            feedback.style.position = 'fixed';
            feedback.style.top = '20px';
            feedback.style.right = '20px';
            feedback.style.background = '#4CAF50';
            feedback.style.color = 'white';
            feedback.style.padding = '10px 20px';
            feedback.style.borderRadius = '5px';
            feedback.style.zIndex = '1000';
            feedback.innerText = data.msg;
            document.body.appendChild(feedback);
            setTimeout(() => feedback.remove(), 3000);
        });

        socket.on('join_success', (data) => {
            console.log('Joined room successfully:', data);
            // Transition to game
            lobbyScreen.classList.remove('active');
            setTimeout(() => {
                lobbyScreen.classList.add('hidden');
                gameScreen.classList.remove('hidden');
                void gameScreen.offsetWidth;
                gameScreen.classList.add('active');
                
                game.init('multi', currentDifficulty);
                updateModeDisplay('multi');
            }, 500);
        });

        socket.on('join_error', (data) => {
            alert(data.msg);
        });

        socket.on('update_player_list', (data) => {
            console.log('Update player list:', data);
            // Select the first player-list (which is for human players)
            const playerList = document.querySelector('.player-list');
            if (!playerList) return;
            
            playerList.innerHTML = '';
            
            if (data.players && Array.isArray(data.players)) {
                data.players.forEach(player => {
                    const item = document.createElement('div');
                    item.className = 'player-item';
                    
                    // Avatar (Simple default)
                    const avatarHtml = `
                        <div class="avatar user-avatar">
                            <svg class="icon-svg" viewBox="0 0 496 512" style="fill: #FFD54F;"><path d="M248 8C111 8 0 119 0 256s111 248 248 248 248-111 248-248S385 8 248 8zm0 96c48.6 0 88 39.4 88 88s-39.4 88-88 88-88-39.4-88-88 39.4-88 88-88zm0 344c-58.7 0-111.3-26.6-146.5-68.2 18.8-35.4 55.6-59.8 98.5-59.8 2.4 0 4.8 .4 7.1 1.1 13 4.2 26.6 6.9 40.9 6.9 14.3 0 28-2.7 40.9-6.9 2.3-.7 4.7-1.1 7.1-1.1 42.9 0 79.7 24.4 98.5 59.8C359.3 421.4 306.7 448 248 448z"/></svg>
                        </div>
                    `;
                    
                    // Role Badge
                    const roleHtml = player.role === 'host' ? '<span class="player-role">房主</span>' : '';
                    
                    // Name (Highlight self)
                    const isSelf = (socket && socket.id === player.sid) ? ' (我)' : '';
                    
                    item.innerHTML = `
                        ${avatarHtml}
                        <div class="player-info">
                            <span class="player-name">${player.name}${isSelf}</span>
                            ${roleHtml}
                        </div>
                    `;
                    
                    playerList.appendChild(item);
                });
            }
        });
    } else {
        console.warn('Socket.IO not loaded. Multiplayer features disabled.');
        socket = {
            emit: () => {},
            on: () => {}
        };
    }
} catch (e) {
    console.error('Socket initialization failed:', e);
    socket = {
        emit: () => {},
        on: () => {}
    };
}

// Initialize Game
let game;
try {
    game = new Game('game-canvas');
} catch (e) {
    console.error('Game initialization failed:', e);
}

let currentRoomId = null;
let currentMode = 'single';
let currentDifficulty = 'no_boundary';
let currentSkin = 'default';

// UI Elements
const menuScreen = document.getElementById('menu-screen');
const lobbyScreen = document.getElementById('lobby-screen');
const gameScreen = document.getElementById('game-screen');
const displayModeTags = {
    single: document.getElementById('display-mode-single'),
    ai: document.getElementById('display-mode-ai')
};
const leaderboardBody = document.querySelector('#leaderboard-table tbody');

// Bind Skin Selection Buttons
function bindSkinButtons() {
    document.querySelectorAll('.skin-option').forEach(btn => {
        btn.onclick = (e) => {
            const skin = e.target.dataset.skin;
            console.log("Skin selected:", skin);
            currentSkin = skin;
            
            // Update active state
            document.querySelectorAll('.skin-option').forEach(b => {
                if (b.dataset.skin === skin) b.classList.add('active');
                else b.classList.remove('active');
            });
        };
    });
}
bindSkinButtons();

// Event Listeners for Difficulty (Now Feature Modes)
// Use event delegation or re-bind since we added new elements dynamically (actually static in HTML now)
// But we need to make sure we select ALL .diff-btn
function bindDifficultyButtons() {
    document.querySelectorAll('.diff-btn').forEach(btn => {
        // Remove old listeners to prevent duplicates if called multiple times? 
        // Better: just add if not present, but simple replacement is fine if we don't call it often.
        // Actually, let's just use a clean event listener approach.
        btn.onclick = (e) => {
            const diff = e.target.dataset.diff;
            console.log("Difficulty selected:", diff);
            currentDifficulty = diff;
            
            // Update all buttons across screens
            document.querySelectorAll('.diff-btn').forEach(b => {
                if (b.dataset.diff === diff) b.classList.add('active');
                else b.classList.remove('active');
            });
            
            // Update display text
            const diffMap = {
                'no_boundary': '无边界',
                'obstacles': '障碍',
                'time_limit': '限时'
            };
            const diffText = document.getElementById('current-difficulty');
            if(diffText) diffText.innerText = diffMap[currentDifficulty];

            // If game is running (paused or active), maybe restart?
            // No, user needs to click restart manually to apply changes usually.
            // But if they are in menu, it just sets the state for next game.
        };
    });
}

// Call initially
bindDifficultyButtons();

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

// Bind Copy Button
const copyBtn = document.getElementById('copy-room-btn');
if(copyBtn) {
    copyBtn.addEventListener('click', () => {
        const roomInput = document.getElementById('lobby-room-input');
        if(roomInput && roomInput.value) {
            navigator.clipboard.writeText(roomInput.value).then(() => {
                // Show feedback (optional)
                const originalTitle = copyBtn.getAttribute('title');
                copyBtn.setAttribute('title', '已复制!');
                setTimeout(() => {
                    copyBtn.setAttribute('title', originalTitle);
                }, 2000);
                alert("房间号已复制: " + roomInput.value);
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        } else {
             alert("请先生成或输入房间号");
        }
    });
}

// Enforce Uppercase on Input
const roomInputEl = document.getElementById('lobby-room-input');
if(roomInputEl) {
    roomInputEl.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
}

// Join Room Function
function joinRoom() {
    const joinInput = document.getElementById('join-room-input');
    if (!joinInput) return;
    
    const roomId = joinInput.value.trim().toUpperCase();
    if (!roomId) {
        alert("请输入房间号");
        return;
    }
    
    if (roomId.length !== 6) {
        alert("房间号格式不正确 (6位字符)");
        return;
    }
    
    currentRoomId = roomId;
    console.log("Joining room:", currentRoomId);
    
    // Join the socket room
    socket.emit('join_game', { room: currentRoomId });
}

// Bind Join Button
const joinBtn = document.getElementById('join-room-btn');
if (joinBtn) {
    joinBtn.addEventListener('click', joinRoom);
}

// Bind Join Input Enter Key
const joinInputEl = document.getElementById('join-room-input');
if (joinInputEl) {
    joinInputEl.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            joinRoom();
        }
    });
    joinInputEl.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
}

// Start Game Function
function startGame(mode) {
    console.log("startGame called with mode:", mode); // Debug log
    if (!game) {
        console.error("Game instance not initialized");
        alert("游戏初始化失败，请刷新页面重试");
        return;
    }
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

             // Update Lobby Mode Display
             const diffMap = {
                 'no_boundary': '无边界',
                 'obstacles': '障碍',
                 'time_limit': '限时'
             };
             const modeText = document.querySelector('#lobby-mode-display .mode-text');
             if (modeText) {
                 modeText.innerText = diffMap[currentDifficulty] || '标准模式';
             }
        } else {
            // Show Game
            gameScreen.classList.remove('hidden');
            // Force reflow
            void gameScreen.offsetWidth; 
            gameScreen.classList.add('active');
            
            // Start Game Logic
            game.init(mode, currentDifficulty, currentSkin);
            updateModeDisplay(mode);
            
            // Stop menu music if playing
            if (window.audioManager) {
                window.audioManager.stop('login');
            }
        }

    }, 500);
}

// Explicitly attach to window immediately
window.startGame = startGame;
window.startMultiplayerGame = startMultiplayerGame;
window.leaveLobby = leaveLobby;
window.generateRoomId = generateRoomId;

function startMultiplayerGame() {
    const roomInput = document.getElementById('lobby-room-input');
    if (!roomInput || !roomInput.value) {
        alert("请输入或生成房间号");
        return;
    }
    currentRoomId = roomInput.value;
    
    // Join the socket room
    socket.emit('join_game', { room: currentRoomId });
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
    game.init(currentMode, currentDifficulty, currentSkin);
}

// Global exposure for Game class buttons
window.runGame = function() {
    game.run();
};
window.restartGame = restartGame;
window.exitGame = exitGame;

function exitGame() {
    game.isRunning = false;
    
    // Stop Game BGM
    if (window.audioManager) {
        window.audioManager.stop('bgm');
    }
    
    // Switch Screen
    gameScreen.classList.remove('active');
    setTimeout(() => {
        gameScreen.classList.add('hidden');
        menuScreen.classList.remove('hidden');
        void menuScreen.offsetWidth;
        menuScreen.classList.add('active');
        
        // Play menu music
        if (window.audioManager) {
            window.audioManager.play('login');
        }
        
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

// Skin Preview Feature
(function() {
    // Create Tooltip
    const tooltip = document.createElement('div');
    tooltip.id = 'skin-preview-tooltip';
    tooltip.innerHTML = `
        <div class='preview-title'></div>
        <canvas id='skin-preview-canvas' width='100' height='150'></canvas>
    `;
    document.body.appendChild(tooltip);

    const canvas = tooltip.querySelector('canvas');
    const ctx = canvas.getContext('2d');
    const titleEl = tooltip.querySelector('.preview-title');

    function showPreview(target, skinName) {
        const skinConfig = Utils.SKINS[skinName];
        if (!skinConfig) return;

        titleEl.textContent = skinConfig.name;
        tooltip.style.display = 'block';

        // Position
        const rect = target.getBoundingClientRect();
        tooltip.style.left = (rect.right + 15) + 'px';
        tooltip.style.top = (rect.top + rect.height / 2) + 'px';

        // Draw Snake Preview
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Mock Game Environment
        const blockSize = 25;
        const mockGame = { 
            tickRate: 100, 
            cols: 4, 
            rows: 6, 
            settings: {} 
        };
        
        // Create dummy snake centered
        let snake;
        try {
            snake = new Snake(mockGame, 0, 0);
        } catch(e) {
            console.error('Snake class not found');
            return;
        }

        snake.skinConfig = skinConfig;
        
        // Vertical Stacking: Head(1.5, 1) -> Body(1.5, 2) -> Body(1.5, 3) -> Body(1.5, 4)
        // Canvas is 100x150. Block 25.
        // X Center = 2.0 (50px).
        // Y Start = 1 (25px).
        // 1.5 * 25 = 37.5. Width 25. Right edge 62.5. Center 50. Perfect.
        
        snake.body = [
            {x: 1.5, y: 1}, // Head
            {x: 1.5, y: 2},
            {x: 1.5, y: 3},
            {x: 1.5, y: 4}
        ];
        
        // Set colors for basic skins
        if (!skinConfig.type) {
             snake.headColor = skinConfig.head;
             snake.bodyColor = skinConfig.body;
        }

        snake.draw(ctx, blockSize);
    }

    function hidePreview() {
        tooltip.style.display = 'none';
    }

    // Attach listeners
    // We need to wait for DOM to be ready if running early, but this is at end of file.
    // Also, if elements are dynamic (unlikely for main menu), this works.
    const options = document.querySelectorAll('.skin-option');
    options.forEach(option => {
        option.addEventListener('mouseenter', (e) => {
            showPreview(e.target, e.target.dataset.skin);
        });
        option.addEventListener('mouseleave', hidePreview);
    });
})();

// Auto-play Login BGM on load
window.addEventListener('load', () => {
    if (window.audioManager) {
        // Try to play immediately
        const promise = window.audioManager.play('login');
        if (promise !== undefined) {
            promise.catch(error => {
                console.log("Auto-play prevented. Waiting for user interaction.");
                // Add one-time listener to start audio on first interaction
                const startAudio = () => {
                    window.audioManager.play('login');
                    document.removeEventListener('click', startAudio);
                    document.removeEventListener('keydown', startAudio);
                };
                document.addEventListener('click', startAudio);
                document.addEventListener('keydown', startAudio);
            });
        }
    }
});

