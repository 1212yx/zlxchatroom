class AudioManager {
    constructor() {
        this.sounds = {};
        this.pendingPlay = null; // Track pending play requests

        const sources = {
            click: { src: '/game/static/mp4/click.mp4?v=2.2', loop: false, volume: 1.0 },
            login: { src: '/game/static/mp4/menu_bgm.mp4?v=2.2', loop: true, volume: 0.5 },
            bgm: { src: '/game/static/mp4/game_bgm.mp4?v=2.2', loop: true, volume: 0.5 },
            win: { src: '/game/static/mp4/win.mp4?v=2.2', loop: false, volume: 1.0 },
            fail: { src: '/game/static/mp4/fail.mp4?v=2.2', loop: false, volume: 1.0 }
        };

        // Initialize Audio objects
        Object.keys(sources).forEach(key => {
            const config = sources[key];
            const audio = new Audio();
            audio.loop = config.loop;
            audio.volume = config.volume;
            // Don't set src yet, wait for fetch
            this.sounds[key] = audio;
            this._loadSound(key, config.src);
        });
        
        this.muted = localStorage.getItem('snakeMuted') === 'true';
        this.updateMuteState();
    }

    async _loadSound(key, src) {
        try {
            const response = await fetch(src);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            const sound = this.sounds[key];
            if (sound) {
                sound.src = url;
                // If this sound was pending to play, play it now
                if (this.pendingPlay === key) {
                    this.pendingPlay = null;
                    const p = this.play(key);
                    if (p) p.catch(e => console.debug('Autoplay prevented during load:', e));
                }
            }
        } catch (e) {
            console.warn(`Error loading audio ${src}:`, e);
            // Fallback: try setting src directly if fetch fails
            if (this.sounds[key] && !this.sounds[key].src) {
                this.sounds[key].src = src;
            }
        }
    }

    play(name) {
        if (this.muted) return;
        const sound = this.sounds[name];
        if (sound) {
            // Check if src is ready
            if (!sound.src) {
                console.log(`Audio ${name} not ready yet, queuing...`);
                this.pendingPlay = name;
                return;
            }

            // For looping sounds (BGM), if already playing, do nothing
            if (sound.loop && !sound.paused) {
                return Promise.resolve();
            }

            // For one-shot sounds or if BGM is stopped, reset and play
            // Only reset if not already at 0 to avoid triggering unnecessary seeks/aborts
            if (sound.currentTime !== 0) {
                sound.currentTime = 0;
            }
            
            // Return the promise directly so caller can handle errors (like autoplay policy)
            return sound.play();
        }
    }

    stop(name) {
        const sound = this.sounds[name];
        if (sound) {
            // Only pause if not already paused to avoid unnecessary aborts
            if (!sound.paused) {
                sound.pause();
            }
            // Do NOT reset currentTime here to avoid triggering new requests/aborts
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        localStorage.setItem('snakeMuted', this.muted);
        this.updateMuteState();
        return this.muted;
    }

    updateMuteState() {
        if (this.muted) {
            this.stop('bgm');
            this.stop('login');
        } else {
            if (window.game && window.game.isRunning) {
                 this.play('bgm');
            }
        }
    }
}

const audioManager = new AudioManager();
window.audioManager = audioManager;

// Global Click Sound
document.addEventListener('click', (e) => {
    // Check if clicked element is interactive
    if (e.target.tagName === 'BUTTON' || 
        e.target.closest('button') || 
        e.target.classList.contains('mode-card') || 
        e.target.closest('.mode-card') ||
        e.target.classList.contains('skin-option') ||
        e.target.classList.contains('diff-btn') ||
        e.target.tagName === 'A') {
        audioManager.play('click').catch(() => {}); // Catch potential errors to avoid console noise
    }
});

// Settings UI Logic
document.addEventListener('DOMContentLoaded', () => {
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const soundToggle = document.getElementById('sound-toggle');

    if (settingsBtn) {
        settingsBtn.onclick = () => settingsModal.classList.add('active');
    }
    if (closeSettingsBtn) {
        closeSettingsBtn.onclick = () => settingsModal.classList.remove('active');
    }
    if (soundToggle) {
        soundToggle.checked = !audioManager.muted;
        soundToggle.onchange = () => {
            audioManager.toggleMute();
        };
    }
    
    // Play Login sound on first interaction if on menu
    const playLogin = () => {
        if (document.getElementById('menu-screen').classList.contains('active')) {
            const p = audioManager.play('login');
            if (p) p.catch(() => {});
        }
        document.removeEventListener('click', playLogin);
    };
    document.addEventListener('click', playLogin);
});

class Game {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.gridSize = 20; // Size of each cell
        this.cols = this.canvas.width / this.gridSize;
        this.rows = this.canvas.height / this.gridSize;

        this.snakes = [];
        this.foods = [];
        this.mode = 'single'; // single, ai, multi
        this.difficulty = 'medium';
        this.isRunning = false;
        this.isPaused = false;
        this.lastTime = 0;
        this.accumulatedTime = 0;
        this.tickRate = 150; // ms per frame (lower is faster)
        this.baseTickRate = 150;

        this.settings = {
            noBoundary: false,
            obstacles: false,
            timeLimit: false
        };

        // UI Elements
        this.scoreEl = document.getElementById('score');
        this.lengthEl = document.getElementById('length');
        this.highScoreEl = document.getElementById('high-score');
        this.overlay = document.getElementById('game-overlay');
        this.overlayTitle = document.getElementById('overlay-title');
        this.overlayMsg = document.getElementById('overlay-message');

        try {
            this.highScore = localStorage.getItem('snakeHighScore') || 0;
        } catch (e) {
            console.warn('Storage not available', e);
            this.highScore = 0;
        }
        this.highScoreEl.innerText = this.highScore;
        
        // Bind loop
        this.loop = this.loop.bind(this);
    }

    init(mode, difficulty, skinName = 'default') {
        window.audioManager.stop('login');
        this.mode = mode;
        this.difficulty = difficulty; // "no_boundary", "obstacles", "time_limit"
        this.snakes = [];
        this.foods = [];
        this.obstacles = []; // Init obstacles
        this.isRunning = false;
        this.isPaused = false;
        
        // Resolve Skin
        const skinConfig = Utils.SKINS[skinName] || Utils.SKINS['default'];

        // Reset Settings
        this.settings = {
            noBoundary: false,
            obstacles: false,
            timeLimit: false
        };

        // Apply Feature Mode Settings
        if (difficulty === 'no_boundary') {
            this.settings.noBoundary = true;
        } else if (difficulty === 'obstacles') {
            this.settings.obstacles = true;
            this.spawnObstacles();
        } else if (difficulty === 'time_limit') {
            this.settings.timeLimit = true;
            this.timeLeft = 60000; // 60 seconds
        }

        // Set Base Speed (Default Medium for all feature modes)
        this.baseTickRate = 150; 
        this.tickRate = this.baseTickRate;

        // Init Player Snake
        const playerSnake = new Snake(this, 5, 5, false, skinConfig, '我');
        this.snakes.push(playerSnake);

        // Init AI or P2
        if (mode === 'ai') {
            const aiSnake = new Snake(this, 25, 25, true, null, 'AI');
            this.snakes.push(aiSnake);
        } else if (mode === 'multi') {
            // AI Opponents (matching Lobby UI)
            // AI 1 (Top Right)
            const ai1 = new Snake(this, this.cols - 6, 6, true, null, 'AI-1');
            this.snakes.push(ai1);
            
            // AI 2 (Bottom Left)
            const ai2 = new Snake(this, 6, this.rows - 6, true, null, 'AI-2');
            this.snakes.push(ai2);
        }

        // Spawn Initial Food
        this.spawnFood();

        // Reset Stats
        this.updateStats();

        // Draw Initial State
        this.draw();

        // Show Ready Overlay
        this.showReadyScreen();
    }

    spawnObstacles() {
        this.obstacles = [];
        // Increase obstacle count slightly for better challenge
        const obstacleCount = 20; 

        for (let i = 0; i < obstacleCount; i++) {
            let valid = false;
            let pos;
            let attempts = 0;
            
            // Try to find a valid position
            while (!valid && attempts < 100) {
                attempts++;
                pos = Utils.randomGridPosition(this.cols, this.rows);
                
                // Safety Zone for Player Start (Top Left area)
                // Snake starts at 5,5. Avoid a 5-cell radius around it.
                if (Math.abs(pos.x - 5) < 5 && Math.abs(pos.y - 5) < 5) continue;
                
                // Safety Zone for AI/P2 Start (Bottom Right area)
                if (this.mode !== 'single') {
                     if (Math.abs(pos.x - 25) < 5 && Math.abs(pos.y - 25) < 5) continue;
                }

                // Avoid overlap with existing obstacles
                if (this.obstacles.some(obs => Utils.isSamePosition(obs, pos))) continue;
                
                valid = true;
            }
            
            if (valid) {
                this.obstacles.push(pos);
            }
        }
    }

    run() {
        if (this.isRunning) return;
        const p = window.audioManager.play('bgm');
        if (p) p.catch(e => console.warn('Game BGM play failed:', e));
        this.isRunning = true;
        this.overlay.classList.add('hidden');
        this.lastTime = performance.now();
        requestAnimationFrame(this.loop);
    }

    showReadyScreen() {
        this.overlayTitle.innerText = "准备好了吗？";
        this.overlayMsg.innerText = "点击下方按钮开始游戏";
        
        // Update Buttons for Ready Screen
        const content = this.overlay.querySelector('.overlay-content');
        // Remove existing buttons logic is tricky if we want to preserve event listeners if they were static, 
        // but since we use global functions, we can just replace innerHTML for buttons or toggle visibility.
        // Let's replace the button container part.
        
        // To be safe and keep it simple, let's just clear and rebuild buttons
        // We need to keep title and msg elements references valid? 
        // Actually, innerText updates on existing elements are fine.
        // But we need to change the buttons.
        
        // Let's find the button container or just append/replace buttons.
        // The HTML structure is h2, p, btn, btn.
        
        // Quickest way without breaking references to title/msg if they are cached?
        // this.overlayTitle and this.overlayMsg are cached in constructor. 
        // If I overwrite innerHTML of .overlay-content, I lose those references? 
        // Yes, if I overwrite the parent.
        
        // So let's manipulate the buttons directly.
        // Remove old buttons
        const oldBtns = this.overlay.querySelectorAll('button');
        oldBtns.forEach(btn => btn.remove());

        // Add Start Button
        const startBtn = document.createElement('button');
        startBtn.className = 'btn btn-primary';
        startBtn.innerText = '开始游戏';
        startBtn.onclick = () => window.runGame(); // We will define this global wrapper
        
        const exitBtn = document.createElement('button');
        exitBtn.className = 'btn btn-secondary';
        exitBtn.innerText = '返回菜单';
        exitBtn.onclick = () => window.exitGame();

        const container = this.overlay.querySelector('.overlay-content');
        container.appendChild(startBtn);
        container.appendChild(exitBtn);

        this.overlay.classList.remove('hidden');
    }

    loop(timestamp) {
        if (!this.isRunning) return;
        
        if (!this.isPaused) {
            const deltaTime = timestamp - this.lastTime;
            this.lastTime = timestamp;
            this.accumulatedTime += deltaTime;
            this.deltaTime = deltaTime; // Store for timers

            // Update Game Logic based on tick rate
            if (this.accumulatedTime >= this.tickRate) {
                this.update();
                this.accumulatedTime -= this.tickRate;
            }
        } else {
            this.lastTime = timestamp; // Prevent jump after unpause
        }

        this.draw();
        requestAnimationFrame(this.loop);
    }

    update() {
        // Update Timer for Time Limit Mode
        if (this.settings.timeLimit && this.isRunning && !this.isPaused) {
            this.timeLeft -= this.tickRate; // Use tickRate (logic step) for correct time subtraction
            if (this.timeLeft <= 0) {
                 this.timeLeft = 0;
                 this.gameOver(this.snakes[0].score, "时间到！");
                 return;
            }
        }

        // Update Snakes
        this.snakes.forEach(snake => snake.update());

        // Check Collisions
        this.checkCollisions();

        // Check Food
        this.checkFood();

        // Update Speed based on Player 1 Length (Simple Rule Implementation)
        const p1 = this.snakes[0];
        if (p1) {
            if (p1.length > 20) this.tickRate = this.baseTickRate * 0.6;
            else if (p1.length > 10) this.tickRate = this.baseTickRate * 0.8;
            else this.tickRate = this.baseTickRate;
        }

        // Spawn Food if low (Maintain multiple scattered foods)
        // User Request: "Food appears randomly and multiple scattered"
        const TARGET_FOOD_COUNT = 5; 
        const currentFoodCount = this.foods.filter(f => f.active).length;
        
        if (currentFoodCount < TARGET_FOOD_COUNT) {
            // Fill up gradually or immediately
            if (Math.random() < 0.2) this.spawnFood(); 
        }

        this.updateStats();
    }

    checkCollisions() {
        this.snakes.forEach(snake => {
            if (snake.isDead) return;

            const head = snake.body[0];

            // 1. Self Collision (handled in Snake logic mostly, but double check)
            if (!snake.invincible && snake.onSnake(head, true)) {
                snake.die();
            }

            // Obstacle Collision
            if (this.settings.obstacles) {
                 this.obstacles.forEach(obs => {
                     if (Utils.isSamePosition(head, obs)) {
                         if (!snake.invincible) {
                             snake.die();
                         }
                     }
                 });
            }

            // 2. Other Snake Collision
            this.snakes.forEach(other => {
                if (snake === other || other.isDead) return;
                if (other.onSnake(head)) {
                    if (!snake.invincible) {
                        snake.die();
                        // Bonus for killer?
                        if (!other.isAI) other.score += 50; 
                    }
                }
            });
        });

        // Check Game Over Conditions
        const aliveSnakes = this.snakes.filter(s => !s.isDead);
        if (this.mode === 'single') {
            if (aliveSnakes.length === 0) {
                this.gameOver(this.snakes[0].score);
            }
        } else {
            // Multi/AI: Last one standing wins or time limit
            // Simple: If player dies, game over (or if AI dies, Player wins)
            const p1 = this.snakes[0];
            if (p1.isDead) {
                this.gameOver(p1.score, "失败！");
            } else if (aliveSnakes.length === 1 && aliveSnakes[0] === p1) {
                this.gameOver(p1.score, "胜利！");
            }
        }
    }

    checkFood() {
        const now = performance.now();
        const COMBO_WINDOW = 4000; // 4 seconds window for combo

        this.snakes.forEach(snake => {
            if (snake.isDead) return;
            const head = snake.body[0];

            this.foods.forEach(food => {
                if (!food.active) return;
                if (Utils.isSamePosition(head, food.position)) {
                    // Eat Food
                    food.active = false;

                    // --- Scoring Logic ---
                    let scoreGain = food.score;

                    // 1. Length Bonus (Only for Normal Food)
                    // "Length longer, score higher (e.g. length 20+ -> +20)"
                    if (food.type === 'normal') {
                        if (snake.length > 20) {
                            scoreGain += 20;
                        } else if (snake.length > 10) {
                            scoreGain += 10;
                        }
                    }

                    // 2. Combo System
                    // "Continuous eat 3+, every extra 1 adds +5"
                    if (now - snake.lastEatTime < COMBO_WINDOW) {
                        snake.comboCount++;
                    } else {
                        snake.comboCount = 1;
                    }
                    snake.lastEatTime = now;

                    if (snake.comboCount >= 3) {
                        scoreGain += 5;
                    }
                    
                    snake.score += scoreGain;
                    
                    // Apply Effect
                    if (food.effect === 'grow') {
                        snake.grow(1);
                    } else if (food.effect === 'shrink') {
                        // "Snake length - 1 (only effective when length > 3)"
                        if (snake.length > 3) {
                            snake.shrink(1);
                        }
                    } else if (food.effect === 'invincible') {
                        // "Short time (5s) immune to collision (pass through wall / self)"
                        snake.makeInvincible(5000);
                    }

                    // Update High Score
                    if (snake === this.snakes[0]) {
                         if (snake.score > this.highScore) {
                            this.highScore = snake.score;
                            try {
                                localStorage.setItem('snakeHighScore', this.highScore);
                            } catch (e) {
                                console.warn('Storage not available', e);
                            }
                        }
                    }
                   
                    // Spawn new immediately to maintain count (Eat one, appear one)
                    this.spawnFood();

                }
            });
        });

        // Cleanup inactive foods
        this.foods = this.foods.filter(f => f.active);
    }

    spawnFood() {
        // Random Type
        const r = Math.random();
        let type = 'normal';
        if (r > 0.9) type = 'invincible';
        else if (r > 0.8) type = 'shorten';
        else if (r > 0.7) type = 'bonus';

        this.foods.push(new Food(this, type));
    }

    draw() {
        // Clear
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw Grid (Optional, makes it look techy)
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        /*
        for (let x = 0; x <= this.canvas.width; x += this.gridSize) {
            this.ctx.beginPath(); this.ctx.moveTo(x, 0); this.ctx.lineTo(x, this.canvas.height); this.ctx.stroke();
        }
        for (let y = 0; y <= this.canvas.height; y += this.gridSize) {
            this.ctx.beginPath(); this.ctx.moveTo(0, y); this.ctx.lineTo(this.canvas.width, y); this.ctx.stroke();
        }
        */

        // Draw Obstacles
        if (this.settings.obstacles) {
            this.obstacles.forEach(obs => {
                const x = obs.x * this.gridSize;
                const y = obs.y * this.gridSize;
                const s = this.gridSize;
                
                // Draw 3D Block Style
                // Main Face
                this.ctx.fillStyle = '#795548'; // Brown
                this.ctx.fillRect(x, y, s, s);
                
                // Top/Left Highlight (Bevel)
                this.ctx.beginPath();
                this.ctx.moveTo(x + s, y);
                this.ctx.lineTo(x, y);
                this.ctx.lineTo(x, y + s);
                this.ctx.strokeStyle = '#A1887F'; // Light Brown
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
                
                // Bottom/Right Shadow (Bevel)
                this.ctx.beginPath();
                this.ctx.moveTo(x + s, y);
                this.ctx.lineTo(x + s, y + s);
                this.ctx.lineTo(x, y + s);
                this.ctx.strokeStyle = '#4E342E'; // Dark Brown
                this.ctx.stroke();
                
                // Inner Detail
                this.ctx.fillStyle = '#6D4C41';
                this.ctx.fillRect(x + 4, y + 4, s - 8, s - 8);
            });
        }

        // Draw Foods
        this.foods.forEach(food => food.draw(this.ctx, this.gridSize));

        // Draw Snakes
        this.snakes.forEach(snake => snake.draw(this.ctx, this.gridSize));

        // Draw Timer
        if (this.settings.timeLimit) {
            this.ctx.fillStyle = 'white';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(`Time: ${Math.ceil(this.timeLeft / 1000)}`, this.canvas.width / 2, 40);
        }
    }

    handleInput(key) {
        if (!this.isRunning || this.isPaused) return;

        const p1 = this.snakes[0];
        
        // P1 Controls (WASD or Arrows if Single/AI)
        // If Multi, P1 is WASD, P2 is Arrows
        
        // General Controls
        if (key === ' ') {
            // Speed Boost (Skip next wait)
            this.accumulatedTime += 50; 
            return;
        }

        // Direction Map
        const dirs = {
            'ArrowUp': {x: 0, y: -1},
            'w': {x: 0, y: -1},
            'ArrowDown': {x: 0, y: 1},
            's': {x: 0, y: 1},
            'ArrowLeft': {x: -1, y: 0},
            'a': {x: -1, y: 0},
            'ArrowRight': {x: 1, y: 0},
            'd': {x: 1, y: 0}
        };

        if (this.mode === 'multi') {
            // Split Controls
            const p2 = this.snakes[1];
            
            if (['w','s','a','d'].includes(key.toLowerCase())) {
                p1.changeDirection(dirs[key.toLowerCase()]);
            } else if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(key)) {
                if (p2) p2.changeDirection(dirs[key]);
            }
        } else {
            // Unified Controls for P1
            if (dirs[key] || dirs[key.toLowerCase()]) {
                p1.changeDirection(dirs[key] || dirs[key.toLowerCase()]);
            }
        }
    }

    updateStats() {
        const p1 = this.snakes[0];
        if (p1) {
            this.scoreEl.innerText = p1.score;
            this.lengthEl.innerText = p1.length;
            this.highScoreEl.innerText = this.highScore;
        }
    }

    gameOver(score, msg = "游戏结束") {
        window.audioManager.stop('bgm');
        if (msg.includes("胜利")) {
             window.audioManager.play('win');
        } else {
             window.audioManager.play('fail');
        }

        this.isRunning = false;
        
        // Check Leaderboard logic first (Only for Single Player)
        if (this.mode === 'single' && this.isHighScore(score)) {
            this.showHighscoreInput(score, msg);
        } else {
            this.showGameOverScreen(score, msg);
        }
    }

    showGameOverScreen(score, msg) {
        this.overlayTitle.innerText = msg;
        this.overlayMsg.innerText = `最终得分: ${score}`;
        this.overlay.classList.remove('hidden');

        // Restore Game Over Buttons
        const oldBtns = this.overlay.querySelectorAll('button');
        oldBtns.forEach(btn => btn.remove());
        const oldInputs = this.overlay.querySelectorAll('input');
        oldInputs.forEach(input => input.remove());
        
        const container = this.overlay.querySelector('.overlay-content');

        const restartBtn = document.createElement('button');
        restartBtn.className = 'btn btn-primary';
        restartBtn.innerText = '再玩一次';
        restartBtn.onclick = () => window.restartGame();
        container.appendChild(restartBtn);

        const exitBtn = document.createElement('button');
        exitBtn.className = 'btn btn-secondary';
        exitBtn.innerText = '返回菜单';
        exitBtn.onclick = () => window.exitGame();
        container.appendChild(exitBtn);
    }

    isHighScore(score) {
        if (score === 0) return false;
        
        let leaderboard = [];
        try {
            leaderboard = JSON.parse(localStorage.getItem('snakeLeaderboard') || '[]');
        } catch (e) {
            console.warn('Storage not available', e);
            return false;
        }

        if (leaderboard.length < 10) return true;
        
        // Check if score is higher than the last one
        return score > leaderboard[leaderboard.length - 1].score;
    }

    showHighscoreInput(score, msg) {
        this.overlayTitle.innerText = "恭喜上榜！";
        this.overlayMsg.innerText = `最终得分: ${score}`;
        this.overlay.classList.remove('hidden');

        // Clear content logic
        const content = this.overlay.querySelector('.overlay-content');
        // Clean up buttons/inputs but keep title/msg
        const oldBtns = this.overlay.querySelectorAll('button');
        oldBtns.forEach(btn => btn.remove());
        const oldInputs = this.overlay.querySelectorAll('input');
        oldInputs.forEach(input => input.remove());

        // Create Input Form
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'name-input';
        input.placeholder = '请输入你的名字';
        input.maxLength = 10;
        input.value = '玩家';
        // Auto focus
        setTimeout(() => input.focus(), 100);

        const submitBtn = document.createElement('button');
        submitBtn.className = 'btn btn-primary';
        submitBtn.innerText = '提交成绩';
        submitBtn.onclick = () => {
            const name = input.value.trim() || '玩家';
            this.saveToLeaderboard(name, score);
            this.showGameOverScreen(score, msg);
        };

        content.appendChild(input);
        content.appendChild(submitBtn);
    }

    saveToLeaderboard(name, score) {
        let leaderboard = [];
        try {
            leaderboard = JSON.parse(localStorage.getItem('snakeLeaderboard') || '[]');
        } catch (e) {
            console.warn('Storage not available', e);
            // Fallback to empty array
        }
        
        const date = new Date().toLocaleDateString();
        
        leaderboard.push({
            name: name,
            score: score,
            date: date
        });

        // Sort descending
        leaderboard.sort((a, b) => b.score - a.score);
        
        // Keep top 10
        leaderboard = leaderboard.slice(0, 10);
        
        try {
            localStorage.setItem('snakeLeaderboard', JSON.stringify(leaderboard));
        } catch (e) {
            console.warn('Storage not available', e);
        }
    }

    togglePause() {
        if (!this.isRunning) return;
        this.isPaused = !this.isPaused;
        const btn = document.getElementById('btn-pause');
        btn.innerText = this.isPaused ? '继续游戏' : '暂停游戏';
    }
}
